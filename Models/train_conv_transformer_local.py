import torch
from collections import Counter

from dataset_loader import MSASLLandmarkDataset
from conv_transformer_model_v2 import ConvTransformerClassifier
from trainer2 import Trainer  

import numpy as np

# ==========================================================
# Config -- mirrors your original train.py
# ==========================================================
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
NUM_CLASSES = 665
WINDOW_SIZE = 90
CHECKPOINT_DIR = "checkpoints_conv_transformer"

TRAIN_JSONL = r"..\Data\Processed\remapped_train_baseline.jsonl"
VAL_JSONL = r"..\Data\Processed\remapped_val_baseline.jsonl"
TEST_JSONL = r"..\Data\Processed\remapped_test_baseline.jsonl"


def interpolate_missing_landmarks(x):
    x = x.copy()
    T, D = x.shape
    coords = x.reshape(T, 75, 3)
    for j in range(75):
        landmark = coords[:, j, :]
        valid = np.any(landmark != 0, axis=1)
        idx = np.where(valid)[0]
        if len(idx) < 2:
            continue
        for c in range(3):
            coords[:, j, c] = np.interp(np.arange(T), idx, landmark[idx, c])
    return coords.reshape(T, D)


def get_augmentation_factor(n):
    if n < 5:
        return 4
    if n < 10:
        return 3
    if n < 20:
        return 2
    return 1


class InterpolatedASLDataset(torch.utils.data.Dataset):
    """Identical to your original -- copied here so this script is self-contained."""

    def __init__(self, dataset, label_counts, augment=False):
        self.dataset = dataset
        self.augment = augment
        self.index_map = []
        for i in range(len(dataset)):
            label = dataset.meta[i]["label"]
            factor = get_augmentation_factor(label_counts[label]) if augment else 1
            for j in range(factor):
                self.index_map.append((i, j > 0))

    def __len__(self):
        return len(self.index_map)

    def __getitem__(self, index):
        real_idx, aug = self.index_map[index]
        x, y, text = self.dataset[real_idx]
        x = np.asarray(x)
        x = x[:, :225]
        x = interpolate_missing_landmarks(x)

        for t in range(len(x)):
            left = x[t, 159:162]
            right = x[t, 162:165]
            center = (left + right) / 2
            width = np.linalg.norm(left - right)
            width = max(width, 0.1)
            x[t, :126] -= np.tile(center, 42)
            x[t, 126:225] -= np.tile(center, 33)
            x[t] /= width

        if aug:
            x *= np.random.uniform(0.95, 1.05)
            x += np.random.normal(0, 0.005, x.shape)
            keep = np.random.random(len(x)) > np.random.uniform(0.02, 0.08)
            if keep.sum() > 15:
                x = x[keep]
            factor = np.random.uniform(0.85, 1.15)
            new_len = max(15, int(len(x) * factor))
            idx = np.linspace(0, len(x) - 1, new_len).astype(int)
            x = x[idx]

        return torch.tensor(x, dtype=torch.float32), int(y), len(x)


def main():
    raw_train_ds = MSASLLandmarkDataset(TRAIN_JSONL, window_size=WINDOW_SIZE)
    raw_val_ds = MSASLLandmarkDataset(VAL_JSONL, window_size=WINDOW_SIZE)

    labels = [raw_train_ds[i][1] for i in range(len(raw_train_ds))]
    label_counts = Counter(labels)

    train_ds = InterpolatedASLDataset(raw_train_ds, label_counts, augment=True)
    val_ds = InterpolatedASLDataset(raw_val_ds, label_counts, augment=False)

    print(f"Train: {len(train_ds)}  Val: {len(val_ds)}")

    weights = torch.zeros(NUM_CLASSES)
    N = len(labels)
    C = len(label_counts)
    for cls, count in label_counts.items():
        weights[cls] = N / (C * count)
    weights = weights.to(DEVICE)

    model = ConvTransformerClassifier(
        input_dim=225,
        dim=192,               # matches the write-up's base single-model size
        kernel_size=17,
        num_classes=NUM_CLASSES,
        conv_drop_rate=0.2,
        drop_path_rate=0.2,
        late_dropout_rate=0.8,
        late_dropout_start_step=15 * (len(train_ds) // 32),  # ~epoch 15, matching the write-up
    )
    print("Parameters:", model.count_parameters())

    trainer = Trainer(
        model=model,
        train_dataset=train_ds,
        val_dataset=val_ds,
        checkpoint_dir=CHECKPOINT_DIR,
        batch_size=32,
        learning_rate=5e-4,   # closer to the write-up's LR for this architecture than your GRU model's 1e-4
        epochs=120,
        device=DEVICE,
        class_weights=weights,
    )

    history = trainer.fit(epochs=120, start_epoch=0)


if __name__ == "__main__":
    main()