# Compilación de MediaPipe 0.8.8 para ARM (Raspberry Pi)

## Información Crítica

### Por qué compilar desde fuente

MediaPipe no proporciona wheels precompilados para arquitecturas ARM, especialmente para ARMv7 32-bit. La compilación desde fuente es necesaria para:
- Optimizar para el hardware específico (NEON, VFPv4)
- Deshabilitar GPU (no soportada en RPi 3)
- Reducir el tamaño del binario
- Asegurar compatibilidad con el sistema

## Preparación Específica para ARM

### 1. Configuración de Bazel para ARM

```bash
# Verificar arquitectura
uname -m  # Debe mostrar: armv7l

# Instalar Bazel correcto
# IMPORTANTE: Bazel 3.7.2 es la última versión compatible con MediaPipe 0.8.8
wget https://github.com/bazelbuild/bazel/releases/download/3.7.2/bazel-3.7.2-linux-armv7l
```

### 2. Parches necesarios para ARM

Crear archivo `mediapipe_arm_patches.patch`:

```patch
diff --git a/mediapipe/python/BUILD b/mediapipe/python/BUILD
index 1234567..abcdefg 100644
--- a/mediapipe/python/BUILD
+++ b/mediapipe/python/BUILD
@@ -50,6 +50,7 @@ cc_library(
     ],
     linkopts = select({
         "//conditions:default": [],
+        "//mediapipe:android_arm": ["-latomic"],
     }),
 )
```

Aplicar:
```bash
cd ~/mediapipe
patch -p1 < mediapipe_arm_patches.patch
```

### 3. Configuración detallada de Bazel

Archivo `.bazelrc.user` optimizado:

```bash
# Configuración base para ARM
build --crosstool_top=//external:android/crosstool
build --cpu=armeabi-v7a
build --host_crosstool_top=@bazel_tools//tools/cpp:toolchain

# Deshabilitar GPU (crítico para RPi)
build --define MEDIAPIPE_DISABLE_GPU=1
build --define MEDIAPIPE_DISABLE_OPENCL=1

# Optimizaciones ARM específicas
build --copt -march=armv7-a
build --copt -mfpu=neon-vfpv4
build --copt -mfloat-abi=hard
build --copt -funsafe-math-optimizations
build --copt -ftree-vectorize
build --copt -ffast-math

# Optimizaciones de compilación
build --copt -O3
build --copt -DNDEBUG
build --copt -flto
build --copt -ffunction-sections
build --copt -fdata-sections

# Optimizaciones de enlace
build --linkopt -Wl,--gc-sections
build --linkopt -Wl,--as-needed
build --linkopt -latomic
build --linkopt -lpthread

# Reducir uso de memoria durante compilación
build --local_ram_resources=2048
build --local_cpu_resources=2
build --jobs=2

# Cache
build --disk_cache=/tmp/bazel_cache
```

## Proceso de Compilación Detallado

### 1. Preparar el entorno

```bash
# Limpiar cache anterior
rm -rf ~/.cache/bazel

# Configurar variables de entorno
export PYTHON_BIN_PATH=$(which python3)
export PYTHON_LIB_PATH=$(python3 -c "import site; print(site.getsitepackages()[0])")
export TF_NEED_CUDA=0
export CC_OPT_FLAGS="-march=armv7-a -mfpu=neon-vfpv4 -mfloat-abi=hard -O3"
```

### 2. Modificar setup.py para ARM

Editar `~/mediapipe/setup.py`:

```python
# Buscar la sección de configuración de Bazel
# Agregar después de las importaciones:
import platform

# En la función _invoke_shell_command, agregar:
if platform.machine() == 'armv7l':
    bazel_command.extend([
        '--copt=-march=armv7-a',
        '--copt=-mfpu=neon-vfpv4',
        '--linkopt=-latomic'
    ])
```

### 3. Compilación paso a paso

```bash
cd ~/mediapipe

# Paso 1: Generar protobuf
python setup.py gen_protos

# Paso 2: Compilar extensiones C++
# Esto puede fallar varias veces, reintentar es normal
bazel build -c opt \
    --define MEDIAPIPE_DISABLE_GPU=1 \
    --copt -DMEDIAPIPE_DISABLE_GPU \
    //mediapipe/modules/pose_landmark:pose_landmark_cpu \
    //mediapipe/python:_framework_bindings

# Paso 3: Construir wheel
python setup.py bdist_wheel --plat-name linux_armv7l

# Paso 4: Instalar
pip install dist/mediapipe-0.8.8-cp39-cp39-linux_armv7l.whl
```

## Solución de Problemas Comunes

### Error: "undefined reference to `__atomic_*`"

```bash
# Solución: Asegurar que -latomic está en los flags
export LDFLAGS="-latomic"
bazel clean --expunge
# Recompilar
```

### Error: "Out of memory"

```bash
# Reducir paralelismo
bazel build --jobs=1 --local_ram_resources=1024 ...

# O compilar por partes:
bazel build //mediapipe/python:_framework_bindings
bazel build //mediapipe/modules/pose_landmark:pose_landmark_cpu
```

### Error: "No module named 'mediapipe.python._framework_bindings'"

```python
# Verificar que el .so se compiló correctamente
find ~/mediapipe -name "*_framework_bindings*.so"

# Si no existe, compilar específicamente:
bazel build //mediapipe/python:_framework_bindings.so
```

### Error: "Illegal instruction"

```bash
# El binario se compiló para una arquitectura incorrecta
# Verificar flags de compilación:
readelf -A bazel-bin/mediapipe/python/_framework_bindings.so | grep Tag_CPU

# Debe mostrar: Tag_CPU_arch: v7
```

## Optimizaciones Adicionales

### 1. Reducir tamaño del binario

```bash
# Agregar a .bazelrc.user
build --strip=always
build --copt -fvisibility=hidden
build --copt -fvisibility-inlines-hidden
```

### 2. Compilar solo módulos necesarios

```python
# En setup.py, comentar módulos no necesarios:
POSE_GRAPHS = [
    'pose_tracking_cpu',
    # 'pose_tracking_gpu',  # No necesario para RPi
]
```

### 3. Usar ccache para acelerar recompilaciones

```bash
sudo apt install ccache
export CC="ccache gcc"
export CXX="ccache g++"
```

## Script de compilación automatizado

```bash
#!/bin/bash
# compile_mediapipe_arm.sh

set -e

# Configuración
MEDIAPIPE_VERSION="0.8.8"
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Compilando MediaPipe ${MEDIAPIPE_VERSION} para ARM${NC}"

# Verificar arquitectura
if [[ $(uname -m) != "armv7l" ]]; then
    echo -e "${RED}Error: Este script es solo para ARMv7${NC}"
    exit 1
fi

# Limpiar
cd ~/mediapipe
bazel clean --expunge
rm -rf dist build

# Configurar entorno
export PYTHON_BIN_PATH=$(which python3)
export PYTHON_LIB_PATH=$(python3 -c "import site; print(site.getsitepackages()[0])")
export CC_OPT_FLAGS="-march=armv7-a -mfpu=neon-vfpv4 -mfloat-abi=hard -O3"
export LDFLAGS="-latomic"

# Generar protobuf
echo "Generando protobuf..."
python setup.py gen_protos

# Compilar con reintentos
MAX_ATTEMPTS=3
for i in $(seq 1 $MAX_ATTEMPTS); do
    echo "Intento $i de $MAX_ATTEMPTS..."
    if python setup.py build_ext; then
        echo -e "${GREEN}Compilación exitosa${NC}"
        break
    else
        if [ $i -eq $MAX_ATTEMPTS ]; then
            echo -e "${RED}Compilación falló después de $MAX_ATTEMPTS intentos${NC}"
            exit 1
        fi
        echo "Reintentando..."
        sleep 5
    fi
done

# Crear wheel
echo "Creando wheel..."
python setup.py bdist_wheel --plat-name linux_armv7l

# Verificar
WHEEL_FILE=$(ls dist/mediapipe-*.whl)
if [ -f "$WHEEL_FILE" ]; then
    echo -e "${GREEN}Wheel creado: $WHEEL_FILE${NC}"
    echo "Para instalar: pip install $WHEEL_FILE"
else
    echo -e "${RED}Error: No se encontró el archivo wheel${NC}"
    exit 1
fi
```

## Verificación Post-Instalación

```python
# test_mediapipe_arm.py
import mediapipe as mp
import cv2
import numpy as np

def test_mediapipe():
    print(f"MediaPipe version: {mp.__version__}")
    
    # Test Pose
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(
        static_image_mode=False,
        model_complexity=0,  # Lite model para ARM
        min_detection_confidence=0.5
    )
    
    # Crear imagen de prueba
    test_image = np.zeros((480, 640, 3), dtype=np.uint8)
    results = pose.process(test_image)
    
    print("✓ MediaPipe Pose inicializado correctamente")
    pose.close()
    
    # Verificar optimizaciones ARM
    import subprocess
    result = subprocess.run(['readelf', '-A', mp.__file__], 
                          capture_output=True, text=True)
    if 'Tag_CPU_arch: v7' in result.stdout:
        print("✓ Compilado para ARMv7")
    if 'Tag_FP_arch: VFPv4' in result.stdout:
        print("✓ Optimizaciones NEON habilitadas")

if __name__ == "__main__":
    test_mediapipe()
```

## Notas de Rendimiento

### FPS esperados en RPi 3:
- Modelo Lite (complexity=0): 8-12 FPS
- Modelo Full (complexity=1): 3-5 FPS
- Modelo Heavy (complexity=2): 1-2 FPS

### Recomendaciones:
1. Usar siempre model_complexity=0
2. Procesar a 320x240 y escalar para display
3. Skip frames (procesar 1 de cada 2-3)
4. Deshabilitar segmentación
5. Usar static_image_mode=False para tracking