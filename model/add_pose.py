import cv2
import mediapipe as mp
import csv
import copy
import itertools
import time
import numpy as np
from mediapipe.framework.formats import landmark_pb2
from mediapipe import solutions


# Constants and Global Variables
NUMBER = 2  # Initial pose class number
record_count = 0  # Counter for pose data records

# Styling for keypoints (red) and connections (thick white)
LANDMARK_STYLE = mp.solutions.drawing_utils.DrawingSpec(
    color=(0, 0, 255), thickness=2, circle_radius=3
)
CONNECTION_STYLE = mp.solutions.drawing_utils.DrawingSpec(
    color=(255, 255, 255), thickness=5
)

# Custom connections excluding the face landmarks
POSE_CONNECTIONS_WITHOUT_FACE = [
    (11, 12), (12, 14), (14, 16),  # Right arm
    (11, 13), (13, 15), (15, 17),  # Left arm
    (23, 24), (24, 26), (26, 28),  # Right leg
    (23, 25), (25, 27), (27, 29),  # Left leg
    (11, 23), (12, 24), (23, 24), (23, 25), (24, 26), (25, 27), (26, 28)  # Torso
]

class PoseLandmarkerAndResult():
    def __init__(self):
        self.result = mp.tasks.vision.PoseLandmarkerResult
        self.landmarker = mp.tasks.vision.PoseLandmarker
        self.create_landmarker()

    def create_landmarker(self):
        # callback function
        def update_result(result: mp.tasks.vision.PoseLandmarkerResult, output_image: mp.Image, timestamp_ms: int):
            self.result = result 

        options = mp.tasks.vision.PoseLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path="model/pose_landmarker_full.task"),
            running_mode=mp.tasks.vision.RunningMode.LIVE_STREAM,
            min_pose_detection_confidence = 0.4, 
            min_pose_presence_confidence = 0.3, # lower than value to get predictions more often
            min_tracking_confidence = 0.3,  # lower than value to get predictions more often
            result_callback=update_result  # Callback para actualizar resultados
        )

        # initialize landmarker
        self.landmarker = mp.tasks.vision.PoseLandmarker.create_from_options(options)

   
    def detect_async(self, frame):
        """Performs asynchronous pose detection."""
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        self.landmarker.detect_async(image=mp_image, timestamp_ms=int(time.time() * 1000))

    def close(self):
        """Closes the pose landmarker."""
        self.landmarker.close()


                

# def draw_landmarks_on_image(rgb_image, detection_result):
#     """Draws landmarks on the image if detected."""
#     try:
#         if not detection_result or not detection_result.pose_landmarks:
#             return rgb_image

#         annotated_image = np.copy(rgb_image)
#         for landmarks in detection_result.pose_landmarks:
#             proto_landmarks = landmark_pb2.NormalizedLandmarkList()
#             proto_landmarks.landmark.extend([
#                 landmark_pb2.NormalizedLandmark(x=lm.x, y=lm.y, z=lm.z) for lm in landmarks
#             ])

#             mp.solutions.drawing_utils.draw_landmarks(
#                 annotated_image,
#                 proto_landmarks,
#                 POSE_CONNECTIONS_WITHOUT_FACE,
#                 LANDMARK_STYLE,
#                 CONNECTION_STYLE
#             )
#         return annotated_image
#     except Exception as e:
#         print(f"Error drawing landmarks: {e}")
#         return rgb_image
    
    
    
def draw_landmarks_on_image(rgb_image, detection_result):
    # if pose_results.pose_landmarks:
    try:
        pose_landmarks_list = detection_result.pose_landmarks
        annotated_image = np.copy(rgb_image)
        # Loop through the detected poses to visualize.
        for idx in range(len(pose_landmarks_list)):
            pose_landmarks = pose_landmarks_list[idx]
            # Draw the pose landmarks.
            pose_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
            pose_landmarks_proto.landmark.extend([
                landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z) for landmark in pose_landmarks
            ])
            solutions.drawing_utils.draw_landmarks(
                annotated_image,
                pose_landmarks_proto,
                solutions.pose.POSE_CONNECTIONS,
                solutions.drawing_styles.get_default_pose_landmarks_style()
            )
        return annotated_image       
    except:
        return rgb_image
  
INCLUDED_LANDMARKS = [11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28]

def filter_landmarks(landmarks):
    """Filters landmarks to include only specific joints."""
    return [landmark for idx, landmark in enumerate(landmarks) if idx in INCLUDED_LANDMARKS]

 
def add_to_csv(image, results, writer):
    """Adds the detected landmarks to the CSV."""
    global record_count
    if results.pose_landmarks:
        for landmarks in results.pose_landmarks:
            filtered_landmarks = filter_landmarks(landmarks)
            landmark_list = calc_landmark_list(image, filtered_landmarks)
            processed_list = pre_process_landmark(landmark_list)
            writer.writerow([NUMBER, *processed_list])
            print(f"WRITE {record_count}")
            record_count += 1


def calc_landmark_list(image, landmarks):
    """Calculates pixel coordinates of landmarks."""
    height, width, _ = image.shape
    return [[
        min(int(lm.x * width), width - 1),
        min(int(lm.y * height), height - 1),
        lm.z
    ] for lm in landmarks]


def pre_process_landmark(landmark_list):
    """Processes landmarks to relative coordinates and normalizes them."""
    temp_list = copy.deepcopy(landmark_list)
    base_x, base_y, base_z = temp_list[0]

    for point in temp_list:
        point[0] -= base_x
        point[1] -= base_y
        point[2] -= base_z

    flat_list = list(itertools.chain.from_iterable(temp_list))
    max_value = max(map(abs, flat_list), default=1)

    return [n / max_value for n in flat_list]

def validar_csv(csv_path):
    """Validates the structure of the CSV file."""
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        for line_num, row in enumerate(reader, start=1):
            if len(row) != 37:
                print(f"Error on line {line_num}: found {len(row)} columns, expected 37.")
                return False

            z_values = map(float, row[3::3])
            if all(z == 0.0 for z in z_values):
                print(f"Warning on line {line_num}: all Z coordinates are 0.")
                return False

        print("CSV validation successful.")
        return True

    
cap = cv2.VideoCapture(0)
pose_landmarker = PoseLandmarkerAndResult()
csv_path = 'model/new_pose_data.csv'  

with open(csv_path, 'a', newline="") as f:
    writer = csv.writer(f)
    while True:
        # pull frame
        ret, frame = cap.read()
        # mirror frame
        frame = cv2.flip(frame, 1)
        height, width, _ = frame.shape
        # frame_resized = cv2.resize(frame, (width/2, height/2))
        min_dimension = min(height, width)
        start_x = int((width - min_dimension) / 2)
        start_y = int((height - min_dimension) / 2)

        # Crop the frame to a square
        square_frame = frame[start_y:start_y + min_dimension, start_x:start_x + min_dimension]
        square_frame = np.array(square_frame)
        # square_frame = frame

        # update landmarker results
        pose_landmarker.detect_async(square_frame)
        # draw landmarks on frame
        square_frame = draw_landmarks_on_image(square_frame,pose_landmarker.result)

        # display image
        cv2.putText(square_frame, f'{NUMBER}', (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 0, 0), 2)
        cv2.imshow('frame',square_frame)
        key = cv2.waitKey(1)

        if key == ord('q'):
            break
        elif key == ord(' '):
            add_to_csv(square_frame, pose_landmarker.result, writer)
        elif key == ord('n'):
            NUMBER += 1
            i = 0
        elif key == ord('p'):
            NUMBER -= 1
            i = 0

    
pose_landmarker.close()
validar_csv(csv_path)
cap.release()
cv2.destroyAllWindows()