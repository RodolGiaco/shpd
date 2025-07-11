# Guía Completa de Instalación para Raspberry Pi 3 Model B Plus

## Especificaciones Técnicas del Sistema

### Características del Hardware Objetivo
- **Modelo**: Raspberry Pi 3 Model B Plus Rev 1.3
- **Arquitectura de Procesador**: ARMv7 32-bit
- **Unidad Central de Procesamiento**: Quad-core ARM Cortex-A53 @ 1.4GHz
- **Memoria RAM**: 1GB LPDDR2 (~872 MB disponibles para el usuario)
- **Conectividad**: USB 2.0, Ethernet LAN78xx, Wi-Fi 802.11n brcmfmac

## Índice de Contenidos
1. [Metodología de Preparación del Sistema](#metodología-de-preparación-del-sistema)
2. [Instalación de Dependencias Base](#instalación-de-dependencias-base)
3. [Compilación de OpenCV 4.5.5.64](#compilación-de-opencv-4.5.5.64)
4. [Compilación de MediaPipe 0.8.8](#compilación-de-mediapipe-0.8.8)
5. [Instalación de TensorFlow Lite](#instalación-de-tensorflow-lite)
6. [Configuración del Proyecto](#configuración-del-proyecto)
7. [Optimizaciones Específicas para Raspberry Pi](#optimizaciones-específicas-para-raspberry-pi)
8. [Diagnóstico y Resolución de Problemas](#diagnóstico-y-resolución-de-problemas)

## Metodología de Preparación del Sistema

### Fase 1: Actualización del Sistema Operativo

```bash
# Actualización de repositorios y paquetes del sistema
sudo apt update
sudo apt upgrade -y
sudo apt dist-upgrade -y

# Actualización del firmware del sistema
sudo rpi-update
```

**Justificación**: La actualización completa del sistema asegura compatibilidad con las últimas optimizaciones del kernel y drivers específicos para el hardware Raspberry Pi.

### Fase 2: Expansión del Sistema de Archivos

```bash
# Configuración mediante raspi-config
sudo raspi-config
# Navegación: Advanced Options → Expand Filesystem

# Reinicio requerido para aplicar cambios
sudo reboot
```

### Fase 3: Configuración del Espacio de Intercambio Virtual

```bash
# Detención del servicio de swap actual
sudo dphys-swapfile swapoff

# Modificación de la configuración de swap
sudo nano /etc/dphys-swapfile
# Parámetro a modificar: CONF_SWAPSIZE=100 → CONF_SWAPSIZE=2048

# Aplicación de la nueva configuración
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

**Fundamentación Técnica**: El incremento del espacio de intercambio de 100MB a 2GB es crítico para el proceso de compilación de MediaPipe, que requiere significativamente más memoria de la disponible físicamente en el dispositivo.

### Fase 4: Optimización de Asignación de Memoria GPU

```bash
sudo raspi-config
# Ruta de configuración: Advanced Options → Memory Split
# Asignación recomendada: 128 MB para GPU
```

## Instalación de Dependencias Base

### Conjunto 1: Herramientas de Desarrollo y Compilación

```bash
# Toolchain de compilación esencial
sudo apt install -y build-essential cmake git pkg-config
sudo apt install -y gcc g++ make automake

# Herramientas de desarrollo Python
sudo apt install -y python3-dev python3-pip python3-venv

# Utilidades de red y descarga
sudo apt install -y wget unzip curl
```

### Conjunto 2: Bibliotecas de Soporte para OpenCV

```bash
# Bibliotecas de procesamiento de imágenes
sudo apt install -y libjpeg-dev libtiff5-dev libjasper-dev libpng-dev

# Bibliotecas de procesamiento de video
sudo apt install -y libavcodec-dev libavformat-dev libswscale-dev libv4l-dev
sudo apt install -y libxvidcore-dev libx264-dev

# Bibliotecas de fuentes y renderizado
sudo apt install -y libfontconfig1-dev libcairo2-dev
sudo apt install -y libgdk-pixbuf2.0-dev libpango1.0-dev

# Bibliotecas de interfaz gráfica
sudo apt install -y libgtk2.0-dev libgtk-3-dev

# Bibliotecas de álgebra lineal optimizada
sudo apt install -y libatlas-base-dev gfortran

# Bibliotecas de manejo de datos científicos
sudo apt install -y libhdf5-dev libhdf5-serial-dev libhdf5-103
sudo apt install -y libqtgui4 libqtwebkit4 libqt4-test python3-pyqt5

# Bibliotecas adicionales especializadas
sudo apt install -y libilmbase-dev libopenexr-dev libgstreamer1.0-dev
sudo apt install -y libwebp-dev libopenblas-dev liblapack-dev
sudo apt install -y libprotobuf-dev protobuf-compiler
```

### Conjunto 3: Creación de Entorno Virtual de Python

```bash
# Navegación al directorio home del usuario
cd ~

# Creación de entorno virtual aislado
python3 -m venv pose_env

# Activación del entorno virtual
source pose_env/bin/activate

# Actualización de herramientas de gestión de paquetes
pip install --upgrade pip setuptools wheel
```

**Ventajas del Entorno Virtual**: Aislamiento de dependencias, prevención de conflictos entre versiones de bibliotecas, y facilidad de replicación del entorno de desarrollo.

## Compilación de OpenCV 4.5.5.64

### Fase 1: Descarga de Código Fuente

```bash
# Navegación al directorio de trabajo
cd ~

# Descarga de OpenCV principal y módulos contrib
wget -O opencv.zip https://github.com/opencv/opencv/archive/4.5.5.zip
wget -O opencv_contrib.zip https://github.com/opencv/opencv_contrib/archive/4.5.5.zip

# Extracción de archivos comprimidos
unzip opencv.zip
unzip opencv_contrib.zip

# Renombrado de directorios para simplicidad
mv opencv-4.5.5 opencv
mv opencv_contrib-4.5.5 opencv_contrib
```

### Fase 2: Configuración de Parámetros de Compilación

```bash
# Navegación al directorio de OpenCV
cd ~/opencv

# Creación del directorio de compilación
mkdir build
cd build

# Configuración mediante CMake con optimizaciones específicas
cmake -D CMAKE_BUILD_TYPE=RELEASE \
    -D CMAKE_INSTALL_PREFIX=/usr/local \
    -D OPENCV_EXTRA_MODULES_PATH=~/opencv_contrib/modules \
    -D ENABLE_NEON=ON \
    -D ENABLE_VFPV3=ON \
    -D BUILD_TESTS=OFF \
    -D INSTALL_PYTHON_EXAMPLES=OFF \
    -D OPENCV_ENABLE_NONFREE=ON \
    -D CMAKE_SHARED_LINKER_FLAGS=-latomic \
    -D BUILD_EXAMPLES=OFF \
    -D WITH_TBB=ON \
    -D WITH_V4L=ON \
    -D WITH_QT=OFF \
    -D WITH_OPENGL=ON \
    -D OPENCV_PYTHON3_INSTALL_PATH=~/pose_env/lib/python3.9/site-packages \
    -D PYTHON_EXECUTABLE=~/pose_env/bin/python3 \
    ..
```

**Análisis de Parámetros de Compilación**:
- `ENABLE_NEON=ON`: Activación de instrucciones SIMD para aceleración vectorial
- `ENABLE_VFPV3=ON`: Habilitación de unidad de punto flotante optimizada
- `CMAKE_SHARED_LINKER_FLAGS=-latomic`: Solución para operaciones atómicas en ARM

### Fase 3: Proceso de Compilación

```bash
# Compilación con paralelización limitada (prevención de agotamiento de memoria)
make -j2

# Alternativa en caso de problemas de memoria
# make -j1

# Instalación del software compilado
sudo make install
sudo ldconfig
```

**Tiempo Estimado**: 2-3 horas dependiendo de la configuración del sistema y velocidad de la tarjeta SD.

### Fase 4: Verificación de la Instalación

```bash
# Activación del entorno virtual
source ~/pose_env/bin/activate

# Verificación de la versión instalada
python -c "import cv2; print(cv2.__version__)"
# Salida esperada: 4.5.5
```

## Compilación de MediaPipe 0.8.8

### Fase 1: Instalación de Bazel (Sistema de Construcción)

```bash
# Descarga de Bazel compatible con MediaPipe 0.8.8
cd ~
wget https://github.com/bazelbuild/bazel/releases/download/3.7.2/bazel-3.7.2-linux-arm64

# Configuración de permisos y ubicación
chmod +x bazel-3.7.2-linux-arm64
sudo mv bazel-3.7.2-linux-arm64 /usr/local/bin/bazel
```

**Nota de Compatibilidad**: Bazel 3.7.2 es la última versión oficialmente compatible con MediaPipe 0.8.8 en arquitecturas ARM.

### Fase 2: Descarga y Configuración de MediaPipe

```bash
# Clonación del repositorio MediaPipe
cd ~
git clone https://github.com/google/mediapipe.git
cd mediapipe

# Checkout a la versión específica requerida
git checkout v0.8.8
```

### Fase 3: Configuración Específica para Arquitectura ARM

```bash
# Creación de archivo de configuración para ARM
cat > .bazelrc.user << EOF
build --crosstool_top=//external:android/crosstool
build --cpu=armeabi-v7a
build --host_crosstool_top=@bazel_tools//tools/cpp:toolchain
build --define MEDIAPIPE_DISABLE_GPU=1
build --copt -march=armv7-a
build --copt -mfpu=neon-vfpv4
build --copt -mfloat-abi=hard
build --copt -O3
build --copt -flto
build --copt -ffunction-sections
build --copt -fdata-sections
build --linkopt -Wl,--gc-sections
build --linkopt=-latomic
EOF
```

**Explicación de Parámetros**:
- `MEDIAPIPE_DISABLE_GPU=1`: Deshabilitación de procesamiento GPU (no compatible con RPi)
- `-march=armv7-a`: Optimización específica para arquitectura ARMv7
- `-mfpu=neon-vfpv4`: Utilización de unidad de procesamiento vectorial NEON

### Fase 4: Compilación de MediaPipe Python

```bash
# Activación del entorno virtual
source ~/pose_env/bin/activate

# Instalación de dependencias Python específicas
pip install numpy==1.19.5
pip install attrs>=19.1.0
pip install absl-py
pip install matplotlib
pip install opencv-contrib-python==4.5.5.64

# Generación de archivos Protocol Buffers
python setup.py gen_protos

# Compilación del wheel de distribución
python setup.py bdist_wheel
```

### Fase 5: Instalación de MediaPipe

```bash
# Instalación del wheel generado
pip install dist/mediapipe-0.8.8-cp39-cp39-linux_armv7l.whl
```

## Instalación de TensorFlow Lite

### Metodología de Instalación para ARMv7

```bash
# Activación del entorno virtual
source ~/pose_env/bin/activate

# Instalación mediante wheel precompilado oficial
pip install https://github.com/google-coral/pycoral/releases/download/v2.0.0/tflite_runtime-2.5.0.post1-cp39-cp39-linux_armv7l.whl
```

### Procedimiento Alternativo: Compilación desde Código Fuente

```bash
# En caso de fallo de la instalación precompilada
cd ~
git clone https://github.com/tensorflow/tensorflow.git
cd tensorflow
git checkout v2.5.0

# Compilación específica para ARM
./tensorflow/lite/tools/pip_package/build_pip_package_with_cmake.sh

# Instalación del wheel generado
pip install tensorflow/lite/tools/pip_package/gen/tflite_pip/python3/dist/tflite_runtime-2.5.0-cp39-cp39-linux_armv7l.whl
```

## Configuración del Proyecto

### Fase 1: Descarga del Repositorio del Proyecto

```bash
# Navegación al directorio home
cd ~

# Clonación del repositorio principal
git clone [URL_DEL_REPOSITORIO] SmartHealthyPostureDetector
cd SmartHealthyPostureDetector
```

### Fase 2: Instalación de Dependencias Adicionales

```bash
# Activación del entorno virtual
source ~/pose_env/bin/activate

# Instalación de bibliotecas de comunicación
pip install requests

# Creación de archivo de requisitos específico para Raspberry Pi
cat > requirements_rpi.txt << EOF
opencv-python==4.5.5.64
mediapipe==0.8.8
numpy==1.19.5
tflite-runtime==2.5.0
requests>=2.25.0
EOF

# Instalación de todas las dependencias
pip install -r requirements_rpi.txt
```

### Fase 3: Configuración Optimizada para Raspberry Pi

```bash
# Creación de archivo de configuración específico
cat > config_pose_rpi.json << EOF
{
  "constants": {
    "pose": {
      "min_pose_detection_confidence": 0.3,
      "min_pose_tracking_confidence": 0.3,
      "min_pose_presence_confidence": 0.3
    },
    "gui": {
      "hand_window_height": 160,
      "hand_window_width": 240
    },
    "buffer_length": 10,
    "speed": 40
  },
  "model_paths": {
    "pose_recogniser": "model/keypoint_classifier.tflite",
    "keypoint_classifier_labels": "model/keypoint_classifier_label.csv"
  },
  "initial_options": {
    "following": false
  },
  "rpi_optimizations": {
    "model_complexity": 0,
    "enable_segmentation": false,
    "smooth_landmarks": false,
    "frame_skip": 2,
    "camera_resolution": [640, 480],
    "camera_fps": 15
  }
}
EOF
```

### Fase 4: Adaptaciones del Código Principal

```python
# Modificaciones recomendadas para main.py
import os
os.environ['OPENCV_VIDEOIO_PRIORITY_MSMF'] = '0'

# Configuración optimizada de captura de video
cap = cv.VideoCapture(0, cv.CAP_V4L2)
cap.set(cv.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv.CAP_PROP_FPS, 15)
cap.set(cv.CAP_PROP_BUFFERSIZE, 1)
```

## Optimizaciones Específicas para Raspberry Pi

### Optimización 1: Configuración de MediaPipe

```python
# Modificación en mp_utils/mp_pose.py
def __init__(self,
             static_image_mode=False,
             model_complexity=0,  # Modelo lite obligatorio
             enable_segmentation=False,  # Deshabilitación de segmentación
             min_detection_confidence=0.3,
             min_tracking_confidence=0.3):
```

### Optimización 2: Implementación de Salto de Frames

```python
# Incorporación en main.py
frame_counter = 0
FRAME_SKIP = 2  # Procesamiento cada 2 frames

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    frame_counter += 1
    if frame_counter % FRAME_SKIP != 0:
        continue
    
    # Lógica de procesamiento de frames...
```

### Optimización 3: Reducción de Resolución de Procesamiento

```python
# Implementación en bucle principal
# Reducción de resolución para procesamiento
frame_process = cv.resize(frame, (320, 240))
# ... procesamiento con frame_process ...
# Escalado para visualización
display_frame = cv.resize(annotated_frame, (640, 480))
```

### Optimización 4: Eliminación de GUI No Esencial

```python
# Comentar o eliminar en main.py las siguientes líneas:
# cv.imshow("Segmentación del cuerpo", colored_mask)
```

## Script de Inicio Automático

### Creación de Script de Ejecución

```bash
# Generación de script de inicio
cat > ~/start_pose_detector.sh << EOF
#!/bin/bash
cd ~/SmartHealthyPostureDetector
source ~/pose_env/bin/activate
export DISPLAY=:0
python main.py
EOF

# Asignación de permisos de ejecución
chmod +x ~/start_pose_detector.sh
```

### Configuración de Autostart del Sistema

```bash
# Creación del directorio de autostart
mkdir -p ~/.config/autostart

# Creación del archivo de configuración de autostart
cat > ~/.config/autostart/pose_detector.desktop << EOF
[Desktop Entry]
Type=Application
Name=Pose Detector
Exec=/home/pi/start_pose_detector.sh
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF
```

## Diagnóstico y Resolución de Problemas

### Problema 1: Errores de Memoria Durante Compilación

```bash
# Detención temporal del servicio de swap
sudo systemctl stop dphys-swapfile
sudo systemctl disable dphys-swapfile

# Reinicio del sistema y rehabilitación
# Reiniciar manualmente después del reinicio
```

### Problema 2: Errores de Detección de Cámara

```bash
# Verificación del estado de la cámara
vcgencmd get_camera
# Salida esperada: supported=1 detected=1

# Habilitación mediante raspi-config
sudo raspi-config
# Ruta: Interfacing Options → Camera → Enable

# Configuración de permisos de grupo
sudo usermod -a -G video $USER
```

### Problema 3: Errores de Importación de cv2

```bash
# Configuración de rutas de Python
export PYTHONPATH="${PYTHONPATH}:/usr/local/lib/python3.9/site-packages"
echo 'export PYTHONPATH="${PYTHONPATH}:/usr/local/lib/python3.9/site-packages"' >> ~/.bashrc
```

### Problema 4: Problemas de Rendimiento de MediaPipe

```python
# Configuración de parámetros conservadores
pose_detection = pose_posture.PoseDetectionPosture(
    static_image_mode=False,
    model_complexity=0,  # Modelo lite obligatorio
    min_pose_detection_confidence=0.5,  # Incremento del umbral
    min_pose_tracking_confidence=0.5
)
```

### Problema 5: Optimización de Gestión de Energía

```bash
# Configuración de governor de CPU para rendimiento
echo performance | sudo tee /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor

# Para modo de ahorro de energía:
echo ondemand | sudo tee /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
```

## Protocolo de Testing y Verificación

### Test 1: Verificación de Componentes del Sistema

```python
# Archivo: test_rpi_setup.py
import cv2
import mediapipe as mp
import tflite_runtime.interpreter as tflite
import numpy as np

print(f"Versión OpenCV: {cv2.__version__}")
print(f"Versión MediaPipe: {mp.__version__}")
print("TensorFlow Lite Runtime: Operativo")

# Verificación de la cámara
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
if ret:
    print("Cámara: Operativa")
else:
    print("Cámara: FALLO")
cap.release()

# Verificación de MediaPipe
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False, model_complexity=0)
print("MediaPipe Pose: Operativo")
pose.close()
```

### Test 2: Benchmark de Rendimiento

```python
# Archivo: benchmark_rpi.py
import time
import cv2
from mp_utils.pose_posture import PoseDetectionPosture

detector = PoseDetectionPosture(model_complexity=0)
cap = cv2.VideoCapture(0)

frame_count = 0
start_time = time.time()

while frame_count < 100:
    ret, frame = cap.read()
    if ret:
        results = detector.extract_pose(frame)
        frame_count += 1

end_time = time.time()
fps_promedio = frame_count / (end_time - start_time)
print(f"FPS Promedio: {fps_promedio:.2f}")

cap.release()
detector.close()
```

## Consideraciones Finales

### Tiempo Total de Implementación
- **Compilación completa**: 4-6 horas
- **Configuración del sistema**: 30-60 minutos
- **Testing y optimización**: 1-2 horas

### Recomendaciones de Hardware Adicional
- **Refrigeración**: Disipadores de calor durante compilación intensiva
- **Almacenamiento**: Tarjeta SD Clase 10 U3 para mejor rendimiento I/O
- **Alimentación**: Fuente de 5V/3A estable para operación continua

### Consideraciones para Producción
- Utilizar Raspberry Pi 4 con 4GB RAM para aplicaciones críticas
- Implementar watchdog de sistema para reinicio automático
- Configurar logging detallado para monitoreo de rendimiento

Esta guía proporciona una metodología completa y sistemática para la implementación exitosa del sistema de detección de posturas en plataformas Raspberry Pi, optimizada para aplicaciones de investigación académica y desarrollo de prototipos.