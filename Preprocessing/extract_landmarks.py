"""
Landmark Extraction (YouTube + generic direct-video URLs)
====================================================================
  - THREE SEPARATE MediaPipe solutions (Hands, Pose, FaceMesh), each run
    independently on the full frame -- NOT the combined Holistic model.
    Same parameters as preprocess_msasl.py:
        Hands:    max_num_hands=2, min_detection_confidence=0.5,
                  min_tracking_confidence=0.5
        Pose:     min_detection_confidence=0.5, min_tracking_confidence=0.5
        FaceMesh: max_num_faces=1, refine_landmarks=False,
                  min_detection_confidence=0.5, min_tracking_confidence=0.5
  - NO normalization/centering step -- raw landmark.x/y/z, concatenated
    directly as [left_hand(63) | right_hand(63) | pose(99) | face(1404)]
  - For YouTube clips with a KNOWN end_sec: uses yt-dlp's
    --download-sections to pull ONLY the needed time window server-side
    (matches preprocess_msasl.py's download_and_trim_clip exactly,
    including its duration sanity check: skip if <=0s or >30s).
  - For entries with end_sec=None (WLASL's frame_end=-1, "runs to end of
    video" -- MS-ASL never has this case, all its clips have both
    start_time/end_time) or non-YouTube URLs: downloads the full video,
    then crops client-side with a --max_frames safety cap.

Produces:
  - landmarks_dir/sample_{index:06d}.npy  — one file per successful clip
  - metadata.jsonl
    (index, label, text, signer_id, num_frames, feature_dim, landmark_file)
  - extraction_fail_log.jsonl — every failure logged IN THIS PASS with a
    reason + the full original entry, no separate retry script needed.

RESUMABLE: if landmarks_dir/sample_{index:06d}.npy already exists, that
entry is skipped instantly.

USAGE:
    python extract_wlasl_landmarks.py --input merged_output/wlasl_downloadable.jsonl --landmarks_dir merged_output/landmarks_wlasl --metadata_out merged_output/metadata_wlasl.jsonl --fail_log_out merged_output/extraction_fail_log.jsonl --workers 4 --max_frames 200 --cookies cookies.txt
"""

import argparse
import json
import os
import subprocess
import tempfile
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

import numpy as np
import requests
from tqdm import tqdm
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120 Safari/537.36"
    )
}

# Must match FeatureDims in your model file exactly
N_HAND_LANDMARKS = 21
N_POSE_LANDMARKS = 33
N_FACE_LANDMARKS = 468
FEATURE_DIM = N_HAND_LANDMARKS * 3 * 2 + N_POSE_LANDMARKS * 3 + N_FACE_LANDMARKS * 3  # 1629


# ──────────────────────────────────────────────────────────────────
# LandmarkExtractor — copied verbatim from preprocess_msasl.py so WLASL
# landmarks are numerically consistent with your MS-ASL landmarks.
# ──────────────────────────────────────────────────────────────────
class LandmarkExtractor:
    def __init__(self, include_face=True):
        import mediapipe as mp
        self.mp = mp
        self.include_face = include_face

        self.hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.pose = mp.solutions.pose.Pose(
            static_image_mode=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        if include_face:
            self.face = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=1,
                refine_landmarks=False,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )

        self.N_HAND_LANDMARKS = N_HAND_LANDMARKS
        self.N_POSE_LANDMARKS = N_POSE_LANDMARKS
        self.N_FACE_LANDMARKS = N_FACE_LANDMARKS if include_face else 0

    def _landmarks_to_array(self, landmark_list, n_expected):
        if landmark_list is None:
            return np.zeros(n_expected * 3, dtype=np.float32)
        pts = np.array(
            [[lm.x, lm.y, lm.z] for lm in landmark_list.landmark],
            dtype=np.float32
        )
        return pts.flatten()

    def extract_frame(self, frame_bgr):
        import cv2
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        frame_rgb.flags.writeable = False

        hand_results = self.hands.process(frame_rgb)
        pose_results = self.pose.process(frame_rgb)
        face_results = self.face.process(frame_rgb) if self.include_face else None

        left_hand = np.zeros(self.N_HAND_LANDMARKS * 3, dtype=np.float32)
        right_hand = np.zeros(self.N_HAND_LANDMARKS * 3, dtype=np.float32)

        if hand_results.multi_hand_landmarks and hand_results.multi_handedness:
            for hand_lms, handedness in zip(
                hand_results.multi_hand_landmarks,
                hand_results.multi_handedness
            ):
                label = handedness.classification[0].label
                arr = self._landmarks_to_array(hand_lms, self.N_HAND_LANDMARKS)
                if label == "Left":
                    left_hand = arr
                else:
                    right_hand = arr

        pose_arr = self._landmarks_to_array(
            pose_results.pose_landmarks, self.N_POSE_LANDMARKS
        )

        feature_parts = [left_hand, right_hand, pose_arr]

        if self.include_face:
            face_arr = np.zeros(self.N_FACE_LANDMARKS * 3, dtype=np.float32)
            if face_results.multi_face_landmarks:
                face_arr = self._landmarks_to_array(
                    face_results.multi_face_landmarks[0], self.N_FACE_LANDMARKS
                )
            feature_parts.append(face_arr)

        return np.concatenate(feature_parts)

    def close(self):
        self.hands.close()
        self.pose.close()
        if self.include_face:
            self.face.close()


# ──────────────────────────────────────────────────────────────────
def classify_url(url):
    if not url:
        return "missing"
    domain = urlparse(url).netloc.lower()
    if not domain:
        return "invalid"
    if "youtube.com" in domain or "youtu.be" in domain:
        return "youtube"
    return domain


# ──────────────────────────────────────────────────────────────────
# Download
# ──────────────────────────────────────────────────────────────────
def download_youtube_section(url, start_sec, end_sec, out_path, 
                              timeout=60, cookies_path=None):
    duration = end_sec - start_sec
    if duration <= 0 or duration > 30:
        raise RuntimeError(f"suspicious clip duration {duration:.1f}s")

    section_arg = f"*{start_sec}-{end_sec}"
    cookie_args = ["--cookies", cookies_path] if cookies_path else []

    cmd = [
        "yt-dlp", "--quiet", "--no-warnings",
        "--js-runtimes", "node",
        "--extractor-args", "youtube:player_client=android",
        *cookie_args,
        "--download-sections", section_arg,
        "--force-keyframes-at-cuts",
        "-f", "mp4[height<=480]/mp4/best",
        "-o", str(out_path),
        url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp failed: {result.stderr.strip()[:200]}")
    if not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
        raise RuntimeError("yt-dlp reported success but no output file produced")

def download_youtube_full(url, out_path, timeout=90, cookies_path=None):
    cookie_args = ["--cookies", cookies_path] if cookies_path else []

    cmd = [
        "yt-dlp", "--quiet", "--no-warnings",
        "--js-runtimes", "node",
        "--extractor-args", "youtube:player_client=android",
        *cookie_args,
        "-f", "mp4[height<=480]/mp4/best",
        "--merge-output-format", "mp4",
        "--no-playlist",
        "-o", str(out_path),
        url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp failed: {result.stderr.strip()[:200]}")
    if not os.path.exists(out_path):
        candidates = list(Path(out_path).parent.glob(Path(out_path).stem + ".*"))
        if candidates:
            os.rename(candidates[0], out_path)
        else:
            raise RuntimeError("no output file found after download")

def download_generic(url, out_path):
    r = requests.get(url, headers=BROWSER_HEADERS, timeout=30,
                      allow_redirects=True, stream=True, verify=False)
    r.raise_for_status()
    with open(out_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=1 << 20):
            f.write(chunk)


# ──────────────────────────────────────────────────────────────────
# Frame reading (mirrors preprocess_msasl.py's extract_landmarks_from_video)
# ──────────────────────────────────────────────────────────────────
def extract_landmarks_from_video(video_path, extractor, start_frame=0,
                                  end_frame=None, max_frames=None):
    """
    Reads frames and runs extractor.extract_frame on each.
    start_frame/end_frame: only used for the client-side-crop path
    (already-trimmed clips from download_youtube_section should pass
    start_frame=0, end_frame=None to read the whole file, matching
    preprocess_msasl.py's behavior exactly for that path).
    """
    import cv2
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError("could not open downloaded video (corrupt or unsupported codec)")

    if start_frame > 0:
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    total_to_read = None
    if end_frame is not None:
        total_to_read = end_frame - start_frame
    if max_frames is not None:
        total_to_read = max_frames if total_to_read is None else min(total_to_read, max_frames)

    frame_features = []
    n_read = 0
    while True:
        if total_to_read is not None and n_read >= total_to_read:
            break
        ret, frame = cap.read()
        if not ret:
            break
        frame_features.append(extractor.extract_frame(frame))
        n_read += 1

    cap.release()

    if len(frame_features) == 0:
        raise RuntimeError("zero frames read from video")

    return np.stack(frame_features, axis=0)


# ──────────────────────────────────────────────────────────────────
# Per-entry worker
# ──────────────────────────────────────────────────────────────────
def process_one(entry, landmarks_dir, max_frames, 
                include_face=True, cookies_path=None):  # add cookies_path
    idx = entry["index"]
    npy_path = os.path.join(landmarks_dir, f"sample_{idx:06d}.npy")

    if os.path.exists(npy_path):
        return {"status": "skipped_existing", "index": idx}

    url = entry.get("url")
    url_type = classify_url(url)
    if url_type in ("missing", "invalid"):
        return {"status": "fail", "index": idx, 
                "reason": f"bad_url:{url_type}", "entry": entry}

    start_sec = entry.get("start_sec") or 0.0
    end_sec = entry.get("end_sec")

    tmp_dir = tempfile.mkdtemp(prefix="wlasl_dl_")
    tmp_path = os.path.join(tmp_dir, f"video_{idx}.mp4")
    extractor = None

    try:
        if url_type == "youtube" and end_sec is not None:
            download_youtube_section(url, start_sec, end_sec, tmp_path,
                                     cookies_path=cookies_path)  # pass through
            extractor = LandmarkExtractor(include_face=include_face)
            landmarks = extract_landmarks_from_video(
                tmp_path, extractor, start_frame=0, 
                end_frame=None, max_frames=max_frames
            )
        elif url_type == "youtube":
            download_youtube_full(url, tmp_path, 
                                  cookies_path=cookies_path)  # pass through
            extractor = LandmarkExtractor(include_face=include_face)
            import cv2
            cap = cv2.VideoCapture(tmp_path)
            fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
            cap.release()
            start_frame = max(0, int(start_sec * fps))
            landmarks = extract_landmarks_from_video(
                tmp_path, extractor, start_frame=start_frame, 
                end_frame=None, max_frames=max_frames
            )
        else:
            # Non-YouTube — cookies don't apply, keep as-is
            download_generic(url, tmp_path)
            extractor = LandmarkExtractor(include_face=include_face)
            import cv2
            cap = cv2.VideoCapture(tmp_path)
            fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.release()
            start_frame = max(0, int(start_sec * fps))
            end_frame = int(end_sec * fps) if end_sec is not None else total_frames
            if total_frames > 0:
                end_frame = min(end_frame, total_frames)
            landmarks = extract_landmarks_from_video(
                tmp_path, extractor, start_frame=start_frame, 
                end_frame=end_frame, max_frames=max_frames
            )

        np.save(npy_path, landmarks)
        return {
            "status": "ok",
            "index": idx,
            "metadata": {
                "index": idx,
                "label": entry["label"],
                "text": entry["text"],
                "signer_id": entry["signer_id"],
                "num_frames": int(landmarks.shape[0]),
                "feature_dim": int(landmarks.shape[1]),
                "landmark_file": os.path.basename(npy_path),
            },
        }
    except Exception as e:
        return {"status": "fail", "index": idx,
                "reason": f"{type(e).__name__}: {str(e)[:300]}",
                "traceback": traceback.format_exc(limit=3),
                "entry": entry}
    finally:
        if extractor is not None:
            extractor.close()
        try:
            for f in os.listdir(tmp_dir):
                os.remove(os.path.join(tmp_dir, f))
            os.rmdir(tmp_dir)
        except OSError:
            pass

# ──────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--landmarks_dir", required=True)
    ap.add_argument("--metadata_out", required=True)
    ap.add_argument("--fail_log_out", required=True)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--max_frames", type=int, default=200)
    ap.add_argument("--include_face", action="store_true", default=True)
    ap.add_argument("--cookies", default=None,
                    help="Path to Netscape-format cookies.txt from a logged-in browser")
    args = ap.parse_args()

    Path(args.landmarks_dir).mkdir(parents=True, exist_ok=True)

    print("Loading entries...")
    entries = []
    with open(args.input, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    print(f"  {len(entries)} entries to process")

    n_ok, n_fail, n_skipped = 0, 0, 0
    with open(args.metadata_out, "a", encoding="utf-8") as meta_f, \
         open(args.fail_log_out, "a", encoding="utf-8") as fail_f, \
         ProcessPoolExecutor(max_workers=args.workers) as executor:

        futures = {
            executor.submit(
                process_one, e, args.landmarks_dir, args.max_frames,
                args.include_face, args.cookies   # pass cookies_path
            ): e
            for e in entries
        }
        for future in tqdm(as_completed(futures), total=len(futures)):
            result = future.result()
            if result["status"] == "ok":
                n_ok += 1
                meta_f.write(json.dumps(result["metadata"]) + "\n")
                meta_f.flush()
            elif result["status"] == "skipped_existing":
                n_skipped += 1
            else:
                n_fail += 1
                fail_f.write(json.dumps({
                    "index": result["index"],
                    "reason": result["reason"],
                    "entry": result.get("entry"),
                }) + "\n")
                fail_f.flush()

    print(f"\nDone — OK: {n_ok} | Skipped: {n_skipped} | Failed: {n_fail}")
    print("\nDone")
    print(f"  Extracted OK: {n_ok}")
    print(f"  Skipped (already extracted): {n_skipped}")
    print(f"  Failed: {n_fail} -> see {args.fail_log_out}")
    print(f"  Metadata -> {args.metadata_out}")


if __name__ == "__main__":
    main()