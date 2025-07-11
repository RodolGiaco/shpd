# Compilación Especializada de MediaPipe 0.8.8 para Arquitectura ARM (Raspberry Pi)

## Fundamentos Teóricos y Justificación

### Marco Conceptual de la Necesidad de Compilación

MediaPipe, desarrollado por Google Research, no proporciona distribuciones precompiladas (wheels) para arquitecturas ARM, especialmente para la variante ARMv7 de 32 bits utilizada en Raspberry Pi 3. Esta limitación técnica requiere la compilación desde código fuente para lograr:

1. **Optimización específica del hardware**: Aprovechamiento de instrucciones SIMD NEON y unidad de punto flotante VFPv4
2. **Deshabilitación de capacidades GPU**: Eliminación de dependencias CUDA/OpenCL no compatibles
3. **Reducción del footprint binario**: Minimización del tamaño ejecutable para sistemas embebidos
4. **Garantía de compatibilidad del sistema**: Aseguramiento de funcionalidad en el ecosistema target

## Metodología de Preparación Específica para ARM

### Fase 1: Verificación de Arquitectura del Sistema

```bash
# Validación de la arquitectura del procesador
uname -m  
# Salida esperada: armv7l (ARM version 7, little-endian)

# Verificación de capacidades del procesador
cat /proc/cpuinfo | grep -E "(model name|Features)"
```

**Análisis de Salida**: La presencia de características como "neon", "vfpv3", y "vfpv4" en el campo Features confirma la disponibilidad de optimizaciones vectoriales.

### Fase 2: Instalación de Bazel Compatible

```bash
# Descarga de la versión específicamente compatible
wget https://github.com/bazelbuild/bazel/releases/download/3.7.2/bazel-3.7.2-linux-armv7l

# Configuración de permisos y ubicación en PATH
chmod +x bazel-3.7.2-linux-armv7l
sudo mv bazel-3.7.2-linux-armv7l /usr/local/bin/bazel

# Verificación de la instalación
bazel version
```

**Consideración Crítica**: Bazel 3.7.2 representa la última versión del sistema de construcción con soporte completo para MediaPipe 0.8.8 en plataformas ARM.

## Implementación de Parches Específicos para ARM

### Parche 1: Corrección de Enlazado Atómico

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

**Aplicación del parche**:
```bash
cd ~/mediapipe
patch -p1 < mediapipe_arm_patches.patch
```

**Justificación Técnica**: Las operaciones atómicas en arquitecturas ARM requieren enlazado explícito con la biblioteca libatomic para garantizar atomicidad en operaciones de memoria compartida.

## Configuración Avanzada de Bazel

### Archivo de Configuración Optimizado

Crear `.bazelrc.user` con parámetros especializados:

```bash
# Configuración fundamental para arquitectura ARM
build --crosstool_top=//external:android/crosstool
build --cpu=armeabi-v7a
build --host_crosstool_top=@bazel_tools//tools/cpp:toolchain

# Deshabilitación de capacidades GPU (crítico para RPi)
build --define MEDIAPIPE_DISABLE_GPU=1
build --define MEDIAPIPE_DISABLE_OPENCL=1

# Optimizaciones específicas para ARMv7
build --copt -march=armv7-a
build --copt -mfpu=neon-vfpv4
build --copt -mfloat-abi=hard
build --copt -funsafe-math-optimizations
build --copt -ftree-vectorize
build --copt -ffast-math

# Optimizaciones agresivas de compilación
build --copt -O3
build --copt -DNDEBUG
build --copt -flto
build --copt -ffunction-sections
build --copt -fdata-sections

# Optimizaciones de enlazado
build --linkopt -Wl,--gc-sections
build --linkopt -Wl,--as-needed
build --linkopt -latomic
build --linkopt -lpthread

# Gestión de recursos durante compilación
build --local_ram_resources=2048
build --local_cpu_resources=2
build --jobs=2

# Configuración de cache
build --disk_cache=/tmp/bazel_cache
```

**Análisis de Parámetros Críticos**:
- `--copt -funsafe-math-optimizations`: Permite optimizaciones matemáticas no estrictamente conformes con IEEE 754
- `--copt -flto`: Habilitación de Link Time Optimization para mejor optimización inter-modular
- `--local_ram_resources=2048`: Limitación de uso de RAM durante compilación para prevenir agotamiento

## Protocolo de Compilación Detallado

### Fase 1: Preparación del Entorno de Desarrollo

```bash
# Limpieza de cache anterior para evitar conflictos
rm -rf ~/.cache/bazel
rm -rf /tmp/bazel_cache
mkdir -p /tmp/bazel_cache

# Configuración de variables de entorno especializadas
export PYTHON_BIN_PATH=$(which python3)
export PYTHON_LIB_PATH=$(python3 -c "import site; print(site.getsitepackages()[0])")
export TF_NEED_CUDA=0
export CC_OPT_FLAGS="-march=armv7-a -mfpu=neon-vfpv4 -mfloat-abi=hard -O3"
export LDFLAGS="-latomic"
```

### Fase 2: Modificación de setup.py para Compatibilidad ARM

Editar `~/mediapipe/setup.py` para incluir optimizaciones específicas:

```python
# Incorporar después de las importaciones estándar
import platform
import subprocess

# Función modificada para detección de arquitectura
def _invoke_shell_command(cmd, **kwargs):
    # Configuración específica para ARM
    if platform.machine() == 'armv7l':
        # Agregar flags específicos para ARMv7
        if 'bazel' in cmd[0]:
            cmd.extend([
                '--copt=-march=armv7-a',
                '--copt=-mfpu=neon-vfpv4',
                '--copt=-mfloat-abi=hard',
                '--linkopt=-latomic'
            ])
    
    # Llamada original con modificaciones
    return subprocess.run(cmd, **kwargs)
```

### Fase 3: Compilación Paso a Paso con Manejo de Errores

```bash
cd ~/mediapipe

# Paso 1: Generación de archivos Protocol Buffers
echo "Iniciando generación de protobuf..."
python setup.py gen_protos
if [ $? -ne 0 ]; then
    echo "Error en generación de protobuf"
    exit 1
fi

# Paso 2: Pre-compilación de componentes críticos
echo "Pre-compilando componentes críticos..."
bazel build -c opt \
    --define MEDIAPIPE_DISABLE_GPU=1 \
    --copt -DMEDIAPIPE_DISABLE_GPU \
    //mediapipe/modules/pose_landmark:pose_landmark_cpu

# Paso 3: Compilación de bindings de Python
echo "Compilando framework bindings..."
bazel build -c opt \
    --define MEDIAPIPE_DISABLE_GPU=1 \
    //mediapipe/python:_framework_bindings

# Paso 4: Construcción del wheel con reintentos automáticos
MAX_ATTEMPTS=3
for attempt in $(seq 1 $MAX_ATTEMPTS); do
    echo "Intento de compilación $attempt de $MAX_ATTEMPTS"
    
    if python setup.py bdist_wheel --plat-name linux_armv7l; then
        echo "Compilación exitosa en intento $attempt"
        break
    else
        if [ $attempt -eq $MAX_ATTEMPTS ]; then
            echo "Compilación falló después de $MAX_ATTEMPTS intentos"
            exit 1
        fi
        echo "Reintentando después de limpieza..."
        bazel clean
        sleep 10
    fi
done

# Paso 5: Instalación del wheel generado
pip install dist/mediapipe-0.8.8-cp39-cp39-linux_armv7l.whl
```

## Diagnóstico y Resolución de Problemas Críticos

### Error 1: Referencias Atómicas No Definidas

**Síntoma**: `undefined reference to '__atomic_*'`

**Solución Sistemática**:
```bash
# Configuración explícita de flags de enlazado
export LDFLAGS="-latomic"
export CFLAGS="-march=armv7-a -mfpu=neon-vfpv4"
export CXXFLAGS="-march=armv7-a -mfpu=neon-vfpv4"

# Limpieza completa y recompilación
bazel clean --expunge
rm -rf ~/.cache/bazel

# Reintento de compilación con flags explícitos
python setup.py bdist_wheel --plat-name linux_armv7l
```

### Error 2: Agotamiento de Memoria Durante Compilación

**Síntoma**: Procesos de compilación terminados por OOM killer

**Estrategias de Mitigación**:
```bash
# Estrategia 1: Reducción de paralelismo
bazel build --jobs=1 --local_ram_resources=1024 \
    //mediapipe/python:_framework_bindings

# Estrategia 2: Compilación por componentes
bazel build //mediapipe/python:_framework_bindings
bazel build //mediapipe/modules/pose_landmark:pose_landmark_cpu
bazel build //mediapipe/calculators/core:*

# Estrategia 3: Configuración de memoria virtual
sudo sysctl vm.overcommit_memory=1
sudo sysctl vm.swappiness=10
```

### Error 3: Módulo de Framework Bindings No Encontrado

**Síntoma**: `No module named 'mediapipe.python._framework_bindings'`

**Procedimiento de Diagnóstico**:
```python
# Verificación de existencia del objeto compartido
import subprocess
result = subprocess.run(['find', '/home/pi', '-name', '*_framework_bindings*.so'], 
                       capture_output=True, text=True)
print("Archivos encontrados:", result.stdout)

# Verificación de arquitectura del binario
subprocess.run(['readelf', '-h', 'path/to/_framework_bindings.so'])
```

**Solución**:
```bash
# Compilación específica del módulo
bazel build //mediapipe/python:_framework_bindings.so

# Verificación de ubicación
find . -name "*_framework_bindings*.so" -exec ls -la {} \;

# Instalación manual si es necesario
cp bazel-bin/mediapipe/python/_framework_bindings.so \
   /path/to/site-packages/mediapipe/python/
```

### Error 4: Instrucción Ilegal en Ejecución

**Síntoma**: `Illegal instruction (core dumped)`

**Análisis de Arquitectura**:
```bash
# Verificación de la arquitectura de compilación
readelf -A bazel-bin/mediapipe/python/_framework_bindings.so | grep Tag_CPU

# Salida esperada para ARMv7:
# Tag_CPU_arch: v7
# Tag_FP_arch: VFPv3-D16
```

**Corrección**:
```bash
# Recompilación con flags de arquitectura explícitos
bazel clean --expunge
bazel build --copt="-march=armv7-a" --copt="-mcpu=cortex-a53" \
    //mediapipe/python:_framework_bindings
```

## Optimizaciones Avanzadas de Rendimiento

### Reducción de Tamaño Binario

```bash
# Incorporar en .bazelrc.user para optimización de tamaño
build --strip=always
build --copt -fvisibility=hidden
build --copt -fvisibility-inlines-hidden
build --copt -fdata-sections
build --copt -ffunction-sections
build --linkopt -Wl,--gc-sections
```

### Compilación de Módulos Específicos

```python
# Modificación en setup.py para incluir solo módulos necesarios
POSE_GRAPHS = [
    'pose_tracking_cpu',
    # Comentar módulos GPU innecesarios:
    # 'pose_tracking_gpu',
    # 'holistic_tracking_gpu',
]
```

### Utilización de ccache para Aceleración

```bash
# Instalación y configuración de ccache
sudo apt install ccache
export CC="ccache gcc"
export CXX="ccache g++"
export CCACHE_DIR=/tmp/ccache
ccache -M 2G  # Límite de cache de 2GB
```

## Script de Automatización de Compilación

```bash
#!/bin/bash
# compile_mediapipe_arm.sh - Script automatizado de compilación

set -e

# Configuración de parámetros
MEDIAPIPE_VERSION="0.8.8"
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
BUILD_DIR="/tmp/mediapipe_build"
LOG_FILE="$BUILD_DIR/compilation.log"

# Configuración de colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Iniciando compilación de MediaPipe ${MEDIAPIPE_VERSION} para ARM${NC}"

# Verificación de requisitos previos
check_prerequisites() {
    echo "Verificando requisitos previos..."
    
    if [[ $(uname -m) != "armv7l" ]]; then
        echo -e "${RED}Error: Este script está diseñado específicamente para ARMv7${NC}"
        exit 1
    fi
    
    # Verificación de espacio en disco
    AVAILABLE_SPACE=$(df /tmp | tail -1 | awk '{print $4}')
    if [[ $AVAILABLE_SPACE -lt 5000000 ]]; then  # 5GB en KB
        echo -e "${YELLOW}Advertencia: Espacio en disco limitado${NC}"
    fi
    
    # Verificación de memoria
    TOTAL_MEM=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    if [[ $TOTAL_MEM -lt 2000000 ]]; then  # 2GB en KB
        echo -e "${YELLOW}Advertencia: Memoria RAM limitada, compilación será lenta${NC}"
    fi
}

# Preparación del entorno
prepare_environment() {
    echo "Preparando entorno de compilación..."
    
    mkdir -p $BUILD_DIR
    cd ~/mediapipe
    
    # Configuración de variables de entorno optimizadas
    export PYTHON_BIN_PATH=$(which python3)
    export PYTHON_LIB_PATH=$(python3 -c "import site; print(site.getsitepackages()[0])")
    export CC_OPT_FLAGS="-march=armv7-a -mfpu=neon-vfpv4 -mfloat-abi=hard -O3"
    export LDFLAGS="-latomic"
    export CCACHE_DIR=$BUILD_DIR/ccache
    
    # Limpieza de compilaciones anteriores
    bazel clean --expunge 2>/dev/null || true
    rm -rf dist build 2>/dev/null || true
}

# Compilación con reintentos y recuperación
compile_with_retry() {
    local max_attempts=3
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        echo -e "${YELLOW}Intento de compilación $attempt de $max_attempts${NC}"
        
        if python setup.py build_ext 2>&1 | tee -a $LOG_FILE; then
            echo -e "${GREEN}Compilación exitosa en intento $attempt${NC}"
            return 0
        else
            if [[ $attempt -eq $max_attempts ]]; then
                echo -e "${RED}Compilación falló después de $max_attempts intentos${NC}"
                echo "Revisar log en: $LOG_FILE"
                return 1
            fi
            
            echo -e "${YELLOW}Intento $attempt falló, limpiando y reintentando...${NC}"
            bazel clean 2>/dev/null || true
            sleep 5
            attempt=$((attempt + 1))
        fi
    done
}

# Función principal
main() {
    check_prerequisites
    prepare_environment
    
    echo "Generando archivos Protocol Buffers..."
    python setup.py gen_protos 2>&1 | tee -a $LOG_FILE
    
    if compile_with_retry; then
        echo "Creando wheel de distribución..."
        python setup.py bdist_wheel --plat-name linux_armv7l 2>&1 | tee -a $LOG_FILE
        
        # Verificación del wheel generado
        WHEEL_FILE=$(ls dist/mediapipe-*.whl 2>/dev/null | head -1)
        if [[ -f "$WHEEL_FILE" ]]; then
            echo -e "${GREEN}Wheel creado exitosamente: $WHEEL_FILE${NC}"
            echo "Para instalar ejecutar: pip install $WHEEL_FILE"
            
            # Verificación de integridad
            python -m zipfile -l "$WHEEL_FILE" | grep -q "_framework_bindings" && \
                echo -e "${GREEN}Verificación de integridad: OK${NC}" || \
                echo -e "${YELLOW}Advertencia: _framework_bindings no encontrado en wheel${NC}"
        else
            echo -e "${RED}Error: No se encontró el archivo wheel generado${NC}"
            exit 1
        fi
    else
        exit 1
    fi
}

# Ejecución del script principal
main "$@"
```

## Verificación Post-Instalación

### Test Integral de Funcionalidad

```python
# test_mediapipe_arm_complete.py
import mediapipe as mp
import cv2
import numpy as np
import time
import platform

def test_mediapipe_comprehensive():
    """Prueba integral de MediaPipe en ARM"""
    
    print(f"Versión de MediaPipe: {mp.__version__}")
    print(f"Arquitectura del sistema: {platform.machine()}")
    print(f"Plataforma: {platform.platform()}")
    
    # Test 1: Inicialización de Pose
    print("\n1. Probando inicialización de MediaPipe Pose...")
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(
        static_image_mode=False,
        model_complexity=0,  # Modelo lite para ARM
        min_detection_confidence=0.5
    )
    print("✓ MediaPipe Pose inicializado correctamente")
    
    # Test 2: Procesamiento de imagen sintética
    print("\n2. Probando procesamiento de imagen...")
    test_image = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.rectangle(test_image, (200, 100), (400, 400), (255, 255, 255), -1)
    
    start_time = time.time()
    results = pose.process(test_image)
    processing_time = time.time() - start_time
    
    print(f"✓ Imagen procesada en {processing_time*1000:.2f} ms")
    
    # Test 3: Verificación de optimizaciones ARM
    print("\n3. Verificando optimizaciones ARM...")
    import subprocess
    try:
        # Verificar que el binario fue compilado para ARMv7
        result = subprocess.run(['readelf', '-A', mp.__file__], 
                              capture_output=True, text=True)
        if 'Tag_CPU_arch: v7' in result.stdout:
            print("✓ Binario compilado para ARMv7")
        if 'Tag_FP_arch: VFPv4' in result.stdout:
            print("✓ Optimizaciones NEON/VFPv4 habilitadas")
    except:
        print("⚠ No se pudo verificar optimizaciones ARM")
    
    # Test 4: Benchmark de rendimiento
    print("\n4. Ejecutando benchmark de rendimiento...")
    frames_to_process = 50
    total_time = 0
    
    for i in range(frames_to_process):
        # Generar imagen aleatoria
        random_image = np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8)
        
        start = time.time()
        pose.process(random_image)
        total_time += time.time() - start
    
    avg_fps = frames_to_process / total_time
    print(f"✓ FPS promedio: {avg_fps:.2f}")
    
    # Test 5: Verificación de memoria
    print("\n5. Verificando uso de memoria...")
    import psutil
    import os
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024
    print(f"✓ Uso de memoria: {memory_mb:.2f} MB")
    
    pose.close()
    
    # Resumen final
    print(f"\n{'='*50}")
    print("RESUMEN DE VERIFICACIÓN")
    print(f"{'='*50}")
    print(f"Plataforma: {platform.machine()}")
    print(f"MediaPipe: {mp.__version__}")
    print(f"Rendimiento: {avg_fps:.2f} FPS")
    print(f"Memoria: {memory_mb:.2f} MB")
    print(f"Tiempo de procesamiento: {processing_time*1000:.2f} ms/frame")
    
    if avg_fps > 8.0:
        print("✅ Rendimiento EXCELENTE para Raspberry Pi 3")
    elif avg_fps > 5.0:
        print("✅ Rendimiento BUENO para Raspberry Pi 3")
    else:
        print("⚠️ Rendimiento LIMITADO - considerar optimizaciones adicionales")

if __name__ == "__main__":
    test_mediapipe_comprehensive()
```

## Consideraciones de Rendimiento Específicas

### Métricas de Rendimiento Esperadas en RPi 3

| Configuración | FPS Esperados | Latencia Promedio | Uso de CPU |
|---------------|---------------|------------------|------------|
| Modelo Lite (complexity=0) | 8-12 FPS | 80-120 ms | 70-80% |
| Modelo Full (complexity=1) | 3-5 FPS | 200-300 ms | 85-95% |
| Modelo Heavy (complexity=2) | 1-2 FPS | 500-800 ms | 95-100% |

### Recomendaciones de Configuración Óptima

1. **Usar exclusivamente model_complexity=0**: El modelo lite proporciona el mejor balance precisión/rendimiento
2. **Procesar a 320x240 y escalar para display**: Reducción significativa de carga computacional
3. **Implementar skip de frames (1 de cada 2-3)**: Mejora responsividad del sistema
4. **Deshabilitar segmentación**: `enable_segmentation=False` reduce overhead
5. **Usar static_image_mode=False**: Aprovecha tracking temporal para eficiencia

Esta guía proporciona una metodología exhaustiva para la compilación exitosa de MediaPipe en arquitecturas ARM, optimizada específicamente para aplicaciones de investigación en sistemas embebidos y desarrollo de prototipos académicos.