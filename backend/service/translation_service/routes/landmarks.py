from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from database import engine
import numpy as np
import time

router = APIRouter(
    prefix="/landmark",
    tags=["Landmarks"],
)


@router.get("/{word}")
def get_landmark(word: str):

    start = time.perf_counter()

    word = word.strip().upper()

    query = text("""
        SELECT text, landmarks
        FROM landmarks
        WHERE UPPER(text) = :word
        LIMIT 1
    """)

    with engine.connect() as connection:
        result = connection.execute(
            query,
            {"word": word}
        ).mappings().first()

    db_time = time.perf_counter()

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"No landmarks found for '{word}'"
        )

    data = np.asarray(
        result["landmarks"],
        dtype=np.float32
    )

    data = data.reshape(-1, 1629)

    frames = []

    for frame in data:
        frames.append({
            "left_hand": frame[0:63].reshape(21, 3).tolist(),
            "right_hand": frame[63:126].reshape(21, 3).tolist(),
            "pose": frame[126:225].reshape(33, 3).tolist(),
            "face": frame[225:1629].reshape(468, 3).tolist(),
        })

    processing_time = time.perf_counter()

    print(
        f"DB: {db_time - start:.3f}s | "
        f"Processing: {processing_time - db_time:.3f}s | "
        f"Total: {processing_time - start:.3f}s"
    )

    return {
        "text": result["text"],
        "fps": 30,
        "frame_count": len(frames),
        "frames": frames,
    }
    