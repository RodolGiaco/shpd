# Guía de Instalación para Raspberry Pi 3 Model B Plus

## Especificaciones del Sistema
- **Modelo**: Raspberry Pi 3 Model B Plus Rev 1.3
- **Arquitectura**: ARMv7 32-bit
- **CPU**: 4 núcleos @ 1.4GHz
- **RAM**: ~872 MB
- **Conectividad**: USB 2.0, Ethernet LAN78xx, Wi-Fi brcmfmac

## Tabla de Contenidos
1. [Preparación del Sistema](#preparación-del-sistema)
2. [Instalación de Dependencias Base](#instalación-de-dependencias-base)
3. [Compilación de OpenCV 4.5.5.64](#compilación-de-opencv-4.5.5.64)
4. [Compilación de MediaPipe 0.8.8](#compilación-de-mediapipe-0.8.8)
5. [Instalación de TensorFlow Lite](#instalación-de-tensorflow-lite)
6. [Configuración del Proyecto](#configuración-del-proyecto)
7. [Optimizaciones para Raspberry Pi](#optimizaciones-para-raspberry-pi)
8. [Solución de Problemas](#solución-de-problemas)

## Preparación del Sistema

### 1. Actualizar el Sistema Operativo
```bash
sudo apt update
sudo apt upgrade -y
sudo apt dist-upgrade -y
sudo rpi-update
```

### 2. Expandir el Sistema de Archivos
```bash
sudo raspi-config
# Seleccionar: Advanced Options → Expand Filesystem
sudo reboot
```

### 3. Aumentar el Swap (Necesario para compilación)
```bash
# Detener el swap actual
sudo dphys-swapfile swapoff

# Modificar el tamaño del swap
sudo nano /etc/dphys-swapfile
# Cambiar CONF_SWAPSIZE=100 a CONF_SWAPSIZE=2048

# Reiniciar el swap
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### 4. Configurar GPU Split
```bash
sudo raspi-config
# Seleccionar: Advanced Options → Memory Split
# Establecer a 128 MB para GPU
```

## Instalación de Dependencias Base

### 1. Herramientas de Compilación
```bash
sudo apt install -y build-essential cmake git pkg-config
sudo apt install -y gcc g++ make automake
sudo apt install -y python3-dev python3-pip python3-venv
sudo apt install -y wget unzip curl
```

### 2. Bibliotecas de Sistema
```bash
# Bibliotecas para OpenCV
sudo apt install -y libjpeg-dev libtiff5-dev libjasper-dev libpng-dev
sudo apt install -y libavcodec-dev libavformat-dev libswscale-dev libv4l-dev
sudo apt install -y libxvidcore-dev libx264-dev
sudo apt install -y libfontconfig1-dev libcairo2-dev
sudo apt install -y libgdk-pixbuf2.0-dev libpango1.0-dev
sudo apt install -y libgtk2.0-dev libgtk-3-dev
sudo apt install -y libatlas-base-dev gfortran
sudo apt install -y libhdf5-dev libhdf5-serial-dev libhdf5-103
sudo apt install -y libqtgui4 libqtwebkit4 libqt4-test python3-pyqt5

# Bibliotecas adicionales
sudo apt install -y libilmbase-dev libopenexr-dev libgstreamer1.0-dev
sudo apt install -y libwebp-dev libopenblas-dev liblapack-dev
sudo apt install -y libprotobuf-dev protobuf-compiler
```

### 3. Crear Entorno Virtual
```bash
cd ~
python3 -m venv pose_env
source pose_env/bin/activate

# Actualizar pip
pip install --upgrade pip setuptools wheel
```

## Compilación de OpenCV 4.5.5.64

### 1. Descargar OpenCV
```bash
cd ~
wget -O opencv.zip https://github.com/opencv/opencv/archive/4.5.5.zip
wget -O opencv_contrib.zip https://github.com/opencv/opencv_contrib/archive/4.5.5.zip
unzip opencv.zip
unzip opencv_contrib.zip
mv opencv-4.5.5 opencv
mv opencv_contrib-4.5.5 opencv_contrib
```

### 2. Configurar la Compilación
```bash
cd ~/opencv
mkdir build
cd build

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

### 3. Compilar OpenCV (Esto tomará 2-3 horas)
```bash
# Usar solo 2 cores para evitar problemas de memoria
make -j2

# Si falla por memoria, usar:
make -j1

# Instalar
sudo make install
sudo ldconfig
```

### 4. Verificar Instalación
```bash
source ~/pose_env/bin/activate
python -c "import cv2; print(cv2.__version__)"
# Debería mostrar: 4.5.5
```

## Compilación de MediaPipe 0.8.8

### 1. Instalar Bazel
```bash
# MediaPipe 0.8.8 requiere Bazel 3.7.2
cd ~
wget https://github.com/bazelbuild/bazel/releases/download/3.7.2/bazel-3.7.2-linux-arm64
chmod +x bazel-3.7.2-linux-arm64
sudo mv bazel-3.7.2-linux-arm64 /usr/local/bin/bazel
```

### 2. Clonar MediaPipe
```bash
cd ~
git clone https://github.com/google/mediapipe.git
cd mediapipe
git checkout v0.8.8
```

### 3. Configurar para ARM
```bash
# Crear archivo de configuración para ARM
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

### 4. Compilar MediaPipe Python
```bash
# Instalar dependencias Python
source ~/pose_env/bin/activate
pip install numpy==1.19.5
pip install attrs>=19.1.0
pip install absl-py
pip install matplotlib
pip install opencv-contrib-python==4.5.5.64

# Compilar wheel de MediaPipe
cd ~/mediapipe
python setup.py gen_protos
python setup.py bdist_wheel
```

### 5. Instalar MediaPipe
```bash
# El archivo .whl estará en dist/
pip install dist/mediapipe-0.8.8-cp39-cp39-linux_armv7l.whl
```

## Instalación de TensorFlow Lite

### 1. Instalar TFLite Runtime para ARM
```bash
source ~/pose_env/bin/activate

# Para ARMv7 32-bit
pip install https://github.com/google-coral/pycoral/releases/download/v2.0.0/tflite_runtime-2.5.0.post1-cp39-cp39-linux_armv7l.whl

# Si falla, compilar desde fuente:
cd ~
git clone https://github.com/tensorflow/tensorflow.git
cd tensorflow
git checkout v2.5.0
./tensorflow/lite/tools/pip_package/build_pip_package_with_cmake.sh
pip install tensorflow/lite/tools/pip_package/gen/tflite_pip/python3/dist/tflite_runtime-2.5.0-cp39-cp39-linux_armv7l.whl
```

## Configuración del Proyecto

### 1. Clonar el Repositorio
```bash
cd ~
git clone [URL_DEL_REPOSITORIO] SmartHealthyPostureDetector
cd SmartHealthyPostureDetector
```

### 2. Instalar Dependencias Restantes
```bash
source ~/pose_env/bin/activate
pip install requests

# Crear requirements específico para Raspberry Pi
cat > requirements_rpi.txt << EOF
opencv-python==4.5.5.64
mediapipe==0.8.8
numpy==1.19.5
tflite-runtime==2.5.0
requests>=2.25.0
EOF

pip install -r requirements_rpi.txt
```

### 3. Optimizar Configuración para Raspberry Pi
```bash
# Crear configuración optimizada
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

### 4. Modificar main.py para Raspberry Pi
```python
# Agregar al inicio de main.py
import os
os.environ['OPENCV_VIDEOIO_PRIORITY_MSMF'] = '0'

# Modificar la inicialización de la cámara
cap = cv.VideoCapture(0, cv.CAP_V4L2)
cap.set(cv.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv.CAP_PROP_FPS, 15)
cap.set(cv.CAP_PROP_BUFFERSIZE, 1)
```

## Optimizaciones para Raspberry Pi

### 1. Optimización de MediaPipe
```python
# En mp_utils/mp_pose.py, modificar __init__:
def __init__(self,
             static_image_mode=False,
             model_complexity=0,  # Cambiar a 0 para modelo lite
             enable_segmentation=False,  # Deshabilitar segmentación
             min_detection_confidence=0.3,
             min_tracking_confidence=0.3):
```

### 2. Frame Skipping
```python
# Agregar a main.py
frame_counter = 0
FRAME_SKIP = 2  # Procesar cada 2 frames

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    frame_counter += 1
    if frame_counter % FRAME_SKIP != 0:
        continue
    
    # Procesar frame...
```

### 3. Reducir Resolución de Procesamiento
```python
# En main.py, después de capturar el frame
frame = cv.resize(frame, (320, 240))  # Procesar a menor resolución
# ... procesamiento ...
display_frame = cv.resize(annotated_frame, (640, 480))  # Mostrar a resolución mayor
```

### 4. Deshabilitar GUI Innecesaria
```python
# Modificar para mostrar solo ventana principal
# Comentar en main.py:
# cv.imshow("Segmentación del cuerpo", colored_mask)
```

## Script de Inicio Automático

### 1. Crear Script de Inicio
```bash
cat > ~/start_pose_detector.sh << EOF
#!/bin/bash
cd ~/SmartHealthyPostureDetector
source ~/pose_env/bin/activate
export DISPLAY=:0
python main.py
EOF

chmod +x ~/start_pose_detector.sh
```

### 2. Configurar Autostart
```bash
# Agregar al archivo de autostart
mkdir -p ~/.config/autostart
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

## Solución de Problemas

### 1. Error de Memoria
```bash
# Si hay errores de memoria durante compilación
sudo systemctl stop dphys-swapfile
sudo systemctl disable dphys-swapfile
# Reiniciar y volver a habilitar swap
```

### 2. Error de Cámara
```bash
# Verificar cámara
vcgencmd get_camera
# Debería mostrar: supported=1 detected=1

# Habilitar cámara
sudo raspi-config
# Interfacing Options → Camera → Enable

# Permisos de video
sudo usermod -a -G video $USER
```

### 3. Error de ImportError con cv2
```bash
# Verificar rutas
export PYTHONPATH="${PYTHONPATH}:/usr/local/lib/python3.9/site-packages"
echo 'export PYTHONPATH="${PYTHONPATH}:/usr/local/lib/python3.9/site-packages"' >> ~/.bashrc
```

### 4. MediaPipe Performance Issues
```python
# Reducir complejidad en tiempo de ejecución
pose_detection = pose_posture.PoseDetectionPosture(
    static_image_mode=False,
    model_complexity=0,  # Lite model
    min_pose_detection_confidence=0.5,  # Aumentar umbral
    min_pose_tracking_confidence=0.5
)
```

### 5. Optimización de Energía
```bash
# Configurar governor de CPU para performance
echo performance | sudo tee /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor

# Para ahorro de energía, usar:
echo ondemand | sudo tee /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
```

## Testing y Verificación

### 1. Test de Componentes
```python
# test_rpi_setup.py
import cv2
import mediapipe as mp
import tflite_runtime.interpreter as tflite
import numpy as np

print(f"OpenCV version: {cv2.__version__}")
print(f"MediaPipe version: {mp.__version__}")
print("TFLite Runtime: OK")

# Test camera
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
if ret:
    print("Camera: OK")
else:
    print("Camera: FAILED")
cap.release()

# Test MediaPipe
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False, model_complexity=0)
print("MediaPipe Pose: OK")
pose.close()
```

### 2. Benchmark de Performance
```python
# benchmark_rpi.py
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
fps = frame_count / (end_time - start_time)
print(f"Average FPS: {fps:.2f}")

cap.release()
detector.close()
```

## Notas Finales

- La compilación completa puede tomar 4-6 horas
- Se recomienda usar disipadores de calor durante la compilación
- Para producción, considerar usar Raspberry Pi 4 con más RAM
- El modelo lite de MediaPipe es suficiente para la mayoría de aplicaciones
- Considerar usar cámara USB en lugar de CSI para mejor compatibilidad