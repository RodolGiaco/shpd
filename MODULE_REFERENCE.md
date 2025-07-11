# Documentación de Referencia de Módulos

## Módulo mp_utils

### Descripción General
El módulo `mp_utils` proporciona utilidades para la detección de posturas utilizando MediaPipe. Contiene dos componentes principales:
- `mp_pose.py`: Funcionalidad de detección de poses
- `pose_posture.py`: Wrapper especializado para detección de posturas

### mp_pose.PoseDetection

#### Descripción de la Clase
```python
mp_utils.mp_pose.PoseDetection(
    static_image_mode=False,
    model_complexity=1,
    enable_segmentation=True,
    min_detection_confidence=0.3,
    min_tracking_confidence=0.3
)
```

#### Documentación Detallada de Métodos

##### `extract_pose(image: np.ndarray) -> mediapipe.python.solution_base.SolutionOutputs`

Procesa una imagen para extraer puntos clave de postura.

**Parámetros:**
- `image`: Imagen BGR como array de numpy

**Retorna:**
- Resultados de pose de MediaPipe que contienen:
  - `pose_landmarks`: 33 puntos clave de postura en coordenadas de imagen
  - `pose_world_landmarks`: 33 puntos clave de postura en coordenadas mundiales
  - `segmentation_mask`: Máscara binaria de la persona (si está habilitada)

**Ejemplo:**
```python
import cv2
from mp_utils.mp_pose import PoseDetection

detector = PoseDetection()
image = cv2.imread('persona.jpg')
results = detector.extract_pose(image)

if results.pose_landmarks:
    for idx, landmark in enumerate(results.pose_landmarks.landmark):
        print(f"Punto clave {idx}: x={landmark.x}, y={landmark.y}, z={landmark.z}")
```

##### `filter_landmarks() -> List[List[float]]`

Filtra y retorna únicamente los puntos clave del torso y extremidades.

**Puntos clave incluidos:**
- 11-16: Parte superior del cuerpo (hombros, codos, muñecas)
- 23-28: Parte inferior del cuerpo (caderas, rodillas, tobillos)

**Retorna:**
```python
[
    [x, y, z, visibility],  # Punto clave 11
    [x, y, z, visibility],  # Punto clave 12
    # ... etc
]
```

## Módulo neural_network

### pose_recognition.PoseRecognizer

#### Descripción de la Clase
Implementa el reconocimiento de gestos posturales utilizando TensorFlow Lite.

#### Pipeline de Procesamiento Interno

1. **Cálculo de puntos clave** (`calc_landmark_list`):
   - Convierte puntos clave normalizados a coordenadas de píxel
   - Filtra para incluir únicamente partes específicas del cuerpo
   - Incluye coordenada Z para información de profundidad

2. **Preprocesamiento** (`pre_process_landmark`):
   - Convierte a coordenadas relativas (primer punto como origen)
   - Aplana coordenadas 3D a array 1D
   - Normaliza por valor absoluto máximo

3. **Clasificación**:
   - Alimenta puntos clave preprocesados al modelo TFLite
   - Retorna ID de gesto con mayor confianza

#### Gestión de Etiquetas de Gestos

El sistema utiliza un archivo CSV para mapear IDs de gestos a nombres:
```csv
0,De pie
1,Saludando
2,Señalando
3,Brazos arriba
4,Brazos abajo
```

## Módulo gui

### ThirdPersonGUI

#### Gestión de Ventanas

La GUI administra tres ventanas separadas de OpenCV:

1. **Ventana de Cámara** (`ThirdPerson`):
   - Vista principal mostrando superposición de pose
   - Feed de cámara completo con puntos clave

2. **Ventana de Información** (`Info`):
   - Visualización de información de estado
   - Muestra: Estado de seguimiento, Movimiento, Batería, Gesto

3. **Ventana de Mano** (`hand`):
   - Vista detallada opcional de manos
   - Actualmente deshabilitada en main.py

#### Sistema de Superposición

El método `overlay_text_on_rect` crea superposiciones de información:
```python
def overlay_text_on_rect(self, frame, text, rect_position, text_position, 
                         font_scale=1, color=(255, 255, 255), thickness=2)
```

Crea un fondo rectangular negro con texto blanco para mejor visibilidad.

## Módulo instructions

### gesture_buffer.GestureBuffer

#### Algoritmo del Buffer

Implementa un buffer circular con verificación de consistencia:

```python
# Flujo interno:
1. Añadir gesto al deque (tamaño fijo)
2. Cuando esté lleno, contar gesto más común
3. Si conteo >= min_consistency * buffer_len:
   - Limpiar buffer
   - Retornar gesto
4. Si no, retornar último gesto válido
```

#### Casos de Uso
- **Alta consistencia (0.8-0.9)**: Requiere pose muy estable
- **Baja consistencia (0.2-0.5)**: Más responsivo, menos estable

### gesture_instructions.Instructions

#### Integración con Telegram

Envía notificaciones vía API Bot de Telegram:
```python
def send_telegram_message(self, message):
    url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
    data = {"chat_id": self.chat_id, "text": message}
    response = requests.post(url, data=data)
```

**Nota de Seguridad**: Token y chat ID deberían moverse al archivo de configuración.

## Módulo model

### add_pose.py Utilidades

#### Funciones de Recolección de Datos

##### `add_to_csv(image, results, writer)`
Procesa y guarda datos de pose para entrenamiento:
1. Filtra puntos clave a articulaciones relevantes
2. Calcula coordenadas de píxel
3. Normaliza relativo al primer punto clave
4. Escribe como fila CSV: `[gesture_id, x1, y1, z1, x2, y2, z2, ...]`

##### `validar_csv(csv_path)`
Valida integridad de datos de entrenamiento:
- Verifica 37 columnas (1 etiqueta + 12 puntos clave * 3 coordenadas)
- Advierte si todos los valores Z son 0
- Reporta filas malformadas

#### Visualización Personalizada de Puntos Clave

Proporciona visualización alternativa sin puntos clave faciales:
```python
POSE_CONNECTIONS_WITHOUT_FACE = [
    (11, 12), (12, 14), (14, 16),  # Brazo derecho
    (11, 13), (13, 15), (15, 17),  # Brazo izquierdo
    (23, 24), (24, 26), (26, 28),  # Pierna derecha
    (23, 25), (25, 27), (27, 29),  # Pierna izquierda
    (11, 23), (12, 24), (23, 24),  # Torso
]
```

## Detalles de Configuración

### Estructura de config_pose.json

```json
{
  "constants": {
    "pose": {
      "min_pose_detection_confidence": 0.5,  // Umbral de detección inicial
      "min_pose_tracking_confidence": 0.5,   // Seguimiento frame a frame
      "min_pose_presence_confidence": 0.5    // Visibilidad de puntos clave
    },
    "gui": {
      "hand_window_height": 200,
      "hand_window_width": 300
    },
    "buffer_length": 20,        // Buffer de estabilidad de gestos
    "speed": 40                 // Velocidad de movimiento (sin usar)
  },
  "model_paths": {
    "pose_recogniser": "model/keypoint_classifier.tflite",
    "keypoint_classifier_labels": "model/keypoint_classifier_label.csv"
  },
  "initial_options": {
    "following": false          // Estado inicial de seguimiento
  }
}
```

### Ajuste de Rendimiento

#### Confianza de Detección
- **0.3-0.4**: Rango máximo de detección, más falsos positivos
- **0.5-0.6**: Rendimiento balanceado
- **0.7-0.9**: Alta precisión, puede perder poses distantes/ocluidas

#### Complejidad del Modelo
- **0**: Modelo lite (~3-5 FPS de mejora)
- **1**: Modelo completo (balanceado)
- **2**: Modelo pesado (mejor precisión, ~2-3 FPS más lento)

#### Impacto de Longitud del Buffer
- **5-10 frames**: Respuesta casi instantánea (0.17-0.33s @ 30fps)
- **20-30 frames**: Balanceado (0.67-1s @ 30fps)
- **40-60 frames**: Muy estable (1.33-2s @ 30fps)

## Manejo de Errores

### Problemas Comunes y Soluciones

1. **No se Detecta Pose**
   ```python
   if results is None or not results.pose_landmarks:
       return -1  # Sin gesto
   ```

2. **Cámara No Disponible**
   ```python
   cap = cv.VideoCapture(0)
   if not cap.isOpened():
       print("Error: No se pudo abrir la cámara")
       return
   ```

3. **Errores de Carga del Modelo**
   - Verificar rutas de archivos en configuración
   - Asegurar que archivos .tflite y .csv existan
   - Verificar instalación de TFLite runtime

## Uso Avanzado

### Adición de Gestos Personalizados

1. Recolectar datos de entrenamiento:
   ```bash
   python model/add_pose.py
   # Presionar SPACE para grabar poses
   # Presionar 'n' para siguiente clase de gesto
   ```

2. Entrenar nuevo modelo:
   - Usar `model/Keypoint_model_training.ipynb`
   - Actualizar CSV de etiquetas con nuevos gestos

3. Implementar:
   - Reemplazar `keypoint_classifier.tflite`
   - Actualizar `keypoint_classifier_label.csv`

### Soporte Multi-Persona

La implementación actual procesa una sola persona. Para multi-persona:
```python
# Modificar en mp_pose.py
self.pose = self.mp_pose.Pose(
    static_image_mode=static_image_mode,
    model_complexity=model_complexity,
    smooth_landmarks=True,  # Añadir suavizado
    enable_segmentation=enable_segmentation,
    smooth_segmentation=True,  # Suavizar máscaras
    min_detection_confidence=min_detection_confidence,
    min_tracking_confidence=min_tracking_confidence
)
```

### Optimizaciones de Rendimiento

#### Técnicas de Optimización de Memoria
```python
# Configurar límites de memoria GPU (si aplica)
import os
os.environ['TF_FORCE_GPU_ALLOW_GROWTH'] = 'true'

# Usar procesamiento por lotes para múltiples frames
def process_batch(frames):
    results = []
    for frame in frames:
        result = detector.extract_pose(frame)
        results.append(result)
    return results
```

#### Implementación de Pool de Threads
```python
import concurrent.futures
import threading

class ThreadedPoseProcessor:
    def __init__(self, num_threads=4):
        self.num_threads = num_threads
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=num_threads)
    
    def process_frames_parallel(self, frames):
        futures = []
        for frame in frames:
            future = self.executor.submit(self.detector.extract_pose, frame)
            futures.append(future)
        
        results = []
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
        return results
```

### Métricas de Evaluación

#### Análisis de Rendimiento en Tiempo Real
```python
import time
from collections import deque

class PerformanceMonitor:
    def __init__(self, window_size=100):
        self.frame_times = deque(maxlen=window_size)
        self.processing_times = deque(maxlen=window_size)
    
    def update(self, frame_time, processing_time):
        self.frame_times.append(frame_time)
        self.processing_times.append(processing_time)
    
    def get_fps(self):
        if len(self.frame_times) < 2:
            return 0
        total_time = sum(self.frame_times)
        return len(self.frame_times) / total_time
    
    def get_avg_processing_time(self):
        return sum(self.processing_times) / len(self.processing_times)
```

#### Validación de Calidad de Datos
```python
def validate_pose_quality(landmarks, min_visibility=0.5):
    """Valida la calidad de los puntos clave detectados"""
    if not landmarks:
        return False
    
    visible_count = 0
    total_count = len(landmarks)
    
    for landmark in landmarks:
        if landmark.visibility > min_visibility:
            visible_count += 1
    
    visibility_ratio = visible_count / total_count
    return visibility_ratio > 0.7  # 70% de puntos deben ser visibles
```