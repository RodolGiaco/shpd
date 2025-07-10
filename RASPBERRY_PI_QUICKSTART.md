# Inicio Rápido - Raspberry Pi 3

## Requerimientos Mínimos
- Raspberry Pi 3 Model B Plus (ARMv7 32-bit)
- Raspbian OS (Buster o posterior)
- Cámara USB o módulo de cámara RPi
- 16GB SD Card (32GB recomendado)
- Conexión a Internet
- 4-6 horas para compilación completa

## Instalación Rápida (Automatizada)

```bash
# Descargar el repositorio
git clone [URL_DEL_REPOSITORIO] SmartHealthyPostureDetector
cd SmartHealthyPostureDetector

# Ejecutar instalador automático
./install_rpi.sh
# Seleccionar opción 1 para instalación completa
```

## Instalación Manual (Paso a Paso)

### 1. Preparar Sistema
```bash
# Aumentar swap
sudo nano /etc/dphys-swapfile
# Cambiar CONF_SWAPSIZE=100 a CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

# Actualizar sistema
sudo apt update && sudo apt upgrade -y
```

### 2. Instalar OpenCV Precompilado (Opción Rápida)
```bash
# Si no necesitas compilar desde fuente
sudo apt install python3-opencv
pip3 install opencv-python==4.5.5.64
```

### 3. Instalar MediaPipe Precompilado
```bash
# Intentar con wheel precompilado de la comunidad
pip3 install mediapipe-rpi4==0.8.8
# O buscar en: https://github.com/jiuqiant/mediapipe_python_aarch64
```

### 4. Si Falla, Compilar MediaPipe (Básico)
```bash
# Instalar Bazel
wget https://github.com/bazelbuild/bazel/releases/download/3.7.2/bazel-3.7.2-linux-armv7l
chmod +x bazel-3.7.2-linux-armv7l
sudo mv bazel-3.7.2-linux-armv7l /usr/local/bin/bazel

# Clonar y compilar
git clone https://github.com/google/mediapipe.git
cd mediapipe
git checkout v0.8.8

# Configurar para ARM
echo "build --define MEDIAPIPE_DISABLE_GPU=1" > .bazelrc.user
echo "build --copt -march=armv7-a" >> .bazelrc.user

# Compilar
python3 setup.py bdist_wheel
pip3 install dist/*.whl
```

### 5. Configurar Proyecto
```bash
cd ~/SmartHealthyPostureDetector

# Instalar dependencias
pip3 install tflite-runtime requests numpy

# Usar configuración optimizada
cp config_pose.json config_pose_rpi.json
# Editar config_pose_rpi.json y cambiar:
# "model_complexity": 0
# "min_pose_detection_confidence": 0.3
```

## Ejecutar Aplicación

### Versión Optimizada para RPi
```bash
python3 main_rpi.py
```

### Versión Original (más lenta)
```bash
python3 main.py
```

## Optimizaciones Rápidas

### 1. Reducir Resolución
En `config_pose_rpi.json`:
```json
"rpi_optimizations": {
    "processing_resolution": [320, 240],
    "camera_resolution": [640, 480],
    "frame_skip": 2
}
```

### 2. Usar Modelo Lite
En el código o configuración:
```python
model_complexity=0  # Siempre usar 0 en RPi
```

### 3. Deshabilitar Características
```python
enable_segmentation=False
smooth_landmarks=False
```

## Solución de Problemas Comunes

### Cámara no detectada
```bash
# Habilitar cámara
sudo raspi-config
# Interfacing Options → Camera → Enable

# Verificar
vcgencmd get_camera
```

### Error de memoria
```bash
# Reducir uso de memoria
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
```

### FPS muy bajos
- Usar `main_rpi.py` en lugar de `main.py`
- Aumentar frame_skip a 3 o 4
- Reducir resolución a 160x120 para procesamiento

### ImportError
```bash
# Agregar al ~/.bashrc
export PYTHONPATH="${PYTHONPATH}:/usr/local/lib/python3.9/site-packages"
source ~/.bashrc
```

## Rendimiento Esperado

| Configuración | FPS Esperados |
|--------------|---------------|
| Modelo Lite + 320x240 | 8-12 FPS |
| Modelo Lite + 160x120 | 12-15 FPS |
| Frame Skip 2 | +30% FPS |
| Frame Skip 3 | +50% FPS |

## Tips Adicionales

1. **Usar cámara USB**: Mejor rendimiento que módulo CSI
2. **Refrigeración**: Usar disipadores o ventilador
3. **Overclock moderado**: Puede ayudar ~10-15% FPS
4. **Deshabilitar GUI innecesaria**: Solo mostrar ventana principal
5. **Procesamiento en background**: No mostrar ventanas para máximo FPS

## Verificar Instalación

```bash
python3 -c "import cv2; print('OpenCV:', cv2.__version__)"
python3 -c "import mediapipe; print('MediaPipe:', mediapipe.__version__)"
python3 -c "import tflite_runtime.interpreter; print('TFLite: OK')"
```

## Siguiente Paso

Para más detalles, consultar:
- [RASPBERRY_PI_INSTALLATION.md](RASPBERRY_PI_INSTALLATION.md) - Guía completa
- [MEDIAPIPE_ARM_COMPILATION.md](MEDIAPIPE_ARM_COMPILATION.md) - Compilación detallada