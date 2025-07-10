# Pose Recognition System - API Documentation

## Table of Contents
1. [Overview](#overview)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [API Reference](#api-reference)
   - [mp_utils Module](#mp_utils-module)
   - [neural_network Module](#neural_network-module)
   - [gui Module](#gui-module)
   - [instructions Module](#instructions-module)
   - [model Module](#model-module)
5. [Configuration](#configuration)
6. [Examples](#examples)

## Overview

This pose recognition system uses MediaPipe for pose detection and a neural network for gesture classification. The system can detect human poses in real-time from a webcam feed, classify them into predefined gestures, and provide visual feedback through a GUI.

### Key Features
- Real-time pose detection using MediaPipe
- Neural network-based gesture classification
- Configurable detection parameters
- Visual feedback with pose overlays
- Gesture buffering for stable predictions
- Telegram integration for notifications

## Installation

```bash
# Install required dependencies
pip install -r requeriments.txt
```

### Dependencies
- OpenCV (cv2)
- MediaPipe
- NumPy
- TensorFlow Lite Runtime
- Requests (for Telegram integration)

## Quick Start

```python
# Run the main application
python main.py
```

Press 'q' to quit the application.

## API Reference

### mp_utils Module

#### `mp_utils.mp_pose.PoseDetection`

A class for pose detection using MediaPipe.

```python
class PoseDetection:
    def __init__(self,
                 static_image_mode=False,
                 model_complexity=1,
                 enable_segmentation=True,
                 min_detection_confidence=0.3,
                 min_tracking_confidence=0.3)
```

**Parameters:**
- `static_image_mode` (bool): Whether to treat images as static or video stream
- `model_complexity` (int): Model complexity (0, 1, or 2)
- `enable_segmentation` (bool): Enable segmentation mask
- `min_detection_confidence` (float): Minimum confidence for detection
- `min_tracking_confidence` (float): Minimum confidence for tracking

**Methods:**

##### `extract_pose(image) -> mediapipe.solutions.pose.PoseLandmarkerResult`
Extracts pose landmarks from an image.

**Example:**
```python
pose_detector = PoseDetection()
results = pose_detector.extract_pose(frame)
```

##### `draw_pose(image) -> np.ndarray`
Draws pose landmarks on the image.

**Example:**
```python
annotated_image = pose_detector.draw_pose(frame)
cv2.imshow('Pose', annotated_image)
```

##### `filter_landmarks() -> List[List[float]]`
Returns filtered landmarks for torso and limbs (indices 11-16, 23-28).

**Example:**
```python
filtered_points = pose_detector.filter_landmarks()
# Returns: [[x, y, z, visibility], ...]
```

##### `close()`
Releases MediaPipe resources.

#### `mp_utils.pose_posture.PoseDetectionPosture`

A wrapper class for pose detection with posture-specific configuration.

```python
class PoseDetectionPosture:
    def __init__(self,
                 static_image_mode=False,
                 model_complexity=1,
                 min_pose_detection_confidence=0.3,
                 min_pose_tracking_confidence=0.3)
```

Provides the same interface as `PoseDetection` with simplified initialization.

### neural_network Module

#### `neural_network.pose_recognition.PoseRecognizer`

Handles pose recognition using a TensorFlow Lite model.

```python
class PoseRecognizer:
    def __init__(self,
                 model_path='model/keypoint_classifier.tflite',
                 label_path='model/keypoint_classifier_label.csv')
```

**Parameters:**
- `model_path` (str): Path to the TFLite model
- `label_path` (str): Path to the CSV file with gesture labels

**Methods:**

##### `recognize_pose(results, debug_image) -> Tuple[int, List[str]]`
Recognizes a pose gesture from MediaPipe results.

**Returns:**
- `gesture_id` (int): ID of the recognized gesture (-1 if none)
- `labels` (List[str]): List of all available gesture labels

**Example:**
```python
recognizer = PoseRecognizer()
gesture_id, labels = recognizer.recognize_pose(pose_results, frame)
```

##### `translate_gesture_id_to_name(gesture_id) -> str`
Translates a gesture ID to its human-readable name.

**Example:**
```python
gesture_name = recognizer.translate_gesture_id_to_name(gesture_id)
print(f"Detected gesture: {gesture_name}")
```

### gui Module

#### `gui.ThirdPersonGUI`

Manages the graphical user interface for the pose recognition system.

```python
class ThirdPersonGUI:
    def __init__(self, hand_window_height, hand_window_width)
```

**Parameters:**
- `hand_window_height` (int): Height of the hand window
- `hand_window_width` (int): Width of the hand window

**Methods:**

##### `update_camera_window(camera_window_image)`
Updates the main camera window with a new frame.

**Example:**
```python
gui = ThirdPersonGUI(200, 300)
gui.update_camera_window(annotated_frame)
```

##### `update_info_window(follow_state, move, battery, gesture_name)`
Updates the information window with status data.

**Parameters:**
- `follow_state` (bool): Whether following is active
- `move` (int): Current movement value
- `battery` (int): Battery percentage (0-100)
- `gesture_name` (str): Name of the current gesture

**Example:**
```python
gui.update_info_window(True, 0, 85, "Standing")
```

##### `show_window()`
Displays all GUI windows.

##### `getKey() -> int`
Returns the key pressed by the user.

**Example:**
```python
key = gui.getKey()
if key == ord('q'):
    break
```

##### `close()`
Closes all GUI windows.

### instructions Module

#### `instructions.gesture_buffer.GestureBuffer`

Implements a buffer for gesture stabilization.

```python
class GestureBuffer:
    def __init__(self, buffer_len=2, min_consistency=0.2)
```

**Parameters:**
- `buffer_len` (int): Length of the gesture buffer
- `min_consistency` (float): Minimum consistency threshold (0-1)

**Methods:**

##### `add_gesture(gesture_id)`
Adds a gesture to the buffer.

##### `get_gesture() -> int`
Returns the most consistent gesture from the buffer.

**Example:**
```python
buffer = GestureBuffer(buffer_len=20, min_consistency=0.8)
buffer.add_gesture(gesture_id)
stable_gesture = buffer.get_gesture()
```

#### `instructions.gesture_instructions.Instructions`

Handles gesture-based instructions and notifications.

```python
class Instructions:
    def __init__(self, following, speed=40, width=1000, height=500)
```

**Parameters:**
- `following` (bool): Initial following state
- `speed` (int): Movement speed
- `width` (int): Window width
- `height` (int): Window height

**Methods:**

##### `get_follow_state() -> bool`
Returns the current following state.

##### `send_telegram_message(message)`
Sends a message via Telegram bot.

**Example:**
```python
instructions = Instructions(following=True)
instructions.send_telegram_message("Gesture detected: Waving")
```

### model Module

#### `model.add_pose.PoseLandmarkerAndResult`

Handles pose landmark detection for data collection.

```python
class PoseLandmarkerAndResult:
    def __init__(self)
```

**Methods:**

##### `detect_async(frame)`
Performs asynchronous pose detection.

##### `close()`
Closes the pose landmarker.

## Configuration

The system uses a `config_pose.json` file for configuration:

```json
{
  "constants": {
    "pose": {
      "min_pose_detection_confidence": 0.5,
      "min_pose_tracking_confidence": 0.5,
      "min_pose_presence_confidence": 0.5
    },
    "gui": {
      "hand_window_height": 200,
      "hand_window_width": 300
    },
    "buffer_length": 20,
    "speed": 40
  },
  "model_paths": {
    "pose_recogniser": "model/keypoint_classifier.tflite",
    "keypoint_classifier_labels": "model/keypoint_classifier_label.csv"
  },
  "initial_options": {
    "following": false
  }
}
```

## Examples

### Basic Pose Detection

```python
import cv2
from mp_utils.mp_pose import PoseDetection

# Initialize pose detector
detector = PoseDetection(min_detection_confidence=0.5)

# Capture from webcam
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Detect pose
    results = detector.extract_pose(frame)
    
    # Draw pose on frame
    annotated_frame = detector.draw_pose(frame)
    
    # Display
    cv2.imshow('Pose Detection', annotated_frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
detector.close()
```

### Gesture Recognition with Buffer

```python
from neural_network.pose_recognition import PoseRecognizer
from instructions.gesture_buffer import GestureBuffer
from mp_utils.pose_posture import PoseDetectionPosture

# Initialize components
detector = PoseDetectionPosture()
recognizer = PoseRecognizer()
buffer = GestureBuffer(buffer_len=20, min_consistency=0.8)

# Process frame
results = detector.extract_pose(frame)
gesture_id, _ = recognizer.recognize_pose(results, frame)

# Add to buffer for stability
buffer.add_gesture(gesture_id)
stable_gesture = buffer.get_gesture()

# Get gesture name
gesture_name = recognizer.translate_gesture_id_to_name(stable_gesture)
print(f"Detected: {gesture_name}")
```

### Complete Application Example

```python
import cv2
import json
from mp_utils.pose_posture import PoseDetectionPosture
from neural_network.pose_recognition import PoseRecognizer
from gui.gui import ThirdPersonGUI
from instructions.gesture_buffer import GestureBuffer

# Load configuration
with open('config_pose.json', 'r') as f:
    config = json.load(f)

# Initialize components
detector = PoseDetectionPosture(
    min_pose_detection_confidence=config['constants']['pose']['min_pose_detection_confidence']
)
recognizer = PoseRecognizer(
    model_path=config['model_paths']['pose_recogniser']
)
gui = ThirdPersonGUI(
    config['constants']['gui']['hand_window_height'],
    config['constants']['gui']['hand_window_width']
)
buffer = GestureBuffer(buffer_len=config['constants']['buffer_length'])

# Main loop
cap = cv2.VideoCapture(0)
while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Process pose
    results = detector.extract_pose(frame)
    annotated_frame = detector.draw_pose(frame)
    
    # Recognize gesture
    gesture_id, _ = recognizer.recognize_pose(results, frame)
    buffer.add_gesture(gesture_id)
    stable_gesture = buffer.get_gesture()
    gesture_name = recognizer.translate_gesture_id_to_name(stable_gesture)
    
    # Update GUI
    gui.update_camera_window(annotated_frame)
    gui.update_info_window(False, 0, 100, gesture_name)
    gui.show_window()
    
    if gui.getKey() == ord('q'):
        break

# Cleanup
cap.release()
detector.close()
gui.close()
```

### Adding New Poses to Dataset

```python
from model.add_pose import PoseLandmarkerAndResult
import cv2
import csv

# Initialize landmarker
landmarker = PoseLandmarkerAndResult()
cap = cv2.VideoCapture(0)

# Open CSV for writing
with open('new_poses.csv', 'a', newline='') as f:
    writer = csv.writer(f)
    
    while True:
        ret, frame = cap.read()
        frame = cv2.flip(frame, 1)  # Mirror frame
        
        # Detect pose
        landmarker.detect_async(frame)
        
        # Draw landmarks
        annotated = draw_landmarks_on_image(frame, landmarker.result)
        cv2.imshow('Pose Collection', annotated)
        
        key = cv2.waitKey(1)
        if key == ord('q'):
            break
        elif key == ord(' '):  # Space to save pose
            add_to_csv(frame, landmarker.result, writer)

landmarker.close()
cap.release()
cv2.destroyAllWindows()
```

## Best Practices

1. **Confidence Thresholds**: Adjust detection confidence based on your use case
   - Higher values (0.7-0.9) for accuracy
   - Lower values (0.3-0.5) for responsiveness

2. **Buffer Length**: Set buffer length based on gesture complexity
   - Shorter buffers (10-20) for quick gestures
   - Longer buffers (30-50) for complex poses

3. **Resource Management**: Always close detectors and release resources
   ```python
   detector.close()
   cap.release()
   cv2.destroyAllWindows()
   ```

4. **Error Handling**: Check for None results
   ```python
   if results and results.pose_landmarks:
       # Process landmarks
   ```

5. **Performance**: Use appropriate model complexity
   - 0: Lite model for mobile/embedded
   - 1: Full model for desktop
   - 2: Heavy model for best accuracy