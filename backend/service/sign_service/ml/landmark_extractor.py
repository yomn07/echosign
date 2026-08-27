import numpy as np
import cv2
import mediapipe as mp


N_HAND_LANDMARKS = 21
N_POSE_LANDMARKS = 33


class VideoLandmarkExtractor:

    def __init__(self):

        self.hands = (
            mp.solutions.hands.Hands(
                static_image_mode=False,
                max_num_hands=2,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
        )

        self.pose = (
            mp.solutions.pose.Pose(
                static_image_mode=False,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
        )

    def _landmarks_to_array(
        self,
        landmark_list,
        n_expected,
    ):

        if landmark_list is None:

            return np.zeros(
                n_expected * 3,
                dtype=np.float32,
            )

        pts = np.array(
            [
                [
                    lm.x,
                    lm.y,
                    lm.z,
                ]

                for lm in landmark_list.landmark
            ],
            dtype=np.float32,
        )

        return pts.flatten()

    def extract_frame(
        self,
        frame_bgr,
    ):

        frame_rgb = cv2.cvtColor(
            frame_bgr,
            cv2.COLOR_BGR2RGB,
        )

        frame_rgb.flags.writeable = False

        hand_results = (
            self.hands.process(
                frame_rgb
            )
        )

        pose_results = (
            self.pose.process(
                frame_rgb
            )
        )

        left_hand = np.zeros(
            N_HAND_LANDMARKS * 3,
            dtype=np.float32,
        )

        right_hand = np.zeros(
            N_HAND_LANDMARKS * 3,
            dtype=np.float32,
        )

        if (
            hand_results.multi_hand_landmarks
            and hand_results.multi_handedness
        ):

            for (
                hand_lms,
                handedness,
            ) in zip(
                hand_results.multi_hand_landmarks,
                hand_results.multi_handedness,
            ):

                label = (
                    handedness
                    .classification[0]
                    .label
                )

                arr = (
                    self._landmarks_to_array(
                        hand_lms,
                        N_HAND_LANDMARKS,
                    )
                )

                if label == "Left":

                    left_hand = arr

                else:

                    right_hand = arr

        pose_arr = (
            self._landmarks_to_array(
                pose_results.pose_landmarks,
                N_POSE_LANDMARKS,
            )
        )

        return np.concatenate(
            [
                left_hand,
                right_hand,
                pose_arr,
            ]
        )

    def close(self):

        self.hands.close()

        self.pose.close()