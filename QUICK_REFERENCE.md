# Guía de Referencia Rápida

## Fragmentos de Código Comunes

### Detección Básica de Poses
```python
from mp_utils.pose_posture import PoseDetectionPosture

detector = PoseDetectionPosture(min_pose_detection_confidence=0.5)
results = detector.extract_pose(frame)
annotated = detector.draw_pose(frame)
```

### Reconocimiento de Gestos
```python
from neural_network.pose_recognition import PoseRecognizer

recognizer = PoseRecognizer()
gesture_id, labels = recognizer.recognize_pose(results, frame)
gesture_name = recognizer.translate_gesture_id_to_name(gesture_id)
```

### Actualización de GUI
```python
from gui.gui import ThirdPersonGUI

gui = ThirdPersonGUI(200, 300)
gui.update_camera_window(frame)
gui.update_info_window(True, 0, 100, "De pie")
gui.show_window()
```

### Buffer de Gestos
```python
from instructions.gesture_buffer import GestureBuffer

buffer = GestureBuffer(buffer_len=20, min_consistency=0.8)
buffer.add_gesture(gesture_id)
stable_gesture = buffer.get_gesture()
```

## Referencia Rápida de Configuración

### Niveles de Confianza de Detección
| Confianza | Caso de Uso | Impacto en Rendimiento |
|-----------|-------------|------------------------|
| 0.3 | Rango máximo, seguimiento de poses parcialmente visibles | Baja precisión |
| 0.5 | Detección y seguimiento balanceado | Moderado |
| 0.7 | Alta precisión, solo poses claras | Puede perder poses |
| 0.9 | Muy estricto, poses perfectas únicamente | Muy restrictivo |

### Complejidad del Modelo
| Nivel | Descripción | Impacto en FPS |
|-------|-------------|----------------|
| 0 | Modelo lite | +3-5 FPS |
| 1 | Modelo completo | Línea base |
| 2 | Modelo pesado | -2-3 FPS |

### Configuraciones del Buffer
| Longitud del Buffer | Tiempo de Respuesta (30fps) | Estabilidad |
|-------------------|---------------------------|-------------|
| 5 | 0.17s | Baja |
| 10 | 0.33s | Media |
| 20 | 0.67s | Alta |
| 30 | 1.00s | Muy Alta |

## Puntos Clave de MediaPipe Pose

### Puntos Clave Filtrados (Utilizados por el Sistema)
```
11: Hombro Izquierdo     12: Hombro Derecho
13: Codo Izquierdo       14: Codo Derecho
15: Muñeca Izquierda     16: Muñeca Derecha
23: Cadera Izquierda     24: Cadera Derecha
25: Rodilla Izquierda    26: Rodilla Derecha
27: Tobillo Izquierdo    28: Tobillo Derecho
```

### Los 33 Puntos Clave de Pose Completos
```
0: Nariz
1-10: Puntos clave faciales
11-22: Parte superior del cuerpo
23-32: Parte inferior del cuerpo
```

## Combinaciones de Teclas

### Aplicación Principal (`main.py`)
- `q`: Salir de la aplicación

### Recolección de Datos (`model/add_pose.py`)
- `ESPACIO`: Grabar pose actual
- `n`: Siguiente clase de gesto
- `p`: Clase anterior de gesto
- `q`: Salir

## Formatos de Archivos

### CSV de Etiquetas de Gestos
```csv
0,De_pie
1,Saludando
2,Señalando
3,Brazos_arriba
4,Brazos_abajo
```

### CSV de Datos de Entrenamiento
```csv
gesture_id,x1,y1,z1,x2,y2,z2,...,x12,y12,z12
0,0.1,0.2,0.01,0.15,0.25,0.02,...
```

## Problemas Comunes y Soluciones

### Cámara No Encontrada
```python
cap = cv2.VideoCapture(0)  # Probar 1, 2, etc. para diferentes cámaras
if not cap.isOpened():
    print("Error: Cámara no encontrada")
```

### Modelo No Se Carga
```python
# Verificar rutas de archivos
import os
print(os.path.exists('model/keypoint_classifier.tflite'))
print(os.path.exists('model/keypoint_classifier_label.csv'))
```

### FPS Bajos
```python
# Reducir complejidad del modelo
detector = PoseDetectionPosture(model_complexity=0)

# Saltar frames
if frame_count % 2 == 0:  # Procesar cada segundo frame
    results = detector.extract_pose(frame)
```

### Gesto No Se Detecta
```python
# Reducir confianza de detección
detector = PoseDetectionPosture(min_pose_detection_confidence=0.3)

# Reducir requisito de consistencia del buffer
buffer = GestureBuffer(buffer_len=10, min_consistency=0.5)
```

## Configuración del Entorno

### Paquetes Requeridos
```bash
opencv-python>=4.5.0
mediapipe>=0.8.0
numpy>=1.19.0
tflite-runtime>=2.5.0
requests>=2.25.0
```

### Estructura de Directorios
```
proyecto/
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

## Lista de Verificación de Optimización de Rendimiento

- [ ] Usar complejidad de modelo apropiada (0 para velocidad, 2 para precisión)
- [ ] Ajustar confianza de detección según el entorno
- [ ] Implementar salto de frames si es necesario
- [ ] Usar procesamiento asíncrono para operaciones pesadas
- [ ] Perfilar con `cProfile` para encontrar cuellos de botella
- [ ] Considerar aceleración GPU si está disponible
- [ ] Optimizar resolución de imagen (640x480 a menudo es suficiente)
- [ ] Usar threading para operaciones independientes
- [ ] Cachear cálculos repetidos
- [ ] Minimizar actualizaciones de GUI por frame

## Lista de Verificación de Pruebas

- [ ] Probar con diferentes condiciones de iluminación
- [ ] Probar con varias distancias de la cámara
- [ ] Probar con oclusiones parciales
- [ ] Verificar que todos los gestos sean reconocidos
- [ ] Verificar uso de memoria a lo largo del tiempo
- [ ] Validar integridad de datos CSV
- [ ] Probar manejo de errores (sin cámara, archivos faltantes)
- [ ] Verificar carga de configuración
- [ ] Probar con múltiples personas en frame
- [ ] Verificar rendimiento en hardware objetivo

## Configuraciones Recomendadas por Escenario

### Escritorio - Alta Precisión
```json
{
  "constants": {
    "pose": {
      "min_pose_detection_confidence": 0.7,
      "min_pose_tracking_confidence": 0.7,
      "model_complexity": 2
    },
    "buffer_length": 30
  }
}
```

### Escritorio - Balanceado
```json
{
  "constants": {
    "pose": {
      "min_pose_detection_confidence": 0.5,
      "min_pose_tracking_confidence": 0.5,
      "model_complexity": 1
    },
    "buffer_length": 20
  }
}
```

### Raspberry Pi - Optimizado
```json
{
  "constants": {
    "pose": {
      "min_pose_detection_confidence": 0.3,
      "min_pose_tracking_confidence": 0.3,
      "model_complexity": 0
    },
    "buffer_length": 10,
    "enable_segmentation": false
  }
}
```

## Comandos de Diagnóstico

### Verificar Instalación
```bash
python3 -c "import cv2; print('OpenCV:', cv2.__version__)"
python3 -c "import mediapipe; print('MediaPipe:', mediapipe.__version__)"
python3 -c "import tflite_runtime.interpreter; print('TFLite: OK')"
```

### Probar Cámara
```python
import cv2
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
if ret:
    print(f"Cámara OK - Resolución: {frame.shape}")
    cv2.imshow("Test", frame)
    cv2.waitKey(1000)
else:
    print("Error de cámara")
cap.release()
cv2.destroyAllWindows()
```

### Benchmark de Rendimiento
```python
import time
import cv2
from mp_utils.pose_posture import PoseDetectionPosture

detector = PoseDetectionPosture()
cap = cv2.VideoCapture(0)

start_time = time.time()
frame_count = 0

while frame_count < 100:
    ret, frame = cap.read()
    if ret:
        results = detector.extract_pose(frame)
        frame_count += 1

end_time = time.time()
fps = frame_count / (end_time - start_time)
print(f"FPS Promedio: {fps:.2f}")

cap.release()
detector.close()
```

## Patrones de Uso Avanzados

### Procesamiento por Lotes
```python
def procesar_lote_frames(frames, detector):
    """Procesar múltiples frames de manera eficiente"""
    resultados = []
    for frame in frames:
        resultado = detector.extract_pose(frame)
        resultados.append(resultado)
    return resultados
```

### Detección con Timeouts
```python
import signal

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Detección de pose timeout")

def detectar_con_timeout(detector, frame, timeout_seconds=1):
    """Detectar pose con timeout para evitar bloqueos"""
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    
    try:
        resultado = detector.extract_pose(frame)
        return resultado
    except TimeoutError:
        print("Detección de pose timeout")
        return None
    finally:
        signal.alarm(0)
```

### Validación de Calidad de Pose
```python
def validar_calidad_pose(landmarks, umbral_visibilidad=0.5):
    """Validar que la pose detectada tiene suficiente calidad"""
    if not landmarks:
        return False
    
    puntos_visibles = 0
    total_puntos = len(landmarks)
    
    for landmark in landmarks:
        if landmark.visibility > umbral_visibilidad:
            puntos_visibles += 1
    
    ratio_visibilidad = puntos_visibles / total_puntos
    return ratio_visibilidad > 0.7  # 70% de puntos deben ser visibles
```

## Solución de Problemas Avanzada

### Memory Leaks
```python
import gc
import psutil
import os

def monitorear_memoria():
    """Monitorear uso de memoria del proceso"""
    proceso = psutil.Process(os.getpid())
    memoria_mb = proceso.memory_info().rss / 1024 / 1024
    print(f"Uso de memoria: {memoria_mb:.2f} MB")
    return memoria_mb

# Llamar periódicamente para detectar memory leaks
# Ejecutar gc.collect() si la memoria crece continuamente
```

### Debugging de Performance
```python
import cProfile
import pstats

def perfilar_deteccion_pose():
    """Perfilar rendimiento de detección de pose"""
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Tu código de detección aquí
    detector = PoseDetectionPosture()
    cap = cv2.VideoCapture(0)
    
    for _ in range(100):
        ret, frame = cap.read()
        if ret:
            detector.extract_pose(frame)
    
    cap.release()
    detector.close()
    
    profiler.disable()
    
    # Analizar resultados
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative').print_stats(10)
```

Esta guía de referencia rápida proporciona acceso inmediato a los comandos y configuraciones más utilizados en el sistema de reconocimiento de posturas.