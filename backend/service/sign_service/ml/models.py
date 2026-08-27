from ml.landmark_extractor import (
    VideoLandmarkExtractor,
)

from ml.predictor import (
    load_all_models,
    build_idx2gloss,
)


print(
    "Loading sign-language models..."
)


models = load_all_models()


print(
    "Loading label mapping..."
)


idx2gloss = build_idx2gloss()


print(
    "Creating landmark extractor..."
)


extractor = VideoLandmarkExtractor()


print(
    "Sign-service models ready."
)