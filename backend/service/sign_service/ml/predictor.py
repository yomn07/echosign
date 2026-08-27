import json
import os

import numpy as np
import torch

from pathlib import Path

from Models.Dataset_with_motion import (
    interpolate_missing_landmarks,
    add_motion_channels,
)


DEVICE = (
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)


NUM_CLASSES = 665

WINDOW_SIZE = 90

TOP_K = 5


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)


CHECKPOINTS = {

    "v1": (
        PROJECT_ROOT
        / "Models"
        / "checkpoints_conv_transformer"
        / "best.pt",
        225,
    ),

    "v2": (
        PROJECT_ROOT
        / "Models"
        / "checkpoints_conv_transformer_v2"
        / "best.pt",
        225,
    ),

    "v2_motion": (
        PROJECT_ROOT
        / "Models"
        / "checkpoints_conv_transformer_v2_motion"
        / "best.pt",
        675,
    ),
}


ENSEMBLE_WEIGHTS = {
    "v1": 1 / 3,
    "v2": 1 / 3,
    "v2_motion": 1 / 3,
}


IDX2GLOSS_CACHE = (
    PROJECT_ROOT
    / "idx2gloss_cache.json"
)


def preprocess(x):

    x = np.asarray(x)[:, :225]

    x = interpolate_missing_landmarks(x)

    for t in range(len(x)):

        left = x[t, 159:162]

        right = x[t, 162:165]

        center = (
            left + right
        ) / 2

        width = np.linalg.norm(
            left - right
        )

        width = max(
            width,
            0.1,
        )

        x[t, :126] -= np.tile(
            center,
            42,
        )

        x[t, 126:225] -= np.tile(
            center,
            33,
        )

        x[t] /= width

    return x


def build_idx2gloss(
    cache_path=IDX2GLOSS_CACHE,
):

    if not os.path.exists(
        cache_path
    ):

        raise FileNotFoundError(
            f"{cache_path} not found."
        )

    with open(
        cache_path,
        "r",
        encoding="utf-8",
    ) as f:

        cached = json.load(f)

    return {
        int(k): v
        for k, v in cached.items()
    }


def load_model(
    name,
    input_dim,
    checkpoint_path,
):

    if name == "v1":

        from Models.conv_transformer_model import (
            ConvTransformerClassifier,
        )

    else:

        from Models.conv_transformer_model_v2 import (
            ConvTransformerClassifier,
        )

    model = ConvTransformerClassifier(
        input_dim=input_dim,
        dim=192,
        num_classes=NUM_CLASSES,
    )

    checkpoint = torch.load(
        checkpoint_path,
        map_location=DEVICE,
    )

    state_dict = (
        checkpoint["model"]
        if "model" in checkpoint
        else checkpoint
    )

    model.load_state_dict(
        state_dict
    )

    model.to(DEVICE)

    model.eval()

    return model


def load_all_models():

    models = {}

    for (
        name,
        (
            checkpoint_path,
            input_dim,
        ),
    ) in CHECKPOINTS.items():

        print(
            f"Loading {name}..."
        )

        models[name] = load_model(
            name,
            input_dim,
            checkpoint_path,
        )

    return models


@torch.no_grad()
def predict_from_landmarks(
    raw_landmarks,
    models,
    idx2gloss,
    top_k=TOP_K,
):

    x_position = preprocess(
        raw_landmarks
    )

    x_motion = add_motion_channels(
        x_position
    )

    length = torch.tensor(
        [
            x_position.shape[0]
        ],
        dtype=torch.long,
        device=DEVICE,
    )

    x_pos_t = torch.tensor(
        x_position,
        dtype=torch.float32,
        device=DEVICE,
    ).unsqueeze(0)

    x_mot_t = torch.tensor(
        x_motion,
        dtype=torch.float32,
        device=DEVICE,
    ).unsqueeze(0)

    ensemble_probs = torch.zeros(
        1,
        NUM_CLASSES,
        device=DEVICE,
    )

    for name, model in models.items():

        input_dim = CHECKPOINTS[
            name
        ][1]

        x_input = (
            x_mot_t
            if input_dim == 675
            else x_pos_t
        )

        logits = model(
            x_input,
            length,
        )

        probs = torch.softmax(
            logits,
            dim=1,
        )

        ensemble_probs += (
            ENSEMBLE_WEIGHTS[name]
            * probs
        )

    top_probs, top_idx = (
        torch.topk(
            ensemble_probs[0],
            k=top_k,
        )
    )

    return [
        (
            idx2gloss.get(
                idx,
                f"<unknown class {idx}>",
            ),
            prob,
        )

        for prob, idx in zip(
            top_probs.tolist(),
            top_idx.tolist(),
        )
    ]