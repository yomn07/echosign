import torch
import torch.nn as nn
import torch.nn.functional as F


class DropPath(nn.Module):
    """Stochastic depth: randomly drops the residual branch per-sample during training."""

    def __init__(self, drop_prob=0.0):
        super().__init__()
        self.drop_prob = drop_prob

    def forward(self, x):
        if self.drop_prob == 0.0 or not self.training:
            return x
        keep_prob = 1 - self.drop_prob
        shape = (x.shape[0],) + (1,) * (x.ndim - 1)  # per-sample, broadcast over the rest
        random_tensor = keep_prob + torch.rand(shape, dtype=x.dtype, device=x.device)
        random_tensor.floor_()  # binarize: 0 or 1
        return x / keep_prob * random_tensor


class CausalConv1dBlock(nn.Module):
    """
    Depthwise causal 1D conv block: Conv -> BatchNorm -> Swish -> Dropout,
    with a residual connection (+ DropPath), matching the write-up's
    Conv1DBlock. Causal padding (pad only on the left) keeps the mask index
    aligned -- output position t only ever depends on input positions <= t.
    """

    def __init__(self, dim, kernel_size=17, drop_rate=0.2, drop_path_rate=0.0):
        super().__init__()
        self.kernel_size = kernel_size
        self.causal_pad = kernel_size - 1

        self.depthwise_conv = nn.Conv1d(
            dim, dim, kernel_size=kernel_size, groups=dim, padding=0, bias=False
        )
        self.pointwise_conv = nn.Conv1d(dim, dim, kernel_size=1, bias=False)
        self.bn = nn.BatchNorm1d(dim, momentum=0.05)  # note: PyTorch momentum is (1 - TF momentum)
        self.dropout = nn.Dropout(drop_rate)
        self.drop_path = DropPath(drop_path_rate)

    def forward(self, x, mask):
        """
        x: (B, C, T)
        mask: (B, 1, T) float, 1.0 = real frame, 0.0 = padding
        """
        residual = x

        x = x * mask  # zero padded positions before conv so they don't leak into causal receptive field
        x = F.pad(x, (self.causal_pad, 0))  # left-pad only (causal)
        x = self.depthwise_conv(x)
        x = self.pointwise_conv(x)
        x = self.bn(x)
        x = F.silu(x)  # Swish
        x = self.dropout(x)
        x = x * mask

        return residual + self.drop_path(x)


class TransformerBlockBNSwish(nn.Module):
    """
    Self-attention + FFN block, using BatchNorm + Swish instead of the usual
    LayerNorm + GELU (per the write-up: "slightly lighter inference with the
    same accuracy"). Pre-norm residual structure.
    """

    def __init__(self, dim, n_heads=8, expand=2, drop_rate=0.2, drop_path_rate=0.0):
        super().__init__()
        self.bn1 = nn.BatchNorm1d(dim, momentum=0.05)
        self.attn = nn.MultiheadAttention(dim, n_heads, dropout=drop_rate, batch_first=True)
        self.drop_path1 = DropPath(drop_path_rate)

        self.bn2 = nn.BatchNorm1d(dim, momentum=0.05)
        self.ffn = nn.Sequential(
            nn.Linear(dim, dim * expand),
            nn.SiLU(),
            nn.Dropout(drop_rate),
            nn.Linear(dim * expand, dim),
            nn.Dropout(drop_rate),
        )
        self.drop_path2 = DropPath(drop_path_rate)

    def forward(self, x, key_padding_mask):
        """
        x: (B, T, C)
        key_padding_mask: (B, T) bool, True = padding position (masked out of attention)
        """
        residual = x
        x_bn = self.bn1(x.transpose(1, 2)).transpose(1, 2)
        attn_out, _ = self.attn(x_bn, x_bn, x_bn, key_padding_mask=key_padding_mask, need_weights=False)
        x = residual + self.drop_path1(attn_out)

        residual = x
        x_bn = self.bn2(x.transpose(1, 2)).transpose(1, 2)
        ffn_out = self.ffn(x_bn)
        x = residual + self.drop_path2(ffn_out)

        return x


class LateDropout(nn.Module):
    """Dropout that only activates after `start_step` training steps have passed."""

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
    """
    Drop-in replacement for modelv3.BiGRUTransformerClassifier.
    Same usage: model(x, lengths) -> logits, shape (batch, num_classes).
    """

    def __init__(
        self,
        input_dim=225,
        dim=192,
        kernel_size=17,
        num_classes=665,
        conv_drop_rate=0.2,
        drop_path_rate=0.2,
        late_dropout_rate=0.8,
        late_dropout_start_step=0,
        n_heads=8,
        transformer_expand=2,
    ):
        super().__init__()

        self.stem = nn.Sequential(
            nn.Linear(input_dim, dim, bias=False),
        )
        self.stem_bn = nn.BatchNorm1d(dim, momentum=0.05)

        self.conv_stage1 = nn.ModuleList([
            CausalConv1dBlock(dim, kernel_size, conv_drop_rate, drop_path_rate) for _ in range(3)
        ])
        self.transformer_stage1 = TransformerBlockBNSwish(dim, n_heads, transformer_expand, conv_drop_rate, drop_path_rate)

        self.conv_stage2 = nn.ModuleList([
            CausalConv1dBlock(dim, kernel_size, conv_drop_rate, drop_path_rate) for _ in range(3)
        ])
        self.transformer_stage2 = TransformerBlockBNSwish(dim, n_heads, transformer_expand, conv_drop_rate, drop_path_rate)

        self.top_conv = nn.Linear(dim, dim * 2)
        self.late_dropout = LateDropout(late_dropout_rate, late_dropout_start_step)
        self.classifier = nn.Linear(dim * 2, num_classes)

    def create_masks(self, lengths, max_len, device):
        """
        Returns:
          conv_mask: (B, 1, T) float -- 1.0 for real frames, 0.0 for padding (used in conv blocks)
          key_padding_mask: (B, T) bool -- True for padding (used in attention)
        """
        arange = torch.arange(max_len, device=device).unsqueeze(0)  # (1, T)
        real = arange < lengths.unsqueeze(1)  # (B, T), True = real frame
        conv_mask = real.float().unsqueeze(1)  # (B, 1, T)
        key_padding_mask = ~real  # (B, T), True = padding
        return conv_mask, key_padding_mask

    def forward(self, x, lengths=None):
        """
        x: (batch, time, input_dim)
        lengths: (batch,)
        """
        B, T, _ = x.shape
        device = x.device

        if lengths is None:
            lengths = torch.full((B,), T, dtype=torch.long, device=device)

        conv_mask, key_padding_mask = self.create_masks(lengths, T, device)

        h = self.stem(x)                              # (B, T, dim)
        h = self.stem_bn(h.transpose(1, 2)).transpose(1, 2)
        h = F.silu(h)

        h = h.transpose(1, 2)                          # (B, dim, T) for conv blocks
        for block in self.conv_stage1:
            h = block(h, conv_mask)
        h = h.transpose(1, 2)                          # back to (B, T, dim) for attention
        h = self.transformer_stage1(h, key_padding_mask)

        h = h.transpose(1, 2)
        for block in self.conv_stage2:
            h = block(h, conv_mask)
        h = h.transpose(1, 2)
        h = self.transformer_stage2(h, key_padding_mask)

        h = self.top_conv(h)                            # (B, T, dim*2)

        # masked global average pooling -- only average over real (non-padded) frames
        mask_expanded = (~key_padding_mask).float().unsqueeze(-1)  # (B, T, 1)
        h = (h * mask_expanded).sum(dim=1) / mask_expanded.sum(dim=1).clamp(min=1e-6)  # (B, dim*2)

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