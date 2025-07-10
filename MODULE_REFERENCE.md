# Module Reference Documentation

## mp_utils Module

### Overview
The `mp_utils` module provides utilities for pose detection using MediaPipe. It contains two main components:
- `mp_pose.py`: Core pose detection functionality
- `pose_posture.py`: Specialized wrapper for posture detection

### mp_pose.PoseDetection

#### Class Overview
```python
mp_utils.mp_pose.PoseDetection(
    static_image_mode=False,
    model_complexity=1,
    enable_segmentation=True,
    min_detection_confidence=0.3,
    min_tracking_confidence=0.3
)
```

#### Detailed Method Documentation

##### `extract_pose(image: np.ndarray) -> mediapipe.python.solution_base.SolutionOutputs`

Processes an image to extract pose landmarks.

**Parameters:**
- `image`: BGR image as numpy array

**Returns:**
- MediaPipe pose results containing:
  - `pose_landmarks`: 33 pose landmarks in image coordinates
  - `pose_world_landmarks`: 33 pose landmarks in world coordinates
  - `segmentation_mask`: Binary mask of the person (if enabled)

**Example:**
```python
import cv2
from mp_utils.mp_pose import PoseDetection

detector = PoseDetection()
image = cv2.imread('person.jpg')
results = detector.extract_pose(image)

if results.pose_landmarks:
    for idx, landmark in enumerate(results.pose_landmarks.landmark):
        print(f"Landmark {idx}: x={landmark.x}, y={landmark.y}, z={landmark.z}")
```

##### `filter_landmarks() -> List[List[float]]`

Filters and returns only torso and limb landmarks.

**Included Landmarks:**
- 11-16: Upper body (shoulders, elbows, wrists)
- 23-28: Lower body (hips, knees, ankles)

**Returns:**
```python
[
    [x, y, z, visibility],  # Landmark 11
    [x, y, z, visibility],  # Landmark 12
    # ... etc
]
```

## neural_network Module

### pose_recognition.PoseRecognizer

#### Class Overview
Implements pose gesture recognition using TensorFlow Lite.

#### Internal Processing Pipeline

1. **Landmark Calculation** (`calc_landmark_list`):
   - Converts normalized landmarks to pixel coordinates
   - Filters to include only specific body parts
   - Includes Z-coordinate for depth information

2. **Preprocessing** (`pre_process_landmark`):
   - Converts to relative coordinates (first point as origin)
   - Flattens 3D coordinates to 1D array
   - Normalizes by maximum absolute value

3. **Classification**:
   - Feeds preprocessed landmarks to TFLite model
   - Returns gesture ID with highest confidence

#### Gesture Label Management

The system uses a CSV file to map gesture IDs to names:
```csv
0,Standing
1,Waving
2,Pointing
3,Arms_Up
4,Arms_Down
```

## gui Module

### ThirdPersonGUI

#### Window Management

The GUI manages three separate OpenCV windows:

1. **Camera Window** (`ThirdPerson`):
   - Main view showing pose overlay
   - Full camera feed with landmarks

2. **Info Window** (`Info`):
   - Status information display
   - Shows: Following state, Movement, Battery, Gesture

3. **Hand Window** (`hand`):
   - Optional detailed hand view
   - Currently disabled in main.py

#### Overlay System

The `overlay_text_on_rect` method creates information overlays:
```python
def overlay_text_on_rect(self, frame, text, rect_position, text_position, 
                         font_scale=1, color=(255, 255, 255), thickness=2)
```

Creates a black rectangle background with white text for better visibility.

## instructions Module

### gesture_buffer.GestureBuffer

#### Buffer Algorithm

Implements a rolling buffer with consistency checking:

```python
# Internal flow:
1. Add gesture to deque (fixed size)
2. When full, count most common gesture
3. If count >= min_consistency * buffer_len:
   - Clear buffer
   - Return gesture
4. Else return last valid gesture
```

#### Use Cases
- **High consistency (0.8-0.9)**: Requires very stable pose
- **Low consistency (0.2-0.5)**: More responsive, less stable

### gesture_instructions.Instructions

#### Telegram Integration

Sends notifications via Telegram Bot API:
```python
def send_telegram_message(self, message):
    url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
    data = {"chat_id": self.chat_id, "text": message}
    response = requests.post(url, data=data)
```

**Security Note**: Token and chat ID should be moved to config file.

## model Module

### add_pose.py Utilities

#### Data Collection Functions

##### `add_to_csv(image, results, writer)`
Processes and saves pose data for training:
1. Filters landmarks to relevant joints
2. Calculates pixel coordinates
3. Normalizes relative to first landmark
4. Writes as CSV row: `[gesture_id, x1, y1, z1, x2, y2, z2, ...]`

##### `validar_csv(csv_path)`
Validates training data integrity:
- Checks for 37 columns (1 label + 12 landmarks * 3 coordinates)
- Warns if all Z-values are 0
- Reports malformed rows

#### Custom Landmark Drawing

Provides alternative visualization without face landmarks:
```python
POSE_CONNECTIONS_WITHOUT_FACE = [
    (11, 12), (12, 14), (14, 16),  # Right arm
    (11, 13), (13, 15), (15, 17),  # Left arm
    (23, 24), (24, 26), (26, 28),  # Right leg
    (23, 25), (25, 27), (27, 29),  # Left leg
    (11, 23), (12, 24), (23, 24),  # Torso
]
```

## Configuration Details

### config_pose.json Structure

```json
{
  "constants": {
    "pose": {
      "min_pose_detection_confidence": 0.5,  // Initial detection threshold
      "min_pose_tracking_confidence": 0.5,   // Frame-to-frame tracking
      "min_pose_presence_confidence": 0.5    // Landmark visibility
    },
    "gui": {
      "hand_window_height": 200,
      "hand_window_width": 300
    },
    "buffer_length": 20,        // Gesture stability buffer
    "speed": 40                 // Movement speed (unused)
  },
  "model_paths": {
    "pose_recogniser": "model/keypoint_classifier.tflite",
    "keypoint_classifier_labels": "model/keypoint_classifier_label.csv"
  },
  "initial_options": {
    "following": false          // Initial follow state
  }
}
```

### Performance Tuning

#### Detection Confidence
- **0.3-0.4**: Maximum detection range, more false positives
- **0.5-0.6**: Balanced performance
- **0.7-0.9**: High accuracy, may miss distant/occluded poses

#### Model Complexity
- **0**: Lite model (~3-5 FPS improvement)
- **1**: Full model (balanced)
- **2**: Heavy model (best accuracy, ~2-3 FPS slower)

#### Buffer Length Impact
- **5-10 frames**: Near instant response (0.17-0.33s @ 30fps)
- **20-30 frames**: Balanced (0.67-1s @ 30fps)
- **40-60 frames**: Very stable (1.33-2s @ 30fps)

## Error Handling

### Common Issues and Solutions

1. **No Pose Detected**
   ```python
   if results is None or not results.pose_landmarks:
       return -1  # No gesture
   ```

2. **Camera Not Available**
   ```python
   cap = cv.VideoCapture(0)
   if not cap.isOpened():
       print("Error: No se pudo abrir la cámara")
       return
   ```

3. **Model Loading Errors**
   - Check file paths in config
   - Ensure .tflite and .csv files exist
   - Verify TFLite runtime installation

## Advanced Usage

### Custom Gesture Addition

1. Collect training data:
   ```bash
   python model/add_pose.py
   # Press SPACE to record poses
   # Press 'n' for next gesture class
   ```

2. Train new model:
   - Use `model/Keypoint_model_training.ipynb`
   - Update label CSV with new gestures

3. Deploy:
   - Replace `keypoint_classifier.tflite`
   - Update `keypoint_classifier_label.csv`

### Multi-Person Support

Current implementation processes single person. For multi-person:
```python
# Modify in mp_pose.py
self.pose = self.mp_pose.Pose(
    static_image_mode=static_image_mode,
    model_complexity=model_complexity,
    smooth_landmarks=True,  # Add smoothing
    enable_segmentation=enable_segmentation,
    smooth_segmentation=True,  # Smooth masks
    min_detection_confidence=min_detection_confidence,
    min_tracking_confidence=min_tracking_confidence
)
```