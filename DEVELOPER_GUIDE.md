# Guía del Desarrollador - Sistema de Reconocimiento de Posturas

## Arquitectura del Sistema

```
┌─────────────────┐
│   main.py       │ ← Punto de entrada
└────────┬────────┘
         │
    ┌────┴─────────────────────────────┐
    │                                  │
┌───▼────────┐  ┌──────────────┐  ┌───▼──────┐
│ mp_utils   │  │neural_network│  │   gui    │
│            │  │              │  │          │
│-PoseDetect │  │-PoseRecogniz │  │-ThirdPers│
│-PosePosture│  │-KeyPointClas │  │   onGUI  │
└────────────┘  └──────────────┘  └──────────┘
                        │
                 ┌──────▼─────┐
                 │instructions│
                 │            │
                 │-GestureBuff│
                 │-Instructions│
                 └────────────┘
```

## Flujo del Sistema

1. **Captura de Frames**: La cámara captura frames de video
2. **Detección de Poses**: MediaPipe extrae 33 puntos clave de postura
3. **Filtrado de Puntos Clave**: El sistema filtra a 12 articulaciones clave
4. **Preprocesamiento**: Los puntos clave se normalizan y aplanan
5. **Clasificación**: El modelo TFLite predice el gesto
6. **Estabilización**: El buffer de gestos asegura estabilidad
7. **Visualización**: La GUI muestra resultados y estado

## Extensión del Sistema

### Añadiendo Nuevos Gestos

#### Paso 1: Recolección de Datos
```python
# Ejecutar el script de recolección de datos
python model/add_pose.py

# Controles:
# ESPACIO - Grabar pose actual
# 'n' - Siguiente clase de gesto (incrementar NÚMERO)
# 'p' - Clase anterior de gesto
# 'q' - Salir
```

#### Paso 2: Actualizar Etiquetas
Editar `model/keypoint_classifier_label.csv`:
```csv
0,De_pie
1,Saludando
2,Señalando
3,Brazos_arriba
4,Brazos_abajo
5,Tu_nuevo_gesto
```

#### Paso 3: Entrenar Modelo
Usar el notebook Jupyter `model/Keypoint_model_training.ipynb`:
```python
# Secciones clave a modificar:
NUM_CLASSES = 6  # Actualizar según tus gestos
EPOCHS = 100     # Ajustar según el tamaño del dataset

# El notebook realizará:
# 1. Cargar datos de pose desde CSV
# 2. Dividir en conjuntos de entrenamiento/prueba
# 3. Construir y entrenar red neuronal
# 4. Exportar a formato TFLite
```

#### Paso 4: Implementar
Reemplazar archivos del modelo:
```bash
cp nuevo_modelo.tflite model/keypoint_classifier.tflite
```

### Creando Filtros de Pose Personalizados

Crear un nuevo filtro en `mp_utils/filtros_personalizados.py`:
```python
class FiltrosPosePersonalizados:
    # Definir qué puntos clave incluir
    PUNTOS_CLAVE_PARTE_SUPERIOR = [11, 12, 13, 14, 15, 16]
    PUNTOS_CLAVE_PARTE_INFERIOR = [23, 24, 25, 26, 27, 28]
    PUNTOS_CLAVE_MANOS = [15, 16, 17, 18, 19, 20, 21, 22]
    
    @staticmethod
    def filtrar_parte_superior(landmarks):
        """Retorna únicamente puntos clave de la parte superior del cuerpo"""
        return [landmarks[i] for i in FiltrosPosePersonalizados.PUNTOS_CLAVE_PARTE_SUPERIOR
                if i < len(landmarks)]
    
    @staticmethod
    def filtrar_para_sentado(landmarks):
        """Puntos clave optimizados para detección de pose sentado"""
        # Incluir caderas, hombros y cabeza
        puntos_sentado = [0, 11, 12, 23, 24]
        return [landmarks[i] for i in puntos_sentado
                if i < len(landmarks)]
```

### Implementando Lógica de Gestos Personalizada

Crear manejadores de acciones en `instructions/acciones_gestos.py`:
```python
from enum import Enum

class AccionGesto(Enum):
    NINGUNA = 0
    INICIAR_GRABACION = 1
    DETENER_GRABACION = 2
    TOMAR_FOTO = 3
    PARADA_EMERGENCIA = 4

class ManejadorAccionGesto:
    def __init__(self):
        self.mapa_acciones = {
            "Saludando": AccionGesto.INICIAR_GRABACION,
            "Alto": AccionGesto.DETENER_GRABACION,
            "Paz": AccionGesto.TOMAR_FOTO,
            "Pose_X": AccionGesto.PARADA_EMERGENCIA
        }
        self.callbacks_acciones = {}
    
    def registrar_callback(self, accion: AccionGesto, callback):
        """Registrar un callback para una acción específica"""
        self.callbacks_acciones[accion] = callback
    
    def procesar_gesto(self, nombre_gesto: str):
        """Procesar gesto y activar acción asociada"""
        accion = self.mapa_acciones.get(nombre_gesto, AccionGesto.NINGUNA)
        
        if accion in self.callbacks_acciones:
            self.callbacks_acciones[accion]()
            return True
        return False

# Ejemplo de uso:
manejador = ManejadorAccionGesto()
manejador.registrar_callback(
    AccionGesto.TOMAR_FOTO,
    lambda: cv2.imwrite(f"foto_{time.time()}.jpg", frame)
)
```

### Visualización Personalizada

Crear visualizaciones mejoradas en `gui/visualizaciones.py`:
```python
import cv2
import numpy as np

class VisualizadorPose:
    @staticmethod
    def dibujar_esqueleto_3d(image, landmarks, connections):
        """Dibujar esqueleto 3D con visualización de profundidad"""
        height, width = image.shape[:2]
        
        # Convertir coordenadas normalizadas a coordenadas de píxel
        puntos = []
        for lm in landmarks:
            x = int(lm.x * width)
            y = int(lm.y * height)
            z = lm.z * 100  # Escalar Z para visibilidad
            puntos.append((x, y, z))
        
        # Dibujar conexiones con grosor basado en profundidad
        for conexion in connections:
            if conexion[0] < len(puntos) and conexion[1] < len(puntos):
                pt1 = puntos[conexion[0]]
                pt2 = puntos[conexion[1]]
                
                # Calcular grosor basado en Z promedio
                z_promedio = (pt1[2] + pt2[2]) / 2
                grosor = int(5 - z_promedio * 0.02)  # Más cerca = más grueso
                grosor = max(1, min(grosor, 10))
                
                # Color basado en profundidad (rojo=cerca, azul=lejos)
                intensidad_color = int(255 * (1 - z_promedio / 200))
                color = (intensidad_color, 0, 255 - intensidad_color)
                
                cv2.line(image, (pt1[0], pt1[1]), 
                        (pt2[0], pt2[1]), color, grosor)
        
        return image
    
    @staticmethod
    def dibujar_rastro_gesto(image, historial_gestos, posicion):
        """Dibujar un rastro mostrando historial de gestos"""
        longitud_rastro = min(len(historial_gestos), 10)
        
        for i in range(longitud_rastro):
            alpha = (i + 1) / longitud_rastro
            y_offset = posicion[1] - (longitud_rastro - i) * 20
            
            cv2.putText(image, historial_gestos[-(i+1)],
                       (posicion[0], y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX,
                       0.5, (255, 255, 255),
                       int(2 * alpha))
        
        return image
```

### Optimización de Rendimiento

#### 1. Procesamiento Asíncrono
```python
import threading
import queue

class ProcesadorPoseAsincrono:
    def __init__(self, detector, recognizer):
        self.detector = detector
        self.recognizer = recognizer
        self.cola_frames = queue.Queue(maxsize=5)
        self.cola_resultados = queue.Queue(maxsize=5)
        self.hilo_procesamiento = threading.Thread(target=self._procesar_frames)
        self.hilo_procesamiento.daemon = True
        self.ejecutando = True
        
    def iniciar(self):
        self.hilo_procesamiento.start()
    
    def _procesar_frames(self):
        while self.ejecutando:
            try:
                frame = self.cola_frames.get(timeout=0.1)
                results = self.detector.extract_pose(frame)
                gesture_id, _ = self.recognizer.recognize_pose(results, frame)
                self.cola_resultados.put((results, gesture_id))
            except queue.Empty:
                continue
    
    def procesar_frame_asincrono(self, frame):
        if not self.cola_frames.full():
            self.cola_frames.put(frame)
    
    def obtener_resultado(self):
        try:
            return self.cola_resultados.get_nowait()
        except queue.Empty:
            return None, None
```

#### 2. Salto de Frames
```python
class SaltadorFrames:
    def __init__(self, saltar_frames=2):
        self.saltar_frames = saltar_frames
        self.contador_frames = 0
    
    def debe_procesar(self):
        self.contador_frames += 1
        return self.contador_frames % (self.saltar_frames + 1) == 0
```

### Pruebas

#### Pruebas Unitarias
Crear `tests/test_reconocimiento_pose.py`:
```python
import unittest
import numpy as np
from mp_utils.mp_pose import PoseDetection
from neural_network.pose_recognition import PoseRecognizer

class TestReconocimientoPose(unittest.TestCase):
    def setUp(self):
        self.detector = PoseDetection()
        self.recognizer = PoseRecognizer()
    
    def test_deteccion_pose_con_imagen_vacia(self):
        # Probar con imagen en blanco
        imagen_vacia = np.zeros((480, 640, 3), dtype=np.uint8)
        results = self.detector.extract_pose(imagen_vacia)
        self.assertIsNotNone(results)
        self.assertIsNone(results.pose_landmarks)
    
    def test_filtrado_puntos_clave(self):
        # Crear puntos clave simulados
        puntos_clave_simulados = [PuntoClaveSim(i*0.1, i*0.1, i*0.01, 1.0) 
                         for i in range(33)]
        
        # Probar filtrado
        self.detector.results = ResultadosSim(puntos_clave_simulados)
        filtrados = self.detector.filter_landmarks()
        
        # Debe retornar 12 puntos clave (índices 11-16, 23-28)
        self.assertEqual(len(filtrados), 12)
    
    def test_consistencia_buffer_gestos(self):
        from instructions.gesture_buffer import GestureBuffer
        
        buffer = GestureBuffer(buffer_len=5, min_consistency=0.6)
        
        # Añadir mayormente gesto 1
        for _ in range(3):
            buffer.add_gesture(1)
        buffer.add_gesture(2)
        buffer.add_gesture(1)
        
        # Debe retornar 1 (aparece 4/5 veces = 80%)
        self.assertEqual(buffer.get_gesture(), 1)

class PuntoClaveSim:
    def __init__(self, x, y, z, visibility):
        self.x = x
        self.y = y
        self.z = z
        self.visibility = visibility

class ResultadosSim:
    def __init__(self, landmarks):
        self.pose_landmarks = PuntosClavesPoseSim(landmarks)

class PuntosClavesPoseSim:
    def __init__(self, landmarks):
        self.landmark = landmarks

if __name__ == '__main__':
    unittest.main()
```

### Depuración

#### Habilitar Logging de Depuración
```python
import logging

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('reconocimiento_pose.log'),
        logging.StreamHandler()
    ]
)

# Añadir a tus clases
class DeteccionPoseDebug(PoseDetection):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
    
    def extract_pose(self, image):
        self.logger.debug(f"Procesando imagen de tamaño: {image.shape}")
        results = super().extract_pose(image)
        
        if results and results.pose_landmarks:
            self.logger.info(f"Detectados {len(results.pose_landmarks.landmark)} puntos clave")
        else:
            self.logger.warning("No se detectaron puntos clave")
        
        return results
```

#### Herramientas de Visualización
```python
def dibujar_puntos_clave_debug(image, landmarks, titulo="Debug"):
    """Dibujar todos los puntos clave con índices para depuración"""
    imagen_debug = image.copy()
    height, width = image.shape[:2]
    
    for idx, landmark in enumerate(landmarks):
        x = int(landmark.x * width)
        y = int(landmark.y * height)
        
        # Dibujar círculo
        cv2.circle(imagen_debug, (x, y), 5, (0, 255, 0), -1)
        
        # Dibujar índice
        cv2.putText(imagen_debug, str(idx), (x+5, y-5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
    
    cv2.imshow(titulo, imagen_debug)
    return imagen_debug
```

## Implementación

### Soporte Docker
Crear `Dockerfile`:
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

### Gestión de Configuración
```python
import os
from pathlib import Path

class GestorConfiguracion:
    def __init__(self, ruta_config="config_pose.json"):
        self.ruta_config = Path(ruta_config)
        self.config = self.cargar_config()
    
    def cargar_config(self):
        """Cargar configuración con sobreescritura de variables de entorno"""
        with open(self.ruta_config, 'r') as f:
            config = json.load(f)
        
        # Sobreescribir con variables de entorno
        if os.getenv('CONFIANZA_DETECCION_POSE'):
            config['constants']['pose']['min_pose_detection_confidence'] = \
                float(os.getenv('CONFIANZA_DETECCION_POSE'))
        
        if os.getenv('LONGITUD_BUFFER'):
            config['constants']['buffer_length'] = \
                int(os.getenv('LONGITUD_BUFFER'))
        
        return config
    
    def obtener(self, ruta_clave, por_defecto=None):
        """Obtener valor de configuración por notación de punto"""
        claves = ruta_clave.split('.')
        valor = self.config
        
        for clave in claves:
            if isinstance(valor, dict) and clave in valor:
                valor = valor[clave]
            else:
                return por_defecto
        
        return valor
```

## Guías de Contribución

1. **Estilo de Código**: Seguir PEP 8
2. **Documentación**: Actualizar docstrings para todos los métodos públicos
3. **Pruebas**: Añadir pruebas unitarias para nuevas características
4. **Rendimiento**: Perfilar cambios que puedan impactar FPS
5. **Compatibilidad Hacia Atrás**: Mantener compatibilidad del archivo de configuración

## Consideraciones de Seguridad

### Validación de Entrada
```python
def validar_frame_entrada(frame):
    """Validar frame de entrada antes de procesamiento"""
    if frame is None:
        raise ValueError("Frame no puede ser None")
    
    if not isinstance(frame, np.ndarray):
        raise TypeError("Frame debe ser array numpy")
    
    if len(frame.shape) != 3 or frame.shape[2] != 3:
        raise ValueError("Frame debe ser imagen BGR de 3 canales")
    
    if frame.size == 0:
        raise ValueError("Frame no puede estar vacío")
    
    return True

def sanitizar_nombre_gesto(nombre):
    """Sanitizar nombres de gestos para prevenir inyección"""
    import re
    # Permitir solo caracteres alfanuméricos y guiones bajos
    return re.sub(r'[^a-zA-Z0-9_]', '', nombre)
```

### Gestión Segura de Archivos
```python
import os
from pathlib import Path

def ruta_segura_modelo(ruta_modelo):
    """Validar que la ruta del modelo es segura"""
    ruta = Path(ruta_modelo).resolve()
    directorio_base = Path("model").resolve()
    
    # Verificar que la ruta está dentro del directorio del modelo
    try:
        ruta.relative_to(directorio_base)
    except ValueError:
        raise SecurityError("Ruta del modelo fuera del directorio permitido")
    
    if not ruta.exists():
        raise FileNotFoundError(f"Archivo del modelo no encontrado: {ruta}")
    
    return ruta
```

## Monitoreo y Métricas

### Sistema de Métricas
```python
import time
from collections import defaultdict

class MonitorRendimiento:
    def __init__(self):
        self.metricas = defaultdict(list)
        self.contadores = defaultdict(int)
    
    def cronometrar(self, nombre_operacion):
        """Decorador para cronometrar operaciones"""
        def decorador(func):
            def wrapper(*args, **kwargs):
                inicio = time.time()
                try:
                    resultado = func(*args, **kwargs)
                    self.contadores[f"{nombre_operacion}_exito"] += 1
                    return resultado
                except Exception as e:
                    self.contadores[f"{nombre_operacion}_error"] += 1
                    raise
                finally:
                    duracion = time.time() - inicio
                    self.metricas[nombre_operacion].append(duracion)
            return wrapper
        return decorador
    
    def obtener_estadisticas(self):
        """Obtener estadísticas de rendimiento"""
        estadisticas = {}
        for operacion, tiempos in self.metricas.items():
            if tiempos:
                estadisticas[operacion] = {
                    'promedio': sum(tiempos) / len(tiempos),
                    'min': min(tiempos),
                    'max': max(tiempos),
                    'total_llamadas': len(tiempos)
                }
        
        for contador, valor in self.contadores.items():
            estadisticas[contador] = valor
        
        return estadisticas
```

## Integración Continua

### Pipeline CI/CD
Crear `.github/workflows/ci.yml`:
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.8
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest tests/ --cov=./ --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v1
      with:
        file: ./coverage.xml
```

Esto proporciona una base sólida para el desarrollo y extensión del sistema de reconocimiento de posturas, manteniendo altos estándares de calidad y seguridad.