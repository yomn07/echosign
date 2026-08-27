import torch
import torch.nn as nn
import torch.nn.functional as F


class ChannelDropout(nn.Module):
    """
    Matches TF's Dropout(rate, noise_shape=(None,1,1)): drops entire channels
    (same mask for all timesteps of a given channel, per sample), rather than
    independent per-element dropout.
    x: (B, T, C) -- mask is (B, 1, C), broadcast over T.
    """

    def __init__(self, drop_rate):
        super().__init__()
        self.drop_rate = drop_rate

    def forward(self, x):
        if self.drop_rate == 0.0 or not self.training:
            return x
        B, T, C = x.shape
        keep_prob = 1 - self.drop_rate
        mask = torch.bernoulli(torch.full((B, 1, C), keep_prob, device=x.device, dtype=x.dtype))
        return x * mask / keep_prob


class DropPath(nn.Module):
    def __init__(self, drop_prob=0.0):
        super().__init__()
        self.drop_prob = drop_prob

    def forward(self, x):
        if self.drop_prob == 0.0 or not self.training:
            return x
        keep_prob = 1 - self.drop_prob
        shape = (x.shape[0],) + (1,) * (x.ndim - 1)
        random_tensor = keep_prob + torch.rand(shape, dtype=x.dtype, device=x.device)
        random_tensor.floor_()
        return x / keep_prob * random_tensor


class ECA(nn.Module):
    """
    Efficient Channel Attention: masked-mean-pool over time -> small 1D conv
    over the CHANNEL axis (not time) -> sigmoid -> rescale channels.
    x: (B, T, C), mask: (B, T, 1) float (1.0 = real frame)
    """

    def __init__(self, kernel_size=5):
        super().__init__()
        self.conv = nn.Conv1d(1, 1, kernel_size=kernel_size, padding=kernel_size // 2, bias=False)

    def forward(self, x, mask):
        pooled = (x * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-6)  # (B, C) masked mean over time
        pooled = pooled.unsqueeze(1)         # (B, 1, C) -- treat channels as the "sequence" for the conv
        gate = self.conv(pooled)             # (B, 1, C)
        gate = torch.sigmoid(gate)           # (B, 1, C) -- broadcasts directly against x (B, T, C)
        return x * gate


class CausalDWConv1d(nn.Module):
    """Depthwise causal 1D conv: left-pad only, so output[t] never sees input[>t]."""

    def __init__(self, channels, kernel_size=17):
        super().__init__()
        self.causal_pad = kernel_size - 1
        self.dw_conv = nn.Conv1d(channels, channels, kernel_size=kernel_size, groups=channels, bias=False)

    def forward(self, x):
        # x: (B, C, T)
        x = F.pad(x, (self.causal_pad, 0))
        return self.dw_conv(x)


class Conv1DBlock(nn.Module):
    """
    True inverted-bottleneck block matching the real implementation:
    expand (dim -> dim*expand_ratio, Swish) -> causal depthwise conv -> BN
    -> ECA -> project (dim*expand_ratio -> dim) -> channel dropout -> residual.
    """

    def __init__(self, dim, kernel_size=17, expand_ratio=2, drop_rate=0.2):
        super().__init__()
        expanded = dim * expand_ratio

        self.expand = nn.Linear(dim, expanded, bias=True)
        self.dwconv = CausalDWConv1d(expanded, kernel_size)
        self.bn = nn.BatchNorm1d(expanded, momentum=0.05)
        self.eca = ECA(kernel_size=5)
        self.project = nn.Linear(expanded, dim, bias=True)
        self.channel_dropout = ChannelDropout(drop_rate)

    def forward(self, x, mask_time_last, mask_channel_last):
        """
        x: (B, T, C)
        mask_time_last: (B, T, 1) float -- for ECA's masked pooling
        mask_channel_last: (B, 1, T) float -- for zeroing before causal conv (approximation
                            for true mask propagation, see module docstring)
        """
        residual = x

        h = F.silu(self.expand(x))                    # (B, T, expanded)
        h = h.transpose(1, 2)                          # (B, expanded, T) for conv
        h = h * mask_channel_last                       # zero padding before causal conv
        h = self.dwconv(h)
        h = self.bn(h)
        h = h.transpose(1, 2)                          # back to (B, T, expanded)

        h = self.eca(h, mask_time_last)
        h = self.project(h)                             # (B, T, dim)
        h = self.channel_dropout(h)

        return residual + h


class MultiHeadSelfAttention(nn.Module):
    def __init__(self, dim, num_heads=4, dropout=0.2):
        super().__init__()
        self.attn = nn.MultiheadAttention(dim, num_heads, dropout=dropout, batch_first=True)

    def forward(self, x, key_padding_mask):
        out, _ = self.attn(x, x, x, key_padding_mask=key_padding_mask, need_weights=False)
        return out


class TransformerBlock(nn.Module):
    """
    Pre-norm (BatchNorm, not LayerNorm) residual block: BN -> MHSA -> channel
    dropout -> add -> BN -> FFN(Swish) -> channel dropout -> add.
    num_heads defaults to 4, matching the real TransformerBlock(dim, expand=2)
    calls (no num_heads override in the source).
    """

    def __init__(self, dim, num_heads=4, expand=2, attn_dropout=0.2, drop_rate=0.2):
        super().__init__()
        self.bn1 = nn.BatchNorm1d(dim, momentum=0.05)
        self.attn = MultiHeadSelfAttention(dim, num_heads, attn_dropout)
        self.drop1 = ChannelDropout(drop_rate)

        self.bn2 = nn.BatchNorm1d(dim, momentum=0.05)
        self.ffn = nn.Sequential(
            nn.Linear(dim, dim * expand, bias=False),
            nn.SiLU(),
            nn.Linear(dim * expand, dim, bias=False),
        )
        self.drop2 = ChannelDropout(drop_rate)

    def forward(self, x, key_padding_mask):
        residual = x
        h = self.bn1(x.transpose(1, 2)).transpose(1, 2)
        h = self.attn(h, key_padding_mask)
        h = self.drop1(h)
        x = residual + h

        residual = x
        h = self.bn2(x.transpose(1, 2)).transpose(1, 2)
        h = self.ffn(h)
        h = self.drop2(h)
        x = residual + h

        return x


class LateDropout(nn.Module):
    def __init__(self, drop_rate, start_step=0):
        super().__init__()
        self.drop_rate = drop_rate
        self.start_step = start_step
        self.register_buffer("step", torch.tensor(0))

    def forward(self, x):
        if self.training:
            self.step += 1
        if not self.training or self.step < self.start_step:
            return x
        return F.dropout(x, p=self.drop_rate, training=True)


class ConvTransformerClassifier(nn.Module):
    """Drop-in replacement for modelv3.BiGRUTransformerClassifier: model(x, lengths) -> logits."""

    def __init__(
        self,
        input_dim=225,
        dim=192,
        kernel_size=17,
        num_classes=665,
        conv_drop_rate=0.2,
        expand_ratio=2,
        num_heads=4,
        transformer_expand=2,
        attn_dropout=0.2,
        late_dropout_rate=0.8,
        late_dropout_start_step=0,
    ):
        super().__init__()

        self.stem = nn.Linear(input_dim, dim, bias=False)
        self.stem_bn = nn.BatchNorm1d(dim, momentum=0.05)

        self.conv_stage1 = nn.ModuleList([
            Conv1DBlock(dim, kernel_size, expand_ratio, conv_drop_rate) for _ in range(3)
        ])
        self.transformer_stage1 = TransformerBlock(dim, num_heads, transformer_expand, attn_dropout, conv_drop_rate)

        self.conv_stage2 = nn.ModuleList([
            Conv1DBlock(dim, kernel_size, expand_ratio, conv_drop_rate) for _ in range(3)
        ])
        self.transformer_stage2 = TransformerBlock(dim, num_heads, transformer_expand, attn_dropout, conv_drop_rate)

        self.top_conv = nn.Linear(dim, dim * 2)
        self.late_dropout = LateDropout(late_dropout_rate, late_dropout_start_step)
        self.classifier = nn.Linear(dim * 2, num_classes)

    def create_masks(self, lengths, max_len, device):
        arange = torch.arange(max_len, device=device).unsqueeze(0)
        real = arange < lengths.unsqueeze(1)                 # (B, T) True = real frame
        mask_time_last = real.float().unsqueeze(-1)          # (B, T, 1) -- for masked pooling / ECA
        mask_channel_last = real.float().unsqueeze(1)         # (B, 1, T) -- for zeroing before conv
        key_padding_mask = ~real                              # (B, T) True = padding, for attention
        return mask_time_last, mask_channel_last, key_padding_mask

    def forward(self, x, lengths=None):
        B, T, _ = x.shape
        device = x.device
        if lengths is None:
            lengths = torch.full((B,), T, dtype=torch.long, device=device)

        mask_time_last, mask_channel_last, key_padding_mask = self.create_masks(lengths, T, device)

        h = self.stem(x)
        h = self.stem_bn(h.transpose(1, 2)).transpose(1, 2)
        h = F.silu(h)

        for block in self.conv_stage1:
            h = block(h, mask_time_last, mask_channel_last)
        h = self.transformer_stage1(h, key_padding_mask)

        for block in self.conv_stage2:
            h = block(h, mask_time_last, mask_channel_last)
        h = self.transformer_stage2(h, key_padding_mask)

        h = self.top_conv(h)

        mask_expanded = mask_time_last  # (B, T, 1)
        h = (h * mask_expanded).sum(dim=1) / mask_expanded.sum(dim=1).clamp(min=1e-6)

        h = self.late_dropout(h)
        logits = self.classifier(h)
        return logits

    def count_parameters(self):
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


if __name__ == "__main__":
    model = ConvTransformerClassifier(input_dim=225, dim=192, num_classes=665)
    print(f"Trainable parameters: {model.count_parameters():,}")

    batch, seq_len = 8, 90
    x = torch.randn(batch, seq_len, 225)
    lengths = torch.tensor([90, 80, 75, 60, 55, 45, 30, 20])

    logits = model(x, lengths)
    print("Output shape:", logits.shape)