import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe.framework.formats import landmark_pb2
from mediapipe import solutions

import time
import numpy as np
import cv2 as cv

class PoseDetection:
    def __init__(self,
                 model_asset_path='model/pose_landmarker_heavy.task',
                 min_pose_detection_confidence=0.3,
                 min_pose_presence_confidence=0.3,
                 min_tracking_confidence=0.3) -> None:
        self.pose_result = mp.tasks.vision.PoseLandmarkerResult
        self.landmarker = mp.tasks.vision.PoseLandmarker
        self.pose = None

        self.initialise_pose(
            model_asset_path,
            min_pose_detection_confidence,
            min_pose_presence_confidence,
            min_tracking_confidence
        )

    def initialise_pose(self, model_asset_path,
                        min_pose_detection_confidence,
                        min_pose_presence_confidence,
                        min_tracking_confidence):

        def update_result(result: mp.tasks.vision.PoseLandmarkerResult,
                          output_image: mp.Image, timestamp_ms: int):
            self.pose_result = result

        base_options = python.BaseOptions(model_asset_path=model_asset_path)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=mp.tasks.vision.RunningMode.LIVE_STREAM,
            num_poses=1,
            min_pose_detection_confidence=min_pose_detection_confidence,
            min_pose_presence_confidence=min_pose_presence_confidence,
            min_tracking_confidence=min_tracking_confidence,
            result_callback=update_result
        )
        self.pose = vision.PoseLandmarker.create_from_options(options)

    def close(self):
        self.pose.close()

    def extract_pose(self, image):
        if image is None:
            return None

        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image)
        self.pose.detect_async(image=mp_image, timestamp_ms=int(time.time() * 1000))
        return self.pose_result

    def draw_pose(self, rgb_image):
        try:
            detection_result = self.pose_result
            pose_landmarks_list = detection_result.pose_landmarks
            annotated_image = np.copy(rgb_image)

            # Dibujar solo torso y extremidades.
            for idx in range(len(pose_landmarks_list)):
                pose_landmarks = pose_landmarks_list[idx]

                # Filtrar solo los puntos relevantes: torso y extremidades.
                filtered_landmarks = self.filter_landmarks(pose_landmarks)

                # Dibujar los landmarks.
                pose_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
                pose_landmarks_proto.landmark.extend([
                    landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z)
                    for landmark in pose_landmarks
                ])

                solutions.drawing_utils.draw_landmarks(
                    annotated_image,
                    pose_landmarks_proto,
                    solutions.pose.POSE_CONNECTIONS,
                    solutions.drawing_styles.get_default_pose_landmarks_style()
                )

            return annotated_image
        except Exception as e:
            print(f"Error al dibujar los landmarks: {e}")
            return rgb_image

    def filter_landmarks(self, landmarks):
        # Indices relevantes: hombros, caderas, codos, rodillas, etc.
        INCLUDED_LANDMARKS = [11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28]

        # Filtrar solo los puntos del torso y extremidades.
        return [landmark for idx, landmark in enumerate(landmarks) if idx in INCLUDED_LANDMARKS]

