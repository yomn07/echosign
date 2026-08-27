import numpy as np
import torch


def interpolate_missing_landmarks(x):
    """Unchanged from your original -- still needed before computing derivatives,
    since differencing across a genuinely missing (zero) frame would inject
    a fake, huge "velocity" spike."""
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


def add_motion_channels(x):
    """
    x: (T, 225) -- already interpolated + normalized position data.
    Returns (T, 675): [position(225), velocity(225), acceleration(225)]
    concatenated along the feature axis.
    """
    dx = np.diff(x, axis=0, prepend=x[:1])       # velocity: frame-to-frame difference
    dx2 = np.diff(dx, axis=0, prepend=dx[:1])    # acceleration: difference of velocity

    return np.concatenate([x, dx, dx2], axis=-1)  # (T, 675)


def get_augmentation_factor(n):
    if n < 5:
        return 4
    if n < 10:
        return 3
    if n < 20:
        return 2
    return 1


class InterpolatedASLDatasetWithMotion(torch.utils.data.Dataset):
    """
    Same as your InterpolatedASLDataset, with motion channels added at the end
    of preprocessing (after interpolation + normalization, before augmentation
    -- augmentation noise/scaling is applied to position only, then motion
    channels are recomputed AFTER augmentation so they reflect the actual
    augmented trajectory, not the original one).
    """

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

        # motion channels computed AFTER augmentation, so velocity reflects
        # the actual (possibly time-warped) sequence the model will see
        x = add_motion_channels(x)  # (T, 675)

        return torch.tensor(x, dtype=torch.float32), int(y), len(x)