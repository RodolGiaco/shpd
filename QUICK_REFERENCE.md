# Quick Reference Guide

## Common Code Snippets

### Basic Pose Detection
```python
from mp_utils.pose_posture import PoseDetectionPosture

detector = PoseDetectionPosture(min_pose_detection_confidence=0.5)
results = detector.extract_pose(frame)
annotated = detector.draw_pose(frame)
```

### Gesture Recognition
```python
from neural_network.pose_recognition import PoseRecognizer

recognizer = PoseRecognizer()
gesture_id, labels = recognizer.recognize_pose(results, frame)
gesture_name = recognizer.translate_gesture_id_to_name(gesture_id)
```

### GUI Update
```python
from gui.gui import ThirdPersonGUI

gui = ThirdPersonGUI(200, 300)
gui.update_camera_window(frame)
gui.update_info_window(True, 0, 100, "Standing")
gui.show_window()
```

### Gesture Buffer
```python
from instructions.gesture_buffer import GestureBuffer

buffer = GestureBuffer(buffer_len=20, min_consistency=0.8)
buffer.add_gesture(gesture_id)
stable_gesture = buffer.get_gesture()
```

## Configuration Quick Reference

### Detection Confidence Levels
| Confidence | Use Case | Performance Impact |
|------------|----------|-------------------|
| 0.3 | Maximum range, tracking partially visible poses | Low accuracy |
| 0.5 | Balanced detection and tracking | Moderate |
| 0.7 | High accuracy, clear poses only | May miss poses |
| 0.9 | Very strict, perfect poses only | Very restrictive |

### Model Complexity
| Level | Description | FPS Impact |
|-------|-------------|------------|
| 0 | Lite model | +3-5 FPS |
| 1 | Full model | Baseline |
| 2 | Heavy model | -2-3 FPS |

### Buffer Settings
| Buffer Length | Response Time (30fps) | Stability |
|--------------|----------------------|-----------|
| 5 | 0.17s | Low |
| 10 | 0.33s | Medium |
| 20 | 0.67s | High |
| 30 | 1.00s | Very High |

## MediaPipe Pose Landmarks

### Filtered Landmarks (Used by System)
```
11: Left Shoulder     12: Right Shoulder
13: Left Elbow        14: Right Elbow
15: Left Wrist        16: Right Wrist
23: Left Hip          24: Right Hip
25: Left Knee         26: Right Knee
27: Left Ankle        28: Right Ankle
```

### All 33 Pose Landmarks
```
0: Nose
1-10: Face landmarks
11-22: Upper body
23-32: Lower body
```

## Key Bindings

### Main Application (`main.py`)
- `q`: Quit application

### Data Collection (`model/add_pose.py`)
- `SPACE`: Record current pose
- `n`: Next gesture class
- `p`: Previous gesture class
- `q`: Quit

## File Formats

### Gesture Labels CSV
```csv
0,Standing
1,Waving
2,Pointing
3,Arms_Up
4,Arms_Down
```

### Training Data CSV
```csv
gesture_id,x1,y1,z1,x2,y2,z2,...,x12,y12,z12
0,0.1,0.2,0.01,0.15,0.25,0.02,...
```

## Common Issues & Solutions

### Camera Not Found
```python
cap = cv2.VideoCapture(0)  # Try 1, 2, etc. for different cameras
if not cap.isOpened():
    print("Error: Camera not found")
```

### Model Not Loading
```python
# Check file paths
import os
print(os.path.exists('model/keypoint_classifier.tflite'))
print(os.path.exists('model/keypoint_classifier_label.csv'))
```

### Low FPS
```python
# Reduce model complexity
detector = PoseDetectionPosture(model_complexity=0)

# Skip frames
if frame_count % 2 == 0:  # Process every other frame
    results = detector.extract_pose(frame)
```

### Gesture Not Detecting
```python
# Lower detection confidence
detector = PoseDetectionPosture(min_pose_detection_confidence=0.3)

# Reduce buffer consistency requirement
buffer = GestureBuffer(buffer_len=10, min_consistency=0.5)
```

## Environment Setup

### Required Packages
```bash
opencv-python>=4.5.0
mediapipe>=0.8.0
numpy>=1.19.0
tflite-runtime>=2.5.0
requests>=2.25.0
```

### Directory Structure
```
project/
├── main.py
├── config_pose.json
├── API_DOCUMENTATION.md
├── MODULE_REFERENCE.md
├── DEVELOPER_GUIDE.md
├── QUICK_REFERENCE.md
├── mp_utils/
│   ├── __init__.py
│   ├── mp_pose.py
│   └── pose_posture.py
├── neural_network/
│   ├── __init__.py
│   └── pose_recognition.py
├── gui/
│   ├── __init__.py
│   └── gui.py
├── instructions/
│   ├── __init__.py
│   ├── gesture_buffer.py
│   └── gesture_instructions.py
└── model/
    ├── keypoint_classifier.tflite
    ├── keypoint_classifier_label.csv
    ├── add_pose.py
    └── Keypoint_model_training.ipynb
```

## Performance Optimization Checklist

- [ ] Use appropriate model complexity (0 for speed, 2 for accuracy)
- [ ] Adjust detection confidence based on environment
- [ ] Implement frame skipping if needed
- [ ] Use async processing for heavy operations
- [ ] Profile with `cProfile` to find bottlenecks
- [ ] Consider GPU acceleration if available
- [ ] Optimize image resolution (640x480 often sufficient)
- [ ] Use threading for independent operations
- [ ] Cache repeated calculations
- [ ] Minimize GUI updates per frame

## Testing Checklist

- [ ] Test with different lighting conditions
- [ ] Test with various distances from camera
- [ ] Test with partial occlusions
- [ ] Verify all gestures are recognized
- [ ] Check memory usage over time
- [ ] Validate CSV data integrity
- [ ] Test error handling (no camera, missing files)
- [ ] Verify configuration loading
- [ ] Test with multiple people in frame
- [ ] Check performance on target hardware