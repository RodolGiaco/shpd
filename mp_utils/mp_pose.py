import cv2
import mediapipe as mp
import numpy as np

class PoseDetection:
    def __init__(self,
                 static_image_mode=False,
                 model_complexity=1,
                 enable_segmentation=False,
                 min_detection_confidence=0.3,
                 min_tracking_confidence=0.3):
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_styles = mp.solutions.drawing_styles

        self.pose = self.mp_pose.Pose(
            static_image_mode=static_image_mode,
            model_complexity=model_complexity,
            enable_segmentation=enable_segmentation,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        self.results = None

    def close(self):
        self.pose.close()

    def extract_pose(self, image):
        if image is None:
            return None

        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        self.results = self.pose.process(image_rgb)

        keypoints = []
        if self.results.pose_landmarks:
            for landmark in self.results.pose_landmarks.landmark:
                keypoints.append([
                    landmark.x,
                    landmark.y,
                    landmark.z,
                    landmark.visibility
                ])
        return keypoints

    def draw_pose(self, image):
        if self.results is None or not self.results.pose_landmarks:
            return image

        annotated_image = image.copy()
        self.mp_drawing.draw_landmarks(
            annotated_image,
            self.results.pose_landmarks,
            self.mp_pose.POSE_CONNECTIONS,
            self.mp_styles.get_default_pose_landmarks_style()
        )
        return annotated_image

    def filter_landmarks(self):
        """
        Devuelve solo los puntos relevantes del torso y extremidades.
        Índices relevantes: 11–16 (hombros y brazos), 23–28 (caderas y piernas)
        """
        if self.results is None or not self.results.pose_landmarks:
            return []

        included_landmarks = [11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28]
        landmarks = self.results.pose_landmarks.landmark
        return [
            [landmarks[i].x, landmarks[i].y, landmarks[i].z, landmarks[i].visibility]
            for i in included_landmarks
        ]

