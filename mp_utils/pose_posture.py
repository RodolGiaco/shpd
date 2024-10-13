from mp_utils import mp_pose

class PoseDetection():  # Renombramos la clase para hacerla más precisa

    def __init__(self,
                pose_model_asset_path='model/pose_landmarker_full.task',
                min_pose_detection_confidence=0.3,
                min_pose_presence_confidence=0.3,
                min_pose_tracking_confidence=0.3,
                ):
        self.pose = mp_pose.PoseDetection(
                model_asset_path=pose_model_asset_path,
                min_pose_detection_confidence=min_pose_detection_confidence,
                min_pose_presence_confidence=min_pose_presence_confidence,
                min_tracking_confidence=min_pose_tracking_confidence,
                )

    def close(self):
        self.pose.close()

    def extract_pose(self, image):
        return self.pose.extract_pose(image)

    def draw_pose(self, image):
        return self.pose.draw_pose(image)
