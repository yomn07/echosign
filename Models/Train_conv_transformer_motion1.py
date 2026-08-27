import torch
from collections import Counter

from dataset_loader import MSASLLandmarkDataset
from conv_transformer_model_v3 import ConvTransformerClassifier
from trainer2 import Trainer
from Dataset_with_motion import InterpolatedASLDatasetWithMotion, get_augmentation_factor

import numpy as np

# ==========================================================
# Config
# ==========================================================
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
NUM_CLASSES = 665
WINDOW_SIZE = 90
INPUT_DIM = 675  # 225 position + 225 velocity + 225 acceleration
CHECKPOINT_DIR = "checkpoints_conv_transformer_v2_motion"

TRAIN_JSONL = r"..\Data\Processed\remapped_train_baseline.jsonl"
VAL_JSONL = r"..\Data\Processed\remapped_val_baseline.jsonl"
TEST_JSONL = r"..\Data\Processed\remapped_test_baseline.jsonl"


def main():
    raw_train_ds = MSASLLandmarkDataset(TRAIN_JSONL, window_size=WINDOW_SIZE)
    raw_val_ds = MSASLLandmarkDataset(VAL_JSONL, window_size=WINDOW_SIZE)

    labels = [raw_train_ds[i][1] for i in range(len(raw_train_ds))]
    label_counts = Counter(labels)

    train_ds = InterpolatedASLDatasetWithMotion(raw_train_ds, label_counts, augment=True)
    val_ds = InterpolatedASLDatasetWithMotion(raw_val_ds, label_counts, augment=False)

    print(f"Train: {len(train_ds)}  Val: {len(val_ds)}")

    # sanity check: confirm the motion channels actually produced 675-dim features
    sample_x, _, _ = train_ds[0]
    print(f"Feature dim per frame: {sample_x.shape[-1]} (expected {INPUT_DIM})")
    assert sample_x.shape[-1] == INPUT_DIM, (
        f"Got {sample_x.shape[-1]}-dim features, expected {INPUT_DIM} -- "
        "check dataset_with_motion.py's add_motion_channels() output."
    )

    weights = torch.zeros(NUM_CLASSES)
    N = len(labels)
    C = len(label_counts)
    for cls, count in label_counts.items():
        weights[cls] = N / (C * count)
    weights = weights.to(DEVICE)

    model = ConvTransformerClassifier(
        input_dim=INPUT_DIM,
        dim=192,
        kernel_size=17,
        num_classes=NUM_CLASSES,
        conv_drop_rate=0.2,
        expand_ratio=2,
        num_heads=4,
        transformer_expand=2,
        attn_dropout=0.2,
        late_dropout_rate=0.8,
        late_dropout_start_step=15 * (len(train_ds) // 32),
    )
    print("Parameters:", model.count_parameters())


    trainer = Trainer(
        model=model,
        train_dataset=train_ds,
        val_dataset=val_ds,
        checkpoint_dir=CHECKPOINT_DIR,
        batch_size=32,
        learning_rate=5e-4,
        epochs=120,
        device=DEVICE,
        class_weights=weights,
    )

    history = trainer.fit(epochs=120, start_epoch=0)


if __name__ == "__main__":
    main()