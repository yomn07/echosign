import json
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import Dataset


class MSASLLandmarkDataset(Dataset):
    """
    Each item returns:
        features: FloatTensor of shape (window_size, feature_dim)
        label:    integer class index
        text:     the gloss string (for debugging/inspection)
    """

    def __init__(self, output_dir, window_size=45, split_signers_for_test=None):
        """
        output_dir: the same output_dir passed to run_pipeline()
        window_size: fixed number of frames per sample (pad/truncate).
                     45 frames matches the production sliding window
                     described in Stage 5 of the pipeline (~0.75s at 60fps,
                     or ~1.5s at the more typical 30fps of downloaded clips).
        split_signers_for_test: optional list of signer_ids to hold out,
                     enabling a signer-independent train/test split
                     (the evaluation mode P1 showed to be the meaningful one).
        """
        self.output_dir = Path(output_dir)
        self.landmarks_dir = Path(output_dir).parent / "landmarks"
        self.window_size = window_size

        if self.output_dir.suffix == ".jsonl":
            metadata_file = self.output_dir
        else:
            metadata_file = self.output_dir / "metadata.jsonl"

        with open(metadata_file, "r") as f:
            all_meta = [json.loads(line) for line in f]
        if split_signers_for_test is not None:
            self.meta = [
                m for m in all_meta
                if m.get("signer_id", -1) not in split_signers_for_test
            ]
        else:
            self.meta = all_meta

        # Build label set for sanity checking / num_classes
        self.labels = sorted(set(m["label"] for m in self.meta))
        self.num_classes = max(self.labels) + 1 if self.labels else 0

    def __len__(self):
        return len(self.meta)

    def _fit_to_window(self, arr):
        """Pad with zeros or truncate (center crop) to self.window_size frames."""
        T = arr.shape[0]
        if T == self.window_size:
            return arr
        if T > self.window_size:
            # Center crop — keeps the most likely "peak" of the gesture
            start = (T - self.window_size) // 2
            return arr[start:start + self.window_size]
        # Pad at the end with zeros (neutral pose)
        pad_len = self.window_size - T
        pad = np.zeros((pad_len, arr.shape[1]), dtype=arr.dtype)
        return np.concatenate([arr, pad], axis=0)

    def __getitem__(self, idx):
        meta = self.meta[idx]
        landmark_path = self.landmarks_dir / meta["landmark_file"]
        arr = np.load(landmark_path)  # (T, feature_dim)
        arr = arr[:, :225]
        arr = self._fit_to_window(arr)

        features = torch.from_numpy(arr).float()
        label = torch.tensor(meta["label"], dtype=torch.long)

        return features, label, meta["text"]


def make_signer_independent_split(output_dir, test_signer_fraction=0.2, seed=42):
    """
    Reads metadata.jsonl, identifies all distinct signer_ids, and randomly
    holds out a fraction of them entirely for testing — so the test set
    contains zero signers seen during training. This mirrors the
    signer-independent evaluation protocol from P1, which is the only
    evaluation mode that reflects real-world performance.

    Returns: (train_signer_ids_excluded_set, test_signer_ids_set)
    """
    import random

    output_dir = Path(output_dir)
    metadata_file = output_dir / "metadata.jsonl"
    with open(metadata_file, "r") as f:
        all_meta = [json.loads(line) for line in f]

    signer_ids = sorted(set(m.get("signer_id", -1) for m in all_meta))
    signer_ids = [s for s in signer_ids if s != -1]  # drop unknowns

    random.seed(seed)
    n_test = max(1, int(len(signer_ids) * test_signer_fraction))
    test_signers = set(random.sample(signer_ids, n_test))
    train_signers_excluded = test_signers  # exclude these from train set

    print(f"Total signers: {len(signer_ids)}")
    print(f"Held out for testing: {len(test_signers)} signers -> {sorted(test_signers)}")
    print(f"Remaining for training: {len(signer_ids) - len(test_signers)} signers")

    return train_signers_excluded, test_signers


if __name__ == "__main__":
    # Example usage
    OUTPUT_DIR = "./msasl100_landmarks_smoketest"

    train_excl, test_signers = make_signer_independent_split(OUTPUT_DIR)

    train_dataset = MSASLLandmarkDataset(
        OUTPUT_DIR, window_size=45, split_signers_for_test=train_excl
    )
    test_dataset = MSASLLandmarkDataset(
        OUTPUT_DIR, window_size=45,
        split_signers_for_test=[s for s in range(1000) if s not in test_signers]
    )

    print(f"Train samples: {len(train_dataset)}")
    print(f"Test samples: {len(test_dataset)}")
    print(f"Num classes: {train_dataset.num_classes}")

    if len(train_dataset) > 0:
        feats, label, text = train_dataset[0]
        print(f"Sample feature shape: {feats.shape}, label: {label.item()}, text: '{text}'")
