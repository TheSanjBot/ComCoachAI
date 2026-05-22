from collections import Counter
from dataclasses import dataclass
from math import dist
from pathlib import Path

import cv2
import mediapipe as mp

from app.core.config import settings
from app.schemas.analysis import (
    EyeContactAnalysis,
    MalpracticeAnalysis,
    PostureAnalysis,
    VideoBehaviorAnalysisResult,
)


def _clamp(value: float, minimum: int = 0, maximum: int = 100) -> int:
    return max(minimum, min(int(round(value)), maximum))


@dataclass
class FrameCounters:
    sampled_frames: int = 0
    direct_gaze_frames: int = 0
    looking_away_frames: int = 0
    downward_gaze_frames: int = 0
    total_face_frames: int = 0
    stable_frames: int = 0
    leaning_frames: int = 0
    slouching_frames: int = 0
    multiple_face_frames: int = 0
    closed_eye_frames: int = 0


class VideoAnalysisService:
    @staticmethod
    def cv2_available() -> bool:
        return True

    @staticmethod
    def mediapipe_available() -> bool:
        return True

    def analyze(
        self,
        recording_path: Path,
        face_detection_state: str,
    ) -> VideoBehaviorAnalysisResult:
        warnings: list[str] = []
        capture = cv2.VideoCapture(str(recording_path))
        fps = capture.get(cv2.CAP_PROP_FPS) or 24.0
        sample_every_n_frames = max(int(fps * settings.video_analysis_sample_interval_seconds), 1)
        counters = FrameCounters()
        eye_states: list[str] = []
        shoulder_centers: list[tuple[float, float]] = []

        face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            refine_landmarks=True,
            max_num_faces=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        pose = mp.solutions.pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        try:
            frame_index = 0
            while True:
                success, frame = capture.read()
                if not success:
                    break
                if frame_index % sample_every_n_frames != 0:
                    frame_index += 1
                    continue

                counters.sampled_frames += 1
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                face_result = face_mesh.process(rgb_frame)
                pose_result = pose.process(rgb_frame)

                face_landmarks = getattr(face_result, "multi_face_landmarks", None) or []
                face_count = len(face_landmarks)
                if face_count > 1:
                    counters.multiple_face_frames += 1

                if face_count >= 1:
                    counters.total_face_frames += 1
                    gaze_state = self._classify_gaze(face_landmarks[0], frame.shape)
                    eye_states.append(gaze_state)
                    if gaze_state == "direct":
                        counters.direct_gaze_frames += 1
                    elif gaze_state == "downward":
                        counters.downward_gaze_frames += 1
                    elif gaze_state == "closed":
                        counters.closed_eye_frames += 1
                        counters.looking_away_frames += 1
                    else:
                        counters.looking_away_frames += 1

                pose_landmarks = getattr(pose_result, "pose_landmarks", None)
                if pose_landmarks is not None:
                    posture_state, shoulder_center = self._classify_posture(
                        pose_landmarks.landmark
                    )
                    shoulder_centers.append(shoulder_center)
                    if posture_state == "stable":
                        counters.stable_frames += 1
                    elif posture_state == "leaning":
                        counters.leaning_frames += 1
                    else:
                        counters.slouching_frames += 1

                frame_index += 1
        finally:
            capture.release()
            face_mesh.close()
            pose.close()

        if counters.sampled_frames == 0:
            raise RuntimeError("No frames were sampled from the recording for video analysis.")

        instability_index = self._calculate_instability_index(shoulder_centers)
        repeated_looking_away_events = self._count_streak_events(eye_states, "away")
        excessive_downward_gaze_events = self._count_streak_events(eye_states, "downward")

        eye_contact_score = _clamp(
            ((counters.direct_gaze_frames / max(counters.total_face_frames, 1)) * 100)
            - counters.downward_gaze_frames * 3.5
            - counters.looking_away_frames * 2.2
            - counters.closed_eye_frames * 4.0
        )
        posture_score = _clamp(
            100
            - counters.leaning_frames * 7.5
            - counters.slouching_frames * 10.5
            - instability_index * 42
        )
        malpractice_confidence_score = _clamp(
            repeated_looking_away_events * 14
            + excessive_downward_gaze_events * 12
            + counters.closed_eye_frames * 5
            + counters.multiple_face_frames * 22
        )

        return VideoBehaviorAnalysisResult(
            sampled_frame_count=counters.sampled_frames,
            frame_sample_interval_seconds=settings.video_analysis_sample_interval_seconds,
            eye_contact=EyeContactAnalysis(
                eye_contact_score=eye_contact_score,
                direct_gaze_frames=counters.direct_gaze_frames,
                looking_away_frames=counters.looking_away_frames,
                downward_gaze_frames=counters.downward_gaze_frames,
                total_face_frames=counters.total_face_frames,
            ),
            posture=PostureAnalysis(
                posture_score=posture_score,
                stable_frames=counters.stable_frames,
                leaning_frames=counters.leaning_frames,
                slouching_frames=counters.slouching_frames,
                instability_index=round(instability_index, 3),
            ),
            malpractice=MalpracticeAnalysis(
                malpractice_confidence_score=malpractice_confidence_score,
                repeated_looking_away_events=repeated_looking_away_events,
                excessive_downward_gaze_events=excessive_downward_gaze_events,
                multiple_face_frames=counters.multiple_face_frames,
                summary=(
                    f"Detected {repeated_looking_away_events} looking-away patterns, "
                    f"{excessive_downward_gaze_events} downward-gaze patterns, and "
                    f"{counters.multiple_face_frames} multi-face samples."
                ),
            ),
            warnings=warnings,
        )

    @staticmethod
    def _classify_gaze(face_landmarks, frame_shape: tuple[int, int, int]) -> str:
        points = face_landmarks.landmark
        frame_height, frame_width = frame_shape[:2]

        def to_xy(index: int) -> tuple[float, float]:
            landmark = points[index]
            return landmark.x * frame_width, landmark.y * frame_height

        left_outer = to_xy(33)
        left_inner = to_xy(133)
        left_top = to_xy(159)
        left_bottom = to_xy(145)
        left_iris = to_xy(468)

        right_outer = to_xy(362)
        right_inner = to_xy(263)
        right_top = to_xy(386)
        right_bottom = to_xy(374)
        right_iris = to_xy(473)

        left_ratio = VideoAnalysisService._ratio_between(left_iris[0], left_outer[0], left_inner[0])
        right_ratio = VideoAnalysisService._ratio_between(right_iris[0], right_inner[0], right_outer[0])
        vertical_ratio = (
            VideoAnalysisService._ratio_between(left_iris[1], left_top[1], left_bottom[1])
            + VideoAnalysisService._ratio_between(right_iris[1], right_top[1], right_bottom[1])
        ) / 2
        left_eye_open_ratio = abs(left_bottom[1] - left_top[1]) / max(
            abs(left_inner[0] - left_outer[0]), 1.0
        )
        right_eye_open_ratio = abs(right_bottom[1] - right_top[1]) / max(
            abs(right_outer[0] - right_inner[0]), 1.0
        )
        eye_open_ratio = (left_eye_open_ratio + right_eye_open_ratio) / 2

        face_left = to_xy(234)
        face_right = to_xy(454)
        nose_tip = to_xy(1)
        chin = to_xy(152)
        face_center_x = (face_left[0] + face_right[0]) / 2
        face_width = max(abs(face_right[0] - face_left[0]), 1.0)
        head_yaw_ratio = abs(nose_tip[0] - face_center_x) / face_width
        eye_center_y = (left_iris[1] + right_iris[1]) / 2
        head_pitch_ratio = abs(nose_tip[1] - eye_center_y) / max(abs(chin[1] - eye_center_y), 1.0)

        horizontal_average = (left_ratio + right_ratio) / 2
        if eye_open_ratio < 0.12:
            return "closed"
        if vertical_ratio > 0.58 or head_pitch_ratio > 0.32:
            return "downward"
        if head_yaw_ratio > 0.06:
            return "away"
        if eye_open_ratio < 0.16:
            return "away"
        if 0.46 <= horizontal_average <= 0.54 and 0.36 <= vertical_ratio <= 0.54:
            return "direct"
        return "away"

    @staticmethod
    def _classify_posture(pose_landmarks) -> tuple[str, tuple[float, float]]:
        left_shoulder = pose_landmarks[11]
        right_shoulder = pose_landmarks[12]
        nose = pose_landmarks[0]
        left_hip = pose_landmarks[23]
        right_hip = pose_landmarks[24]

        shoulder_width = max(
            dist((left_shoulder.x, left_shoulder.y), (right_shoulder.x, right_shoulder.y)),
            0.01,
        )
        shoulder_mid_x = (left_shoulder.x + right_shoulder.x) / 2
        shoulder_mid_y = (left_shoulder.y + right_shoulder.y) / 2
        hip_mid_y = (left_hip.y + right_hip.y) / 2
        head_height_ratio = (shoulder_mid_y - nose.y) / shoulder_width
        lean_ratio = abs(nose.x - shoulder_mid_x) / shoulder_width
        torso_compression = (hip_mid_y - shoulder_mid_y) / shoulder_width
        shoulder_tilt = abs(left_shoulder.y - right_shoulder.y) / shoulder_width

        if head_height_ratio < 0.5 or torso_compression < 0.58:
            return "slouching", (shoulder_mid_x, shoulder_mid_y)
        if lean_ratio > 0.18 or shoulder_tilt > 0.08:
            return "leaning", (shoulder_mid_x, shoulder_mid_y)
        return "stable", (shoulder_mid_x, shoulder_mid_y)

    @staticmethod
    def _ratio_between(value: float, start: float, end: float) -> float:
        low, high = sorted((start, end))
        if abs(high - low) < 1e-6:
            return 0.5
        return (value - low) / (high - low)

    @staticmethod
    def _calculate_instability_index(shoulder_centers: list[tuple[float, float]]) -> float:
        if len(shoulder_centers) < 2:
            return 0.0
        average_x = sum(point[0] for point in shoulder_centers) / len(shoulder_centers)
        average_y = sum(point[1] for point in shoulder_centers) / len(shoulder_centers)
        mean_distance = sum(
            dist(point, (average_x, average_y)) for point in shoulder_centers
        ) / len(shoulder_centers)
        return mean_distance

    @staticmethod
    def _count_streak_events(states: list[str], target_state: str) -> int:
        events = 0
        streak = 0
        for state in states:
            if state == target_state:
                streak += 1
                if streak == 2:
                    events += 1
            else:
                streak = 0
        return events
