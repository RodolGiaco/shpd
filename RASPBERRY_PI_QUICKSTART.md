# Guía de Inicio Rápido - Implementación en Raspberry Pi 3

## Especificaciones del Hardware Objetivo

### Requerimientos Mínimos del Sistema
- **Plataforma**: Raspberry Pi 3 Model B Plus (ARMv7 32-bit)
- **Sistema Operativo**: Raspberry Pi OS (Buster o versión posterior)
- **Dispositivo de Captura**: Cámara USB o módulo de cámara oficial RPi
- **Almacenamiento**: Tarjeta SD de 16GB (se recomienda 32GB para desarrollo)
- **Conectividad**: Acceso a Internet para descarga de dependencias
- **Tiempo Estimado**: 4-6 horas para compilación completa desde código fuente

## Metodología de Instalación Automatizada

### Procedimiento Estándar (Recomendado)

```bash
# Clonación del repositorio del proyecto
git clone [URL_DEL_REPOSITORIO] SmartHealthyPostureDetector
cd SmartHealthyPostureDetector

# Ejecución del instalador automatizado
./install_rpi.sh
# Seleccionar opción 1 para instalación completa con optimizaciones
```

**Nota Académica**: El script automatizado implementa las mejores prácticas para deployment en sistemas embebidos, incluyendo optimizaciones específicas para la arquitectura ARM y gestión eficiente de recursos limitados.

## Metodología de Instalación Manual (Proceso Detallado)

### Fase 1: Preparación del Entorno del Sistema

```bash
# Incremento del espacio de intercambio (swap) para compilación
sudo nano /etc/dphys-swapfile
# Modificar: CONF_SWAPSIZE=100 → CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

# Actualización completa del sistema operativo
sudo apt update && sudo apt upgrade -y
```

**Justificación Técnica**: El aumento del swap es crítico durante la fase de compilación de MediaPipe, ya que el proceso requiere más memoria RAM de la disponible en el hardware estándar.

### Fase 2: Instalación de Dependencias de OpenCV (Enfoque Expedito)

```bash
# Opción A: Instalación mediante repositorios del sistema (más rápida)
sudo apt install python3-opencv
pip3 install opencv-python==4.5.5.64
```

**Consideración de Rendimiento**: Esta aproximación sacrifica algunas optimizaciones específicas del hardware a cambio de una instalación significativamente más rápida.

### Fase 3: Instalación de MediaPipe para Arquitectura ARM

```bash
# Opción A: Instalación mediante wheel precompilado de la comunidad
pip3 install mediapipe-rpi4==0.8.8
# Fuente alternativa: https://github.com/jiuqiant/mediapipe_python_aarch64
```

**Nota de Compatibilidad**: Los wheels precompilados pueden no estar disponibles para todas las versiones. En caso de fallo, proceder con compilación desde código fuente.

### Fase 4: Compilación de MediaPipe desde Código Fuente (Procedimiento Alternativo)

```bash
# Instalación de Bazel (herramienta de compilación requerida)
wget https://github.com/bazelbuild/bazel/releases/download/3.7.2/bazel-3.7.2-linux-armv7l
chmod +x bazel-3.7.2-linux-armv7l
sudo mv bazel-3.7.2-linux-armv7l /usr/local/bin/bazel

# Clonación y configuración de MediaPipe
git clone https://github.com/google/mediapipe.git
cd mediapipe
git checkout v0.8.8

# Configuración específica para arquitectura ARM
echo "build --define MEDIAPIPE_DISABLE_GPU=1" > .bazelrc.user
echo "build --copt -march=armv7-a" >> .bazelrc.user

# Proceso de compilación
python3 setup.py gen_protos
python3 setup.py bdist_wheel
pip3 install dist/*.whl
```

### Fase 5: Configuración del Proyecto

```bash
# Navegación al directorio del proyecto
cd ~/SmartHealthyPostureDetector

# Instalación de dependencias restantes
pip3 install tflite-runtime requests numpy

# Creación de configuración optimizada para Raspberry Pi
cp config_pose.json config_pose_rpi.json
```

**Modificaciones de Configuración Recomendadas**:
```json
{
  "constants": {
    "pose": {
      "model_complexity": 0,
      "min_pose_detection_confidence": 0.3
    }
  }
}
```

## Ejecución del Sistema

### Modalidades de Operación

#### Versión Optimizada para Raspberry Pi (Recomendada)
```bash
python3 main_rpi.py
```

#### Versión Estándar (Rendimiento Reducido)
```bash
python3 main.py
```

**Análisis Comparativo**: La versión optimizada implementa técnicas específicas de reducción de carga computacional, incluyendo salto de frames y simplificación de modelos.

## Optimizaciones de Rendimiento

### Configuración de Parámetros de Procesamiento

#### Reducción de Resolución de Procesamiento
Modificar `config_pose_rpi.json`:
```json
{
  "rpi_optimizations": {
    "processing_resolution": [320, 240],
    "camera_resolution": [640, 480],
    "frame_skip": 2
  }
}
```

#### Utilización del Modelo de Complejidad Mínima
```python
# En configuración o código directo
model_complexity=0  # Siempre utilizar modelo lite en Raspberry Pi
```

#### Deshabilitación de Características No Esenciales
```python
enable_segmentation=False    # Reducir carga computacional
smooth_landmarks=False       # Eliminar suavizado innecesario
```

## Diagnóstico y Solución de Problemas

### Problemas Frecuentes y Sus Soluciones

#### Error de Detección de Cámara
```bash
# Habilitación de la interfaz de cámara
sudo raspi-config
# Navegar: Interfacing Options → Camera → Enable

# Verificación del estado de la cámara
vcgencmd get_camera
# Salida esperada: supported=1 detected=1
```

#### Gestión de Memoria Insuficiente
```bash
# Configuración de variables de entorno para optimización
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
```

#### Optimización de FPS Bajos
**Estrategias de Implementación**:
- Utilizar `main_rpi.py` en lugar de `main.py`
- Incrementar `frame_skip` a 3 o 4 para procesamiento cada 3-4 frames
- Reducir resolución de procesamiento a 160x120 para casos críticos

#### Resolución de Errores de Importación
```bash
# Configuración de variables de entorno Python
export PYTHONPATH="${PYTHONPATH}:/usr/local/lib/python3.9/site-packages"
echo 'export PYTHONPATH="${PYTHONPATH}:/usr/local/lib/python3.9/site-packages"' >> ~/.bashrc
source ~/.bashrc
```

## Análisis de Rendimiento Esperado

### Métricas de Rendimiento por Configuración

| Configuración del Sistema | FPS Esperados | Uso de CPU | Latencia |
|---------------------------|---------------|------------|----------|
| Modelo Lite + 320x240     | 8-12 FPS      | 70-80%     | ~80ms    |
| Modelo Lite + 160x120     | 12-15 FPS     | 60-70%     | ~60ms    |
| Frame Skip 2              | +30% FPS      | Reducido   | Variable |
| Frame Skip 3              | +50% FPS      | Reducido   | Variable |

### Recomendaciones de Optimización Adicionales

1. **Selección del Dispositivo de Captura**: Preferir cámaras USB sobre el módulo CSI para mejor compatibilidad
2. **Gestión Térmica**: Implementar disipadores de calor o ventilación para mantener rendimiento sostenido
3. **Overclocking Moderado**: Puede proporcionar mejoras de rendimiento del 10-15% en FPS
4. **Minimización de GUI**: Deshabilitar ventanas innecesarias para maximizar recursos de procesamiento
5. **Procesamiento en Segundo Plano**: Eliminar visualización para aplicaciones de producción

## Verificación de la Instalación

### Protocolo de Validación del Sistema

```bash
# Verificación de bibliotecas principales
python3 -c "import cv2; print('OpenCV:', cv2.__version__)"
python3 -c "import mediapipe; print('MediaPipe:', mediapipe.__version__)"
python3 -c "import tflite_runtime.interpreter; print('TensorFlow Lite: Operativo')"
```

**Salida Esperada**:
```
OpenCV: 4.5.5
MediaPipe: 0.8.8
TensorFlow Lite: Operativo
```

## Consideraciones para Trabajo Futuro

### Limitaciones Identificadas
- **Throughput de FPS**: Limitado por capacidad de procesamiento del hardware
- **Resolución de Procesamiento**: Compromiso entre calidad y velocidad
- **Latencia del Sistema**: Dependiente de la complejidad del modelo seleccionado

### Sugerencias de Mejora
- **Implementación de Edge TPU**: Para aceleración de inferencia de ML
- **Optimización de Pipeline**: Mediante técnicas de paralelización
- **Modelos Cuantizados**: Reducción de precisión para mayor velocidad

## Referencia a Documentación Extendida

Para información detallada sobre procedimientos de instalación y compilación, consultar:
- **[RASPBERRY_PI_INSTALLATION.md](RASPBERRY_PI_INSTALLATION.md)** - Procedimientos completos de instalación
- **[MEDIAPIPE_ARM_COMPILATION.md](MEDIAPIPE_ARM_COMPILATION.md)** - Guía detallada de compilación para ARM

Esta guía proporciona un enfoque sistemático para la implementación eficiente del sistema en plataformas de recursos limitados, optimizado para aplicaciones de investigación y desarrollo en el campo de la visión artificial.