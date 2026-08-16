# Instalación en Raspberry Pi 3

Compilación e instalación de las dependencias nativas del proyecto para ARMv7, y puesta en marcha de `main_rpi.py`. Para el flujo de recolección de datos y entrenamiento del modelo (en la PC), ver [`README.md`](../README.md).

## Especificaciones del hardware

- **Modelo:** Raspberry Pi 3 Model B Plus (Rev 1.3)
- **Arquitectura:** ARMv7, 32-bit
- **CPU:** 4 núcleos @ 1.4 GHz · **RAM:** ~872 MB
- **Python:** 3.7 (el que trae Raspberry Pi OS Buster de fábrica — no actualizar a 3.9, ninguno de los wheels de este documento existe para esa versión en ARMv7)
- **Cámara:** USB o módulo CSI · **SD:** 16 GB mínimo, 32 GB recomendado
- **Tiempo estimado de compilación completa:** 4-6 horas

## Por qué se compila todo desde fuente

OpenCV, MediaPipe y TensorFlow Lite no publican wheels precompilados para ARMv7 de 32 bits. Compilar a mano permite además optimizar para el hardware (NEON, VFPv4), apagar soporte de GPU (la Pi 3 no tiene una utilizable por MediaPipe) y reducir el tamaño final del binario.

---

## Instalación automatizada

Si no necesitás entender cada paso, [`install_rpi.sh`](install_rpi.sh) hace todo lo de este documento con un menú interactivo:

```bash
git clone <url-del-repositorio> shpd-edge-vision
cd shpd-edge-vision
./install_rpi.sh
# Opción 1: instalación completa
```

El resto de esta guía es la versión manual, paso a paso, para cuando algo falla o hace falta ajustar algo puntual.

---

## 1. Preparación del sistema

```bash
sudo apt update && sudo apt upgrade -y && sudo apt dist-upgrade -y

# Expandir el filesystem a toda la SD
sudo raspi-config   # Advanced Options → Expand Filesystem → reboot

# Aumentar el swap (imprescindible: sin esto, la compilación de OpenCV/MediaPipe
# se cuelga por falta de memoria en los ~872 MB de RAM de la Pi 3)
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile     # CONF_SWAPSIZE=100  ->  CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

# GPU split — dejarle más RAM al sistema, MediaPipe no usa la GPU de la Pi 3
sudo raspi-config   # Advanced Options → Memory Split → 128
```

## 2. Dependencias base

```bash
# Herramientas de compilación
sudo apt install -y build-essential cmake git pkg-config \
    gcc g++ make automake python3-dev python3-pip python3-venv \
    wget unzip curl

# Bibliotecas para OpenCV
sudo apt install -y libjpeg-dev libtiff5-dev libjasper-dev libpng-dev \
    libavcodec-dev libavformat-dev libswscale-dev libv4l-dev \
    libxvidcore-dev libx264-dev libfontconfig1-dev libcairo2-dev \
    libgdk-pixbuf2.0-dev libpango1.0-dev libgtk2.0-dev libgtk-3-dev \
    libatlas-base-dev gfortran libhdf5-dev libhdf5-serial-dev \
    libilmbase-dev libopenexr-dev libgstreamer1.0-dev \
    libwebp-dev libopenblas-dev liblapack-dev \
    libprotobuf-dev protobuf-compiler
```

```bash
# Entorno virtual del dispositivo — todo lo que sigue se instala acá dentro
cd ~
python3 -m venv pose_env
source pose_env/bin/activate
pip install --upgrade pip setuptools wheel
```

## 3. Compilar OpenCV 4.5.5.64

```bash
cd ~
wget -O opencv.zip https://github.com/opencv/opencv/archive/4.5.5.zip
wget -O opencv_contrib.zip https://github.com/opencv/opencv_contrib/archive/4.5.5.zip
unzip opencv.zip && unzip opencv_contrib.zip
mv opencv-4.5.5 opencv && mv opencv_contrib-4.5.5 opencv_contrib

cd opencv && mkdir build && cd build

cmake -D CMAKE_BUILD_TYPE=RELEASE \
    -D CMAKE_INSTALL_PREFIX=/usr/local \
    -D OPENCV_EXTRA_MODULES_PATH=~/opencv_contrib/modules \
    -D ENABLE_NEON=ON -D ENABLE_VFPV3=ON \
    -D BUILD_TESTS=OFF -D INSTALL_PYTHON_EXAMPLES=OFF \
    -D OPENCV_ENABLE_NONFREE=ON \
    -D CMAKE_SHARED_LINKER_FLAGS=-latomic \
    -D BUILD_EXAMPLES=OFF -D WITH_TBB=ON -D WITH_V4L=ON \
    -D WITH_QT=OFF -D WITH_OPENGL=ON \
    -D OPENCV_PYTHON3_INSTALL_PATH=~/pose_env/lib/python3.7/site-packages \
    -D PYTHON_EXECUTABLE=~/pose_env/bin/python3 \
    ..

# 2-3 horas. Usar -j1 en vez de -j2 si falla por falta de memoria.
make -j2
sudo make install
sudo ldconfig
```

Verificar:
```bash
source ~/pose_env/bin/activate
python -c "import cv2; print(cv2.__version__)"   # -> 4.5.5
```

## 4. Compilar MediaPipe 0.8.8 para ARM

MediaPipe no publica wheels para ARMv7, así que se compila con Bazel. Esta es la parte más larga y la que más suele fallar — la sección de [problemas comunes](#problemas-comunes) cubre los errores típicos de este paso.

```bash
# Bazel 3.7.2 es la última versión compatible con MediaPipe 0.8.8
cd ~
wget https://github.com/bazelbuild/bazel/releases/download/3.7.2/bazel-3.7.2-linux-armv7l
chmod +x bazel-3.7.2-linux-armv7l
sudo mv bazel-3.7.2-linux-armv7l /usr/local/bin/bazel

git clone https://github.com/google/mediapipe.git
cd mediapipe
git checkout v0.8.8
```

Configuración de Bazel para ARM (`~/mediapipe/.bazelrc.user`):

```bash
cat > .bazelrc.user << 'EOF'
build --crosstool_top=//external:android/crosstool
build --cpu=armeabi-v7a
build --host_crosstool_top=@bazel_tools//tools/cpp:toolchain

# Sin GPU: la Pi 3 no tiene una que MediaPipe pueda usar
build --define MEDIAPIPE_DISABLE_GPU=1

# Optimizaciones especificas de ARMv7 / NEON
build --copt -march=armv7-a
build --copt -mfpu=neon-vfpv4
build --copt -mfloat-abi=hard
build --copt -O3
build --copt -flto
build --copt -ffunction-sections
build --copt -fdata-sections
build --linkopt -Wl,--gc-sections
build --linkopt=-latomic

# Menos paralelismo: la Pi 3 tiene ~872 MB de RAM
build --local_ram_resources=2048
build --jobs=2
EOF
```

Compilar e instalar:

```bash
source ~/pose_env/bin/activate
pip install numpy==1.19.5 attrs>=19.1.0 absl-py matplotlib opencv-contrib-python==4.5.5.64

cd ~/mediapipe
python setup.py gen_protos
python setup.py bdist_wheel --plat-name linux_armv7l

pip install dist/mediapipe-0.8.8-cp37-cp37m-linux_armv7l.whl
```

Si falla por memoria, bajar el paralelismo (`--jobs=1 --local_ram_resources=1024`) o compilar el binding de a partes: `bazel build //mediapipe/python:_framework_bindings` y luego `bazel build //mediapipe/modules/pose_landmark:pose_landmark_cpu` por separado.

## 5. Instalar TensorFlow Lite Runtime

```bash
source ~/pose_env/bin/activate

# Wheel precompilado para ARMv7 / Python 3.7 (ver tambien requirements-rpi.txt)
pip install https://github.com/google-coral/pycoral/releases/download/release-frogfish/tflite_runtime-2.5.0-cp37-cp37m-linux_armv7l.whl
```

Si el wheel deja de estar disponible, se compila desde fuente:

```bash
cd ~
git clone https://github.com/tensorflow/tensorflow.git
cd tensorflow
git checkout v2.5.0
./tensorflow/lite/tools/pip_package/build_pip_package_with_cmake.sh
pip install tensorflow/lite/tools/pip_package/gen/tflite_pip/python3/dist/tflite_runtime-2.5.0-cp37-cp37m-linux_armv7l.whl
```

> Este es exactamente el mecanismo que usa `neural_network/pose_recognition.py` (`from tflite_runtime.interpreter import Interpreter`) — no TensorFlow completo, que es demasiado pesado para la Pi 3.

## 6. Configurar el proyecto

```bash
cd ~/shpd-edge-vision   # si no lo clonaste todavia, el paso anterior a este
source ~/pose_env/bin/activate

pip install -r requirements-rpi.txt
pip install requests   # si vas a usar las notificaciones de instructions/gesture_instructions.py
```

Copiá a la Pi el modelo ya entrenado (ver el Paso 3 de `README.md`, se hace desde la PC):

```bash
scp model/keypoint_classifier.tflite model/keypoint_classifier_label.csv \
    pi@<ip-de-la-raspberry>:~/shpd-edge-vision/model/
```

Verificar que cargue con el runtime real de la Pi:

```bash
python3 -c "
from tflite_runtime.interpreter import Interpreter
i = Interpreter(model_path='model/keypoint_classifier.tflite')
i.allocate_tensors()
print('Interpreter cargado correctamente ✅')
"
```

**No hace falta editar `main_pc.py` a mano.** Las optimizaciones para la Pi (frame skipping, resolución de cámara reducida, `model_complexity=0`, backend `V4L2`) ya están escritas en `main_rpi.py` — ese es el punto de entrada que se corre en el dispositivo:

```bash
python3 main_rpi.py
```

Si querés afinar algo puntual sin tocar código, `main_rpi.py` lee `config_pose_rpi.json` si existe (si no, usa `config_pose.json`). Ejemplo de `config_pose_rpi.json`:

```json
{
  "constants": {
    "pose": { "min_pose_detection_confidence": 0.3, "min_pose_tracking_confidence": 0.3 },
    "buffer_length": 10,
    "speed": 40
  },
  "model_paths": {
    "pose_recogniser": "model/keypoint_classifier.tflite",
    "keypoint_classifier_labels": "model/keypoint_classifier_label.csv"
  },
  "initial_options": { "following": false },
  "rpi_optimizations": {
    "model_complexity": 0,
    "enable_segmentation": false,
    "smooth_landmarks": false,
    "frame_skip": 2,
    "camera_resolution": [640, 480],
    "camera_fps": 15,
    "processing_resolution": [320, 240]
  }
}
```

## 7. (Opcional) Inicio automático al bootear

```bash
cat > ~/start_pose_detector.sh << 'EOF'
#!/bin/bash
cd ~/shpd-edge-vision
source ~/pose_env/bin/activate
export DISPLAY=:0
python main_rpi.py
EOF
chmod +x ~/start_pose_detector.sh

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

---

## Rendimiento esperado

| Configuración | FPS aproximados |
|---|---|
| `model_complexity=0` (lite) + 320×240 | 8-12 FPS |
| `model_complexity=0` + 160×120 | 12-15 FPS |
| `model_complexity=1` (full) | 3-5 FPS — evitar en Pi 3 |
| `model_complexity=2` (heavy) | 1-2 FPS — no usable en tiempo real |
| + frame skip 2 | +30% FPS aprox. |

`main_rpi.py` ya usa `model_complexity=0` y frame skipping por defecto. Tips adicionales: cámara USB en vez de módulo CSI, disipadores/ventilador si vas a correrlo por tiempo prolongado, y no mostrar ventanas de más (cada `cv.imshow` cuesta CPU).

---

## Problemas comunes

**Error de memoria durante la compilación (OpenCV o MediaPipe)**
Confirmá que el swap quedó en 2048 MB (paso 1). Si sigue fallando, bajá el paralelismo: `make -j1`, o en Bazel `--jobs=1 --local_ram_resources=1024`.

**`undefined reference to '__atomic_*'` compilando MediaPipe**
Falta `-latomic` en el link. Confirmá que está en `.bazelrc.user` (`build --linkopt=-latomic`) y `export LDFLAGS="-latomic"` antes de compilar; después `bazel clean --expunge` y recompilar.

**`No module named 'mediapipe.python._framework_bindings'`**
El `.so` no se terminó de compilar. `find ~/mediapipe -name "*_framework_bindings*.so"` — si no aparece, compilar puntualmente ese target: `bazel build //mediapipe/python:_framework_bindings`.

**`Illegal instruction` al importar mediapipe u opencv**
Se compiló para la arquitectura equivocada. `readelf -A <archivo>.so | grep Tag_CPU_arch` debe mostrar `v7`, no `v8` ni genérico.

**Cámara no detectada**
```bash
vcgencmd get_camera        # deberia decir: supported=1 detected=1
sudo raspi-config          # Interfacing Options -> Camera -> Enable
sudo usermod -a -G video $USER
```

**`ImportError` con cv2 o mediapipe ya instalados**
```bash
export PYTHONPATH="${PYTHONPATH}:/usr/local/lib/python3.7/site-packages"
echo 'export PYTHONPATH="${PYTHONPATH}:/usr/local/lib/python3.7/site-packages"' >> ~/.bashrc
```

**FPS muy bajos en tiempo real**
Usar `main_rpi.py` (no `main_pc.py`), subir `frame_skip` a 3-4 en `config_pose_rpi.json`, bajar `processing_resolution` a `[160, 120]`.

---

## Verificación rápida del entorno completo

```bash
python3 -c "
import cv2, mediapipe as mp
import tflite_runtime.interpreter as tflite
print('OpenCV:', cv2.__version__)
print('MediaPipe:', mp.__version__)
print('TFLite Runtime: OK')

cap = cv2.VideoCapture(0)
ret, _ = cap.read()
print('Cámara:', 'OK' if ret else 'FALLÓ')
cap.release()
"
```

Para probar puntualmente que el modelo entrenado carga con este mismo runtime, usar `model/interpreter.py` (documentado en `README.md`, sección del Paso 2).
