import json

import cv2
import numpy as np

from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
)

from config import MAX_FRAMES

from ml.models import (
    models,
    idx2gloss,
    extractor,
)

from ml.predictor import (
    predict_from_landmarks,
)

from processing.predictions import (
    format_predictions,
    xy_pairs,
)


router = APIRouter(
    prefix="/ws",
    tags=["WebSocket"],
)


@router.websocket("/sign")
async def sign_detection(
    websocket: WebSocket,
):

    await websocket.accept()

    print(
        "Client connected"
    )

    # ======================================================
    # SESSION STATE
    # ======================================================

    frames = []

    recording = False

    try:

        while True:

            message = (
                await websocket.receive()
            )

            # ==================================================
            # JSON COMMAND
            # ==================================================

            if "text" in message:

                try:

                    command = json.loads(
                        message["text"]
                    )

                except json.JSONDecodeError:

                    await websocket.send_json({
                        "type": "error",
                        "message":
                            "Invalid JSON",
                    })

                    continue

                action = command.get(
                    "action"
                )

                # ----------------------------------------------
                # START
                # ----------------------------------------------

                if action == "start":

                    print(
                        "Recording started"
                    )

                    frames = []

                    recording = True

                    await websocket.send_json({
                        "type":
                            "recording",

                        "status":
                            "recording",
                    })

                    continue

                # ----------------------------------------------
                # STOP
                # ----------------------------------------------

                if action == "stop":

                    print(
                        "Recording stopped"
                    )

                    recording = False

                    if not frames:

                        await websocket.send_json({
                            "type":
                                "prediction",

                            "prediction":
                                [],

                            "message":
                                "No frames recorded",
                        })

                        continue

                    print(
                        "Predicting",
                        len(frames),
                        "frames...",
                    )

                    prediction = (
                        predict_from_landmarks(
                            frames,
                            models,
                            idx2gloss,
                        )
                    )

                    results = (
                        format_predictions(
                            prediction
                        )
                    )

                    await websocket.send_json({
                        "type":
                            "prediction",

                        "prediction":
                            results,
                    })

                    frames = []

                    continue

                # ----------------------------------------------
                # UNKNOWN COMMAND
                # ----------------------------------------------

                await websocket.send_json({
                    "type":
                        "error",

                    "message":
                        f"Unknown action: {action}",
                })

                continue

            # ==================================================
            # VIDEO FRAME
            # ==================================================

            if "bytes" in message:

                data = message[
                    "bytes"
                ]

                img_array = (
                    np.frombuffer(
                        data,
                        np.uint8,
                    )
                )

                frame = cv2.imdecode(
                    img_array,
                    cv2.IMREAD_COLOR,
                )

                if frame is None:

                    continue

                # ----------------------------------------------
                # LANDMARK EXTRACTION
                # ----------------------------------------------

                landmarks = (
                    extractor.extract_frame(
                        frame
                    )
                )

                if landmarks is None:

                    continue

                # ----------------------------------------------
                # SEND LANDMARKS
                # ----------------------------------------------

                await websocket.send_json({
                    "type":
                        "landmarks",

                    "landmarks": {

                        "left_hand":
                            xy_pairs(
                                landmarks,
                                0,
                                63,
                            ),

                        "right_hand":
                            xy_pairs(
                                landmarks,
                                63,
                                126,
                            ),

                        "pose":
                            xy_pairs(
                                landmarks,
                                126,
                                225,
                            ),
                    },
                })

                # ----------------------------------------------
                # RECORD
                # ----------------------------------------------

                if recording:

                    frames.append(
                        landmarks
                    )

                    # ------------------------------------------
                    # MAXIMUM FRAMES
                    # ------------------------------------------

                    if (
                        len(frames)
                        >= MAX_FRAMES
                    ):

                        print(
                            "Maximum frames reached"
                        )

                        recording = False

                        prediction = (
                            predict_from_landmarks(
                                frames,
                                models,
                                idx2gloss,
                            )
                        )

                        results = (
                            format_predictions(
                                prediction
                            )
                        )

                        await websocket.send_json({
                            "type":
                                "prediction",

                            "prediction":
                                results,
                        })

                        frames = []

    except WebSocketDisconnect:

        print(
            "Client disconnected"
        )

    except Exception as e:

        print(
            "WebSocket error:",
            repr(e),
        )

        try:

            await websocket.send_json({
                "type":
                    "error",

                "message":
                    "WebSocket processing error",
            })

        except Exception:

            pass

    finally:

        print(
            "WebSocket connection closed"
        )
