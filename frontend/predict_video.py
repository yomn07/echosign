"""
Run inference on a single video file: extract landmarks -> preprocess
(identical to training) -> ensemble prediction across v1/v2/v2_motion ->
print top-5 predicted signs with real gloss names (not just class indices).

Usage:
    python predict_video.py path/to/your_video.mp4
"""

import sys
import numpy as np
import torch

from extract_single_video import extract_video_landmarks
from Dataset_with_motion import interpolate_missing_landmarks, add_motion_channels

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
NUM_CLASSES = 665
WINDOW_SIZE = 90
TRAIN_JSONL = r"C:\Users\toumi\OneDrive\Desktop\EchoSign Preprocessing\DatasetMS-ASL\remapped_train_baseline.jsonl"  # used only to build the index -> gloss lookup

CHECKPOINTS = {
    "v1": (r"C:\Users\toumi\OneDrive\Desktop\EchoSign Preprocessing\checkpoints_conv_transformer\best.pt", 225),
    "v2": (r"C:\Users\toumi\OneDrive\Desktop\EchoSign Preprocessing\checkpoints_conv_transformer_v2\best.pt", 225),
    "v2_motion": (r"C:\Users\toumi\OneDrive\Desktop\EchoSign Preprocessing\checkpoints_conv_transformer_v2_motion\best.pt", 675),
}
ENSEMBLE_WEIGHTS = {"v1": 1 / 3, "v2": 1 / 3, "v2_motion": 1 / 3}  # adjust to your tuned weights if you found better ones

TOP_K = 5


def preprocess(x):
    """Identical to InterpolatedASLDataset's non-augmented path: interpolate + shoulder-normalize."""
    x = np.asarray(x)[:, :225]
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

    return x  # (T, 225)


import os
import json

IDX2GLOSS_CACHE = "idx2gloss_cache.json"


def build_idx2gloss(cache_path=IDX2GLOSS_CACHE):
    """
    Loads the pre-built gloss lookup file. Run build_gloss_cache.py once
    beforehand to create it -- this function no longer scans the training
    set itself, it just reads the input file.
    """
    if not os.path.exists(cache_path):
        raise FileNotFoundError(
            f"{cache_path} not found. Run `python build_gloss_cache.py` once "
            "first to generate it."
        )
    with open(cache_path, "r", encoding="utf-8") as f:
        cached = json.load(f)
    return {int(k): v for k, v in cached.items()}  # JSON keys are always strings, convert back to int


def load_model(name, input_dim, checkpoint_path):
    if name == "v1":
        from conv_transformer_model import ConvTransformerClassifier
    else:
        from conv_transformer_model_v2 import ConvTransformerClassifier

    model = ConvTransformerClassifier(input_dim=input_dim, dim=192, num_classes=NUM_CLASSES)
    checkpoint = torch.load(checkpoint_path, map_location=DEVICE)
    state_dict = checkpoint["model"] if "model" in checkpoint else checkpoint
    model.load_state_dict(state_dict)
    model.to(DEVICE)
    model.eval()
    return model


def load_all_models():
    """Load all checkpoints once. Returns dict of name -> loaded model."""
    models = {}
    for name, (ckpt_path, input_dim) in CHECKPOINTS.items():
        print(f"Loading {name}...")
        models[name] = load_model(name, input_dim, ckpt_path)
    return models


@torch.no_grad()
def predict_from_landmarks(raw_landmarks, models, idx2gloss, top_k=TOP_K):
    """
    raw_landmarks: (T, 225) raw extracted landmarks (not yet preprocessed).
    models: dict from load_all_models().
    Returns list of (gloss, confidence) tuples, sorted best first.
    """
    x_position = preprocess(raw_landmarks)
    x_motion = add_motion_channels(x_position)

    length = torch.tensor([x_position.shape[0]], dtype=torch.long, device=DEVICE)
    x_pos_t = torch.tensor(x_position, dtype=torch.float32, device=DEVICE).unsqueeze(0)
    x_mot_t = torch.tensor(x_motion, dtype=torch.float32, device=DEVICE).unsqueeze(0)

    ensemble_probs = torch.zeros(1, NUM_CLASSES, device=DEVICE)
    for name, model in models.items():
        input_dim = CHECKPOINTS[name][1]
        x_input = x_mot_t if input_dim == 675 else x_pos_t
        logits = model(x_input, length)
        probs = torch.softmax(logits, dim=1)
        ensemble_probs += ENSEMBLE_WEIGHTS[name] * probs

    top_probs, top_idx = torch.topk(ensemble_probs[0], k=top_k)
    return [(idx2gloss.get(idx, f"<unknown class {idx}>"), prob)
            for prob, idx in zip(top_probs.tolist(), top_idx.tolist())]


@torch.no_grad()
def predict(video_path):
    print(f"Extracting landmarks from {video_path} ...")
    raw_landmarks = extract_video_landmarks(video_path)
    print(f"  {raw_landmarks.shape[0]} frames extracted")

    print("Building label lookup from training data...")
    idx2gloss = build_idx2gloss()
    models = load_all_models()

    results = predict_from_landmarks(raw_landmarks, models, idx2gloss)

    print(f"\n==================== TOP-{TOP_K} PREDICTIONS ====================")
    for rank, (gloss, prob) in enumerate(results, 1):
        print(f"{rank}. {gloss:20s}  confidence={prob:.4f}")
    print("===================================================================")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python predict_video.py path/to/video.mp4")
        sys.exit(1)

    predict(sys.argv[1])