from mp_utils import mp_pose

class PoseDetectionPosture:
    def __init__(self,
                 static_image_mode=False,
                 model_complexity=1,
                 min_pose_detection_confidence=0.3,
                 min_pose_tracking_confidence=0.3):
        self.pose = mp_pose.PoseDetection(
            min_detection_confidence=min_pose_detection_confidence,
            min_tracking_confidence=min_pose_tracking_confidence
        )

    def close(self):
        self.pose.close()

    def extract_pose(self, image):
        return self.pose.extract_pose(image)

    def draw_pose(self, image):
        return self.pose.draw_pose(image)

