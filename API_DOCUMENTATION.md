# Documentación de la API - Sistema de Reconocimiento de Posturas

## Tabla de Contenidos
1. [Visión General](#visión-general)
2. [Instalación](#instalación)
3. [Inicio Rápido](#inicio-rápido)
4. [Referencia de la API](#referencia-de-la-api)
   - [Módulo mp_utils](#módulo-mp_utils)
   - [Módulo neural_network](#módulo-neural_network)
   - [Módulo gui](#módulo-gui)
   - [Módulo instructions](#módulo-instructions)
   - [Módulo model](#módulo-model)
5. [Configuración](#configuración)
6. [Ejemplos de Implementación](#ejemplos-de-implementación)

## Visión General

Este sistema de reconocimiento de posturas utiliza **MediaPipe** para la detección de poses y **redes neuronales** para la clasificación de gestos. El sistema puede detectar posturas humanas en tiempo real desde una fuente de video, clasificarlas en gestos predefinidos y proporcionar retroalimentación visual mediante una interfaz gráfica de usuario.

### Características Principales
- **Detección de posturas en tiempo real** utilizando MediaPipe
- **Clasificación de gestos basada en redes neuronales**
- **Parámetros de detección configurables**
- **Retroalimentación visual** con superposición de poses
- **Buffer de gestos** para predicciones estables
- **Integración con Telegram** para notificaciones

## Instalación

```bash
# Instalar dependencias requeridas
pip install -r requirements.txt
```

### Dependencias
- OpenCV (cv2)
- MediaPipe
- NumPy
- TensorFlow Lite Runtime
- Requests (para integración con Telegram)

## Inicio Rápido

```python
# Ejecutar la aplicación principal
python main.py
```

Presionar 'q' para salir de la aplicación.

## Referencia de la API

### Módulo mp_utils

#### `mp_utils.mp_pose.PoseDetection`

Clase para la detección de posturas utilizando MediaPipe.

```python
class PoseDetection:
    def __init__(self,
                 static_image_mode=False,
                 model_complexity=1,
                 enable_segmentation=True,
                 min_detection_confidence=0.3,
                 min_tracking_confidence=0.3)
```

**Parámetros:**
- `static_image_mode` (bool): Si tratar las imágenes como estáticas o flujo de video
- `model_complexity` (int): Complejidad del modelo (0, 1, o 2)
- `enable_segmentation` (bool): Habilitar máscara de segmentación
- `min_detection_confidence` (float): Confianza mínima para detección
- `min_tracking_confidence` (float): Confianza mínima para seguimiento

**Métodos:**

##### `extract_pose(image) -> mediapipe.solutions.pose.PoseLandmarkerResult`
Extrae los puntos clave de postura de una imagen.

**Ejemplo:**
```python
pose_detector = PoseDetection()
results = pose_detector.extract_pose(frame)
```

##### `draw_pose(image) -> np.ndarray`
Dibuja los puntos clave de postura sobre la imagen.

**Ejemplo:**
```python
annotated_image = pose_detector.draw_pose(frame)
cv2.imshow('Pose', annotated_image)
```

##### `filter_landmarks() -> List[List[float]]`
Retorna puntos clave filtrados para torso y extremidades (índices 11-16, 23-28).

**Ejemplo:**
```python
filtered_points = pose_detector.filter_landmarks()
# Retorna: [[x, y, z, visibility], ...]
```

##### `close()`
Libera los recursos de MediaPipe.

#### `mp_utils.pose_posture.PoseDetectionPosture`

Clase wrapper para detección de posturas con configuración específica.

```python
class PoseDetectionPosture:
    def __init__(self,
                 static_image_mode=False,
                 model_complexity=1,
                 min_pose_detection_confidence=0.3,
                 min_pose_tracking_confidence=0.3)
```

Proporciona la misma interfaz que `PoseDetection` con inicialización simplificada.

### Módulo neural_network

#### `neural_network.pose_recognition.PoseRecognizer`

Maneja el reconocimiento de posturas utilizando un modelo TensorFlow Lite.

```python
class PoseRecognizer:
    def __init__(self,
                 model_path='model/keypoint_classifier.tflite',
                 label_path='model/keypoint_classifier_label.csv')
```

**Parámetros:**
- `model_path` (str): Ruta al modelo TFLite
- `label_path` (str): Ruta al archivo CSV con etiquetas de gestos

**Métodos:**

##### `recognize_pose(results, debug_image) -> Tuple[int, List[str]]`
Reconoce un gesto de postura a partir de resultados de MediaPipe.

**Retorna:**
- `gesture_id` (int): ID del gesto reconocido (-1 si ninguno)
- `labels` (List[str]): Lista de todas las etiquetas de gestos disponibles

**Ejemplo:**
```python
recognizer = PoseRecognizer()
gesture_id, labels = recognizer.recognize_pose(pose_results, frame)
```

##### `translate_gesture_id_to_name(gesture_id) -> str`
Traduce un ID de gesto a su nombre legible.

**Ejemplo:**
```python
gesture_name = recognizer.translate_gesture_id_to_name(gesture_id)
print(f"Gesto detectado: {gesture_name}")
```

### Módulo gui

#### `gui.ThirdPersonGUI`

Administra la interfaz gráfica de usuario para el sistema de reconocimiento de posturas.

```python
class ThirdPersonGUI:
    def __init__(self, hand_window_height, hand_window_width)
```

**Parámetros:**
- `hand_window_height` (int): Altura de la ventana de mano
- `hand_window_width` (int): Ancho de la ventana de mano

**Métodos:**

##### `update_camera_window(camera_window_image)`
Actualiza la ventana principal de la cámara con un nuevo frame.

**Ejemplo:**
```python
gui = ThirdPersonGUI(200, 300)
gui.update_camera_window(annotated_frame)
```

##### `update_info_window(follow_state, move, battery, gesture_name)`
Actualiza la ventana de información con datos de estado.

**Parámetros:**
- `follow_state` (bool): Si el seguimiento está activo
- `move` (int): Valor de movimiento actual
- `battery` (int): Porcentaje de batería (0-100)
- `gesture_name` (str): Nombre del gesto actual

**Ejemplo:**
```python
gui.update_info_window(True, 0, 85, "De pie")
```

##### `show_window()`
Muestra todas las ventanas de GUI.

##### `getKey() -> int`
Retorna la tecla presionada por el usuario.

**Ejemplo:**
```python
key = gui.getKey()
if key == ord('q'):
    break
```

##### `close()`
Cierra todas las ventanas de GUI.

### Módulo instructions

#### `instructions.gesture_buffer.GestureBuffer`

Implementa un buffer para estabilización de gestos.

```python
class GestureBuffer:
    def __init__(self, buffer_len=2, min_consistency=0.2)
```

**Parámetros:**
- `buffer_len` (int): Longitud del buffer de gestos
- `min_consistency` (float): Umbral mínimo de consistencia (0-1)

**Métodos:**

##### `add_gesture(gesture_id)`
Añade un gesto al buffer.

##### `get_gesture() -> int`
Retorna el gesto más consistente del buffer.

**Ejemplo:**
```python
buffer = GestureBuffer(buffer_len=20, min_consistency=0.8)
buffer.add_gesture(gesture_id)
stable_gesture = buffer.get_gesture()
```

#### `instructions.gesture_instructions.Instructions`

Maneja instrucciones basadas en gestos y notificaciones.

```python
class Instructions:
    def __init__(self, following, speed=40, width=1000, height=500)
```

**Parámetros:**
- `following` (bool): Estado inicial de seguimiento
- `speed` (int): Velocidad de movimiento
- `width` (int): Ancho de ventana
- `height` (int): Alto de ventana

**Métodos:**

##### `get_follow_state() -> bool`
Retorna el estado actual de seguimiento.

##### `send_telegram_message(message)`
Envía un mensaje vía bot de Telegram.

**Ejemplo:**
```python
instructions = Instructions(following=True)
instructions.send_telegram_message("Gesto detectado: Saludando")
```

### Módulo model

#### `model.add_pose.PoseLandmarkerAndResult`

Maneja la detección de puntos clave de postura para recolección de datos.

```python
class PoseLandmarkerAndResult:
    def __init__(self)
```

**Métodos:**

##### `detect_async(frame)`
Realiza detección de postura asíncrona.

##### `close()`
Cierra el detector de puntos clave.

## Configuración

El sistema utiliza un archivo `config_pose.json` para configuración:

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

## Ejemplos de Implementación

### Detección Básica de Posturas

```python
import cv2
from mp_utils.mp_pose import PoseDetection

# Inicializar detector de posturas
detector = PoseDetection(min_detection_confidence=0.5)

# Capturar desde webcam
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Detectar postura
    results = detector.extract_pose(frame)
    
    # Dibujar postura en frame
    annotated_frame = detector.draw_pose(frame)
    
    # Mostrar
    cv2.imshow('Detección de Postura', annotated_frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
detector.close()
```

### Reconocimiento de Gestos con Buffer

```python
from neural_network.pose_recognition import PoseRecognizer
from instructions.gesture_buffer import GestureBuffer
from mp_utils.pose_posture import PoseDetectionPosture

# Inicializar componentes
detector = PoseDetectionPosture()
recognizer = PoseRecognizer()
buffer = GestureBuffer(buffer_len=20, min_consistency=0.8)

# Procesar frame
results = detector.extract_pose(frame)
gesture_id, _ = recognizer.recognize_pose(results, frame)

# Añadir al buffer para estabilidad
buffer.add_gesture(gesture_id)
stable_gesture = buffer.get_gesture()

# Obtener nombre del gesto
gesture_name = recognizer.translate_gesture_id_to_name(stable_gesture)
print(f"Detectado: {gesture_name}")
```

### Aplicación Completa de Ejemplo

```python
import cv2
import json
from mp_utils.pose_posture import PoseDetectionPosture
from neural_network.pose_recognition import PoseRecognizer
from gui.gui import ThirdPersonGUI
from instructions.gesture_buffer import GestureBuffer

# Cargar configuración
with open('config_pose.json', 'r') as f:
    config = json.load(f)

# Inicializar componentes
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

# Bucle principal
cap = cv2.VideoCapture(0)
while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Procesar postura
    results = detector.extract_pose(frame)
    annotated_frame = detector.draw_pose(frame)
    
    # Reconocer gesto
    gesture_id, _ = recognizer.recognize_pose(results, frame)
    buffer.add_gesture(gesture_id)
    stable_gesture = buffer.get_gesture()
    gesture_name = recognizer.translate_gesture_id_to_name(stable_gesture)
    
    # Actualizar GUI
    gui.update_camera_window(annotated_frame)
    gui.update_info_window(False, 0, 100, gesture_name)
    gui.show_window()
    
    if gui.getKey() == ord('q'):
        break

# Limpieza
cap.release()
detector.close()
gui.close()
```

### Añadir Nuevas Posturas al Dataset

```python
from model.add_pose import PoseLandmarkerAndResult
import cv2
import csv

# Inicializar detector de puntos clave
landmarker = PoseLandmarkerAndResult()
cap = cv2.VideoCapture(0)

# Abrir CSV para escritura
with open('new_poses.csv', 'a', newline='') as f:
    writer = csv.writer(f)
    
    while True:
        ret, frame = cap.read()
        frame = cv2.flip(frame, 1)  # Espejo del frame
        
        # Detectar postura
        landmarker.detect_async(frame)
        
        # Dibujar puntos clave
        annotated = draw_landmarks_on_image(frame, landmarker.result)
        cv2.imshow('Recolección de Posturas', annotated)
        
        key = cv2.waitKey(1)
        if key == ord('q'):
            break
        elif key == ord(' '):  # Espacio para guardar postura
            add_to_csv(frame, landmarker.result, writer)

landmarker.close()
cap.release()
cv2.destroyAllWindows()
```

## Mejores Prácticas

1. **Umbrales de Confianza**: Ajustar la confianza de detección según el caso de uso
   - Valores altos (0.7-0.9) para precisión
   - Valores bajos (0.3-0.5) para capacidad de respuesta

2. **Longitud del Buffer**: Establecer longitud del buffer según complejidad del gesto
   - Buffers cortos (10-20) para gestos rápidos
   - Buffers largos (30-50) para poses complejas

3. **Gestión de Recursos**: Siempre cerrar detectores y liberar recursos
   ```python
   detector.close()
   cap.release()
   cv2.destroyAllWindows()
   ```

4. **Manejo de Errores**: Verificar resultados None
   ```python
   if results and results.pose_landmarks:
       # Procesar puntos clave
   ```

5. **Rendimiento**: Usar complejidad de modelo apropiada
   - 0: Modelo lite para móvil/embebido
   - 1: Modelo completo para escritorio
   - 2: Modelo pesado para mejor precisión