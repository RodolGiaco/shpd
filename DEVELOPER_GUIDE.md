# Developer Guide - Pose Recognition System

## Architecture Overview

```
┌─────────────────┐
│   main.py       │ ← Entry point
└────────┬────────┘
         │
    ┌────┴─────────────────────────────┐
    │                                  │
┌───▼────────┐  ┌──────────────┐  ┌───▼──────┐
│ mp_utils   │  │neural_network│  │   gui    │
│            │  │              │  │          │
│-PoseDetect │  │-PoseRecogniz│  │-ThirdPers│
│-PosePosture│  │-KeyPointClas│  │   onGUI  │
└────────────┘  └──────────────┘  └──────────┘
                        │
                 ┌──────▼─────┐
                 │instructions│
                 │            │
                 │-GestureBuff│
                 │-Instructions│
                 └────────────┘
```

## System Flow

1. **Frame Capture**: Camera captures video frames
2. **Pose Detection**: MediaPipe extracts 33 pose landmarks
3. **Landmark Filtering**: System filters to 12 key joints
4. **Preprocessing**: Landmarks normalized and flattened
5. **Classification**: TFLite model predicts gesture
6. **Buffering**: Gesture buffer ensures stability
7. **Display**: GUI shows results and status

## Extending the System

### Adding New Gestures

#### Step 1: Data Collection
```python
# Run the data collection script
python model/add_pose.py

# Controls:
# SPACE - Record current pose
# 'n' - Next gesture class (increment NUMBER)
# 'p' - Previous gesture class
# 'q' - Quit
```

#### Step 2: Update Labels
Edit `model/keypoint_classifier_label.csv`:
```csv
0,Standing
1,Waving
2,Pointing
3,Arms_Up
4,Arms_Down
5,Your_New_Gesture
```

#### Step 3: Train Model
Use the Jupyter notebook `model/Keypoint_model_training.ipynb`:
```python
# Key sections to modify:
NUM_CLASSES = 6  # Update based on your gestures
EPOCHS = 100     # Adjust based on dataset size

# The notebook will:
# 1. Load pose data from CSV
# 2. Split into train/test sets
# 3. Build and train neural network
# 4. Export to TFLite format
```

#### Step 4: Deploy
Replace model files:
```bash
cp new_model.tflite model/keypoint_classifier.tflite
```

### Creating Custom Pose Filters

Create a new filter in `mp_utils/custom_filters.py`:
```python
class CustomPoseFilter:
    # Define which landmarks to include
    UPPER_BODY_LANDMARKS = [11, 12, 13, 14, 15, 16]
    LOWER_BODY_LANDMARKS = [23, 24, 25, 26, 27, 28]
    HANDS_LANDMARKS = [15, 16, 17, 18, 19, 20, 21, 22]
    
    @staticmethod
    def filter_upper_body(landmarks):
        """Returns only upper body landmarks"""
        return [landmarks[i] for i in CustomPoseFilter.UPPER_BODY_LANDMARKS
                if i < len(landmarks)]
    
    @staticmethod
    def filter_for_sitting(landmarks):
        """Optimized landmarks for sitting pose detection"""
        # Include hips, shoulders, and head
        sitting_landmarks = [0, 11, 12, 23, 24]
        return [landmarks[i] for i in sitting_landmarks
                if i < len(landmarks)]
```

### Implementing Custom Gesture Logic

Create action handlers in `instructions/gesture_actions.py`:
```python
from enum import Enum

class GestureAction(Enum):
    NONE = 0
    START_RECORDING = 1
    STOP_RECORDING = 2
    TAKE_PHOTO = 3
    EMERGENCY_STOP = 4

class GestureActionHandler:
    def __init__(self):
        self.action_map = {
            "Waving": GestureAction.START_RECORDING,
            "Stop": GestureAction.STOP_RECORDING,
            "Peace": GestureAction.TAKE_PHOTO,
            "X_Pose": GestureAction.EMERGENCY_STOP
        }
        self.action_callbacks = {}
    
    def register_callback(self, action: GestureAction, callback):
        """Register a callback for a specific action"""
        self.action_callbacks[action] = callback
    
    def process_gesture(self, gesture_name: str):
        """Process gesture and trigger associated action"""
        action = self.action_map.get(gesture_name, GestureAction.NONE)
        
        if action in self.action_callbacks:
            self.action_callbacks[action]()
            return True
        return False

# Usage example:
handler = GestureActionHandler()
handler.register_callback(
    GestureAction.TAKE_PHOTO,
    lambda: cv2.imwrite(f"photo_{time.time()}.jpg", frame)
)
```

### Custom Visualization

Create enhanced visualizations in `gui/visualizations.py`:
```python
import cv2
import numpy as np

class PoseVisualizer:
    @staticmethod
    def draw_skeleton_3d(image, landmarks, connections):
        """Draw 3D skeleton with depth visualization"""
        height, width = image.shape[:2]
        
        # Convert normalized coordinates to pixel coordinates
        points = []
        for lm in landmarks:
            x = int(lm.x * width)
            y = int(lm.y * height)
            z = lm.z * 100  # Scale Z for visibility
            points.append((x, y, z))
        
        # Draw connections with thickness based on depth
        for connection in connections:
            if connection[0] < len(points) and connection[1] < len(points):
                pt1 = points[connection[0]]
                pt2 = points[connection[1]]
                
                # Calculate thickness based on average Z
                avg_z = (pt1[2] + pt2[2]) / 2
                thickness = int(5 - avg_z * 0.02)  # Closer = thicker
                thickness = max(1, min(thickness, 10))
                
                # Color based on depth (red=close, blue=far)
                color_intensity = int(255 * (1 - avg_z / 200))
                color = (color_intensity, 0, 255 - color_intensity)
                
                cv2.line(image, (pt1[0], pt1[1]), 
                        (pt2[0], pt2[1]), color, thickness)
        
        return image
    
    @staticmethod
    def draw_gesture_trail(image, gesture_history, position):
        """Draw a trail showing gesture history"""
        trail_length = min(len(gesture_history), 10)
        
        for i in range(trail_length):
            alpha = (i + 1) / trail_length
            y_offset = position[1] - (trail_length - i) * 20
            
            cv2.putText(image, gesture_history[-(i+1)],
                       (position[0], y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX,
                       0.5, (255, 255, 255),
                       int(2 * alpha))
        
        return image
```

### Performance Optimization

#### 1. Async Processing
```python
import threading
import queue

class AsyncPoseProcessor:
    def __init__(self, detector, recognizer):
        self.detector = detector
        self.recognizer = recognizer
        self.frame_queue = queue.Queue(maxsize=5)
        self.result_queue = queue.Queue(maxsize=5)
        self.processing_thread = threading.Thread(target=self._process_frames)
        self.processing_thread.daemon = True
        self.running = True
        
    def start(self):
        self.processing_thread.start()
    
    def _process_frames(self):
        while self.running:
            try:
                frame = self.frame_queue.get(timeout=0.1)
                results = self.detector.extract_pose(frame)
                gesture_id, _ = self.recognizer.recognize_pose(results, frame)
                self.result_queue.put((results, gesture_id))
            except queue.Empty:
                continue
    
    def process_frame_async(self, frame):
        if not self.frame_queue.full():
            self.frame_queue.put(frame)
    
    def get_result(self):
        try:
            return self.result_queue.get_nowait()
        except queue.Empty:
            return None, None
```

#### 2. Frame Skipping
```python
class FrameSkipper:
    def __init__(self, skip_frames=2):
        self.skip_frames = skip_frames
        self.frame_count = 0
    
    def should_process(self):
        self.frame_count += 1
        return self.frame_count % (self.skip_frames + 1) == 0
```

### Testing

#### Unit Tests
Create `tests/test_pose_recognition.py`:
```python
import unittest
import numpy as np
from mp_utils.mp_pose import PoseDetection
from neural_network.pose_recognition import PoseRecognizer

class TestPoseRecognition(unittest.TestCase):
    def setUp(self):
        self.detector = PoseDetection()
        self.recognizer = PoseRecognizer()
    
    def test_pose_detection_with_blank_image(self):
        # Test with blank image
        blank_image = np.zeros((480, 640, 3), dtype=np.uint8)
        results = self.detector.extract_pose(blank_image)
        self.assertIsNotNone(results)
        self.assertIsNone(results.pose_landmarks)
    
    def test_landmark_filtering(self):
        # Create mock landmarks
        mock_landmarks = [MockLandmark(i*0.1, i*0.1, i*0.01, 1.0) 
                         for i in range(33)]
        
        # Test filtering
        self.detector.results = MockResults(mock_landmarks)
        filtered = self.detector.filter_landmarks()
        
        # Should return 12 landmarks (indices 11-16, 23-28)
        self.assertEqual(len(filtered), 12)
    
    def test_gesture_buffer_consistency(self):
        from instructions.gesture_buffer import GestureBuffer
        
        buffer = GestureBuffer(buffer_len=5, min_consistency=0.6)
        
        # Add mostly gesture 1
        for _ in range(3):
            buffer.add_gesture(1)
        buffer.add_gesture(2)
        buffer.add_gesture(1)
        
        # Should return 1 (appears 4/5 times = 80%)
        self.assertEqual(buffer.get_gesture(), 1)

class MockLandmark:
    def __init__(self, x, y, z, visibility):
        self.x = x
        self.y = y
        self.z = z
        self.visibility = visibility

class MockResults:
    def __init__(self, landmarks):
        self.pose_landmarks = MockPoseLandmarks(landmarks)

class MockPoseLandmarks:
    def __init__(self, landmarks):
        self.landmark = landmarks

if __name__ == '__main__':
    unittest.main()
```

### Debugging

#### Enable Debug Logging
```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pose_recognition.log'),
        logging.StreamHandler()
    ]
)

# Add to your classes
class PoseDetectionDebug(PoseDetection):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
    
    def extract_pose(self, image):
        self.logger.debug(f"Processing image shape: {image.shape}")
        results = super().extract_pose(image)
        
        if results and results.pose_landmarks:
            self.logger.info(f"Detected {len(results.pose_landmarks.landmark)} landmarks")
        else:
            self.logger.warning("No landmarks detected")
        
        return results
```

#### Visualization Tools
```python
def debug_draw_landmarks(image, landmarks, title="Debug"):
    """Draw all landmarks with indices for debugging"""
    debug_image = image.copy()
    height, width = image.shape[:2]
    
    for idx, landmark in enumerate(landmarks):
        x = int(landmark.x * width)
        y = int(landmark.y * height)
        
        # Draw circle
        cv2.circle(debug_image, (x, y), 5, (0, 255, 0), -1)
        
        # Draw index
        cv2.putText(debug_image, str(idx), (x+5, y-5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
    
    cv2.imshow(title, debug_image)
    return debug_image
```

## Deployment

### Docker Support
Create `Dockerfile`:
```dockerfile
FROM python:3.8-slim

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    wget

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

### Configuration Management
```python
import os
from pathlib import Path

class ConfigManager:
    def __init__(self, config_path="config_pose.json"):
        self.config_path = Path(config_path)
        self.config = self.load_config()
    
    def load_config(self):
        """Load config with environment variable overrides"""
        with open(self.config_path, 'r') as f:
            config = json.load(f)
        
        # Override with environment variables
        if os.getenv('POSE_DETECTION_CONFIDENCE'):
            config['constants']['pose']['min_pose_detection_confidence'] = \
                float(os.getenv('POSE_DETECTION_CONFIDENCE'))
        
        if os.getenv('BUFFER_LENGTH'):
            config['constants']['buffer_length'] = \
                int(os.getenv('BUFFER_LENGTH'))
        
        return config
    
    def get(self, key_path, default=None):
        """Get config value by dot notation path"""
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
```

## Contributing Guidelines

1. **Code Style**: Follow PEP 8
2. **Documentation**: Update docstrings for all public methods
3. **Testing**: Add unit tests for new features
4. **Performance**: Profile changes that might impact FPS
5. **Backwards Compatibility**: Maintain config file compatibility