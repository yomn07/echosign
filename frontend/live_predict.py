"""
Live webcam sign recognition, push-to-record style:
  - Press 'r' to START recording (buffers frames + extracts landmarks live)
  - Press 'r' again to STOP recording and run prediction
  - Press 'q' to quit

Models load ONCE at startup (not per-clip), so repeated signs are fast after
the initial load. Reuses your exact preprocessing + ensemble logic from
predict_video.py.

Top-1 prediction is spoken aloud via pyttsx3. The TTS engine is created
once at startup and speech runs on a background thread (with a lock) so
a several-hundred-ms "say the word" call never freezes the camera preview.

Note: this is push-to-record, not continuous auto-detection -- the model
was trained on isolated, pre-trimmed clips, so it has no notion of "no sign
being performed." Auto-segmentation (motion-based start/stop detection) is
a further step up in complexity; ask if you want that built next.
"""

import threading
import time

import cv2
import numpy as np
import pyttsx3

from extract_single_video import VideoLandmarkExtractor
from live_predict import load_all_models, build_idx2gloss, predict_from_landmarks, TRAIN_JSONL, TOP_K

MAX_RECORD_FRAMES = 300  # safety cap, same as file-based extraction
RESULT_DISPLAY_SECONDS = 4.0  # how long to show the last prediction before clearing it

TTS_RATE = 175   # words per minute; pyttsx3 default is ~200, slightly slower reads clearer
TTS_VOLUME = 1.0


class Speaker:
    """
    pyttsx3 has a well-documented cross-platform quirk: reusing a single
    engine instance's runAndWait() from a new thread on every call works
    the first time, then goes silent afterward (especially on Windows'
    SAPI5 driver, whose COM initialization is thread-affine). The reliable
    fix is to create a fresh engine per speak() call rather than reusing
    one - costs ~100-300ms of init overhead each time, but actually keeps
    speaking on every call instead of just the first.
    """

    def __init__(self, rate=TTS_RATE, volume=TTS_VOLUME):
        self.rate = rate
        self.volume = volume
        self._lock = threading.Lock()

    def speak(self, text):
        def _run():
            with self._lock:
                engine = pyttsx3.init()
                engine.setProperty("rate", self.rate)
                engine.setProperty("volume", self.volume)
                engine.say(text)
                engine.runAndWait()
                engine.stop()

        threading.Thread(target=_run, daemon=True).start()


def main():
    print("Loading models (one-time)...")
    models = load_all_models()
    print("Building gloss lookup...")
    idx2gloss = build_idx2gloss()
    print("Initializing speech...")
    speaker = Speaker()
    print("Ready.")

    extractor = VideoLandmarkExtractor()
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Could not open webcam (device 0). Try a different index if you have multiple cameras.")

    recording = False
    buffered_landmarks = []
    last_results = None
    last_result_time = 0.0
    r_press_count = 0  # odd press = start recording, even (paired) press = stop + speak

    print("\nPress 'r' to start/stop recording a sign. Press 'q' to quit.\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        display_frame = frame.copy()

        if recording:
            landmarks = extractor.extract_frame(frame)
            buffered_landmarks.append(landmarks)

            cv2.putText(display_frame, f"RECORDING ({len(buffered_landmarks)} frames)",
                        (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            if len(buffered_landmarks) >= MAX_RECORD_FRAMES:
                recording = False
                cv2.putText(display_frame, "Max length reached, stopping...",
                            (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        else:
            cv2.putText(display_frame, "Press 'r' to record a sign",
                        (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        if last_results is not None and (time.time() - last_result_time) < RESULT_DISPLAY_SECONDS:
            y = 100
            for rank, (gloss, prob) in enumerate(last_results, 1):
                cv2.putText(display_frame, f"{rank}. {gloss} ({prob:.2f})",
                            (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                y += 30

        cv2.imshow("Sign Recognition (press 'r' to record, 'q' to quit)", display_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r'):
            r_press_count += 1

            if r_press_count % 2 == 1:
                # odd press: start recording
                recording = True
                buffered_landmarks = []
                last_results = None
                print(f"Recording started... (press #{r_press_count})")
            else:
                # even (paired) press: stop recording and always speak something
                recording = False
                print(f"Recording stopped (press #{r_press_count}, {len(buffered_landmarks)} frames). Predicting...")

                if len(buffered_landmarks) < 5:
                    print("  Too short, ignoring.")
                    speaker.speak("Too short, try again")
                else:
                    raw_landmarks = np.stack(buffered_landmarks, axis=0)
                    last_results = predict_from_landmarks(raw_landmarks, models, idx2gloss, top_k=TOP_K)
                    last_result_time = time.time()

                    print(f"  Top-{TOP_K}:")
                    for rank, (gloss, prob) in enumerate(last_results, 1):
                        print(f"    {rank}. {gloss}  ({prob:.4f})")

                    top1_gloss, top1_prob = last_results[0]
                    speaker.speak(top1_gloss)

    cap.release()
    extractor.close()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()