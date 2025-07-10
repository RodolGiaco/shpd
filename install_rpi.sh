#!/bin/bash
# Script de instalación automatizada para SmartHealthyPostureDetector en Raspberry Pi 3
# Versión: 1.0
# Compatibilidad: Raspberry Pi 3 Model B Plus Rev 1.3 (ARMv7 32-bit)

set -e  # Salir si hay errores

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables de configuración
OPENCV_VERSION="4.5.5"
MEDIAPIPE_VERSION="0.8.8"
BAZEL_VERSION="3.7.2"
PYTHON_VERSION="3.9"
SWAP_SIZE="2048"
GPU_MEMORY="128"

# Función para imprimir mensajes
print_msg() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[ADVERTENCIA]${NC} $1"
}

# Verificar que estamos en Raspberry Pi
check_raspberry_pi() {
    if ! grep -q "Raspberry Pi" /proc/cpuinfo; then
        print_error "Este script solo es compatible con Raspberry Pi"
        exit 1
    fi
    print_msg "Raspberry Pi detectada"
}

# Configurar swap
configure_swap() {
    print_msg "Configurando swap a ${SWAP_SIZE}MB..."
    sudo dphys-swapfile swapoff
    sudo sed -i "s/CONF_SWAPSIZE=.*/CONF_SWAPSIZE=$SWAP_SIZE/" /etc/dphys-swapfile
    sudo dphys-swapfile setup
    sudo dphys-swapfile swapon
    print_msg "Swap configurado correctamente"
}

# Actualizar sistema
update_system() {
    print_msg "Actualizando sistema..."
    sudo apt update
    sudo apt upgrade -y
    sudo apt dist-upgrade -y
    print_msg "Sistema actualizado"
}

# Instalar dependencias base
install_base_dependencies() {
    print_msg "Instalando dependencias base..."
    
    # Herramientas de compilación
    sudo apt install -y \
        build-essential cmake git pkg-config \
        gcc g++ make automake \
        python3-dev python3-pip python3-venv \
        wget unzip curl
    
    # Bibliotecas para OpenCV
    sudo apt install -y \
        libjpeg-dev libtiff5-dev libjasper-dev libpng-dev \
        libavcodec-dev libavformat-dev libswscale-dev libv4l-dev \
        libxvidcore-dev libx264-dev \
        libfontconfig1-dev libcairo2-dev \
        libgdk-pixbuf2.0-dev libpango1.0-dev \
        libgtk2.0-dev libgtk-3-dev \
        libatlas-base-dev gfortran \
        libhdf5-dev libhdf5-serial-dev \
        libilmbase-dev libopenexr-dev libgstreamer1.0-dev \
        libwebp-dev libopenblas-dev liblapack-dev \
        libprotobuf-dev protobuf-compiler
    
    print_msg "Dependencias base instaladas"
}

# Crear entorno virtual
create_virtual_env() {
    print_msg "Creando entorno virtual..."
    cd ~
    python3 -m venv pose_env
    source pose_env/bin/activate
    pip install --upgrade pip setuptools wheel
    print_msg "Entorno virtual creado"
}

# Compilar OpenCV
compile_opencv() {
    print_msg "Iniciando compilación de OpenCV ${OPENCV_VERSION}..."
    
    cd ~
    
    # Descargar OpenCV
    if [ ! -d "opencv" ]; then
        wget -O opencv.zip https://github.com/opencv/opencv/archive/${OPENCV_VERSION}.zip
        wget -O opencv_contrib.zip https://github.com/opencv/opencv_contrib/archive/${OPENCV_VERSION}.zip
        unzip opencv.zip
        unzip opencv_contrib.zip
        mv opencv-${OPENCV_VERSION} opencv
        mv opencv_contrib-${OPENCV_VERSION} opencv_contrib
    fi
    
    cd opencv
    mkdir -p build
    cd build
    
    # Configurar compilación
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
        -D OPENCV_PYTHON3_INSTALL_PATH=~/pose_env/lib/python${PYTHON_VERSION}/site-packages \
        -D PYTHON_EXECUTABLE=~/pose_env/bin/python3 \
        ..
    
    # Compilar
    print_msg "Compilando OpenCV (esto tomará 2-3 horas)..."
    make -j2
    
    # Instalar
    sudo make install
    sudo ldconfig
    
    print_msg "OpenCV instalado correctamente"
}

# Instalar Bazel
install_bazel() {
    print_msg "Instalando Bazel ${BAZEL_VERSION}..."
    
    cd ~
    # Corrección: usar versión armhf para ARMv7
    wget https://github.com/bazelbuild/bazel/releases/download/${BAZEL_VERSION}/bazel-${BAZEL_VERSION}-linux-armv7l
    chmod +x bazel-${BAZEL_VERSION}-linux-armv7l
    sudo mv bazel-${BAZEL_VERSION}-linux-armv7l /usr/local/bin/bazel
    
    print_msg "Bazel instalado"
}

# Compilar MediaPipe
compile_mediapipe() {
    print_msg "Iniciando compilación de MediaPipe ${MEDIAPIPE_VERSION}..."
    
    cd ~
    
    # Clonar MediaPipe
    if [ ! -d "mediapipe" ]; then
        git clone https://github.com/google/mediapipe.git
        cd mediapipe
        git checkout v${MEDIAPIPE_VERSION}
    else
        cd mediapipe
    fi
    
    # Configurar para ARM
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
    
    # Instalar dependencias Python
    source ~/pose_env/bin/activate
    pip install numpy==1.19.5
    pip install attrs>=19.1.0
    pip install absl-py
    pip install matplotlib
    
    # Compilar wheel
    print_msg "Compilando MediaPipe Python wheel..."
    python setup.py gen_protos
    python setup.py bdist_wheel
    
    # Instalar
    pip install dist/mediapipe-${MEDIAPIPE_VERSION}-cp39-cp39-linux_armv7l.whl
    
    print_msg "MediaPipe instalado correctamente"
}

# Instalar TensorFlow Lite
install_tflite() {
    print_msg "Instalando TensorFlow Lite Runtime..."
    
    source ~/pose_env/bin/activate
    
    # Intentar instalar desde wheel precompilado
    pip install https://github.com/google-coral/pycoral/releases/download/v2.0.0/tflite_runtime-2.5.0.post1-cp39-cp39-linux_armv7l.whl || {
        print_warning "Instalación desde wheel falló, compilando desde fuente..."
        
        cd ~
        git clone https://github.com/tensorflow/tensorflow.git
        cd tensorflow
        git checkout v2.5.0
        ./tensorflow/lite/tools/pip_package/build_pip_package_with_cmake.sh
        pip install tensorflow/lite/tools/pip_package/gen/tflite_pip/python3/dist/tflite_runtime-2.5.0-cp39-cp39-linux_armv7l.whl
    }
    
    print_msg "TensorFlow Lite instalado"
}

# Configurar proyecto
setup_project() {
    print_msg "Configurando proyecto..."
    
    cd ~
    
    # Clonar repositorio (reemplazar con URL real)
    if [ ! -d "SmartHealthyPostureDetector" ]; then
        print_warning "Por favor, clona el repositorio manualmente:"
        print_warning "git clone [URL_DEL_REPOSITORIO] SmartHealthyPostureDetector"
        return
    fi
    
    cd SmartHealthyPostureDetector
    
    # Activar entorno virtual
    source ~/pose_env/bin/activate
    
    # Instalar dependencias restantes
    pip install requests
    
    # Crear configuración optimizada para RPi
    create_rpi_config
    
    # Crear script de prueba
    create_test_script
    
    print_msg "Proyecto configurado"
}

# Crear configuración para RPi
create_rpi_config() {
    cat > config_pose_rpi.json << 'EOF'
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
}

# Crear script de prueba
create_test_script() {
    cat > test_installation.py << 'EOF'
#!/usr/bin/env python3
import sys
import importlib

def test_import(module_name):
    try:
        module = importlib.import_module(module_name)
        version = getattr(module, '__version__', 'N/A')
        print(f"✓ {module_name} {version}")
        return True
    except ImportError as e:
        print(f"✗ {module_name}: {e}")
        return False

print("Verificando instalación...")
print("-" * 40)

modules = ['cv2', 'mediapipe', 'numpy', 'tflite_runtime.interpreter']
success = all(test_import(mod) for mod in modules)

if success:
    print("\n✓ Todas las dependencias instaladas correctamente")
else:
    print("\n✗ Algunas dependencias faltan")
    sys.exit(1)

# Test de cámara
try:
    import cv2
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    if ret:
        print("✓ Cámara funcionando")
    else:
        print("✗ Cámara no detectada")
except Exception as e:
    print(f"✗ Error al probar cámara: {e}")
EOF
    chmod +x test_installation.py
}

# Configurar inicio automático
setup_autostart() {
    print_msg "Configurando inicio automático..."
    
    # Crear script de inicio
    cat > ~/start_pose_detector.sh << 'EOF'
#!/bin/bash
cd ~/SmartHealthyPostureDetector
source ~/pose_env/bin/activate
export DISPLAY=:0
python main.py
EOF
    chmod +x ~/start_pose_detector.sh
    
    # Crear entrada de autostart
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
    
    print_msg "Inicio automático configurado"
}

# Menú principal
main_menu() {
    echo "================================================"
    echo "Instalador de SmartHealthyPostureDetector"
    echo "Para Raspberry Pi 3 Model B Plus"
    echo "================================================"
    echo ""
    echo "Seleccione una opción:"
    echo "1) Instalación completa"
    echo "2) Solo preparar sistema"
    echo "3) Solo compilar OpenCV"
    echo "4) Solo compilar MediaPipe"
    echo "5) Solo instalar TensorFlow Lite"
    echo "6) Configurar proyecto"
    echo "7) Verificar instalación"
    echo "8) Salir"
    echo ""
    read -p "Opción: " choice
    
    case $choice in
        1)
            full_installation
            ;;
        2)
            prepare_system
            ;;
        3)
            source ~/pose_env/bin/activate
            compile_opencv
            ;;
        4)
            source ~/pose_env/bin/activate
            compile_mediapipe
            ;;
        5)
            source ~/pose_env/bin/activate
            install_tflite
            ;;
        6)
            setup_project
            ;;
        7)
            verify_installation
            ;;
        8)
            exit 0
            ;;
        *)
            print_error "Opción inválida"
            main_menu
            ;;
    esac
}

# Instalación completa
full_installation() {
    print_msg "Iniciando instalación completa..."
    
    check_raspberry_pi
    configure_swap
    update_system
    install_base_dependencies
    create_virtual_env
    
    source ~/pose_env/bin/activate
    
    compile_opencv
    install_bazel
    compile_mediapipe
    install_tflite
    setup_project
    setup_autostart
    
    print_msg "¡Instalación completa!"
    verify_installation
}

# Preparar sistema
prepare_system() {
    check_raspberry_pi
    configure_swap
    update_system
    install_base_dependencies
    create_virtual_env
}

# Verificar instalación
verify_installation() {
    print_msg "Verificando instalación..."
    
    if [ -f ~/SmartHealthyPostureDetector/test_installation.py ]; then
        cd ~/SmartHealthyPostureDetector
        source ~/pose_env/bin/activate
        python test_installation.py
    else
        print_error "Script de verificación no encontrado"
    fi
}

# Ejecutar menú principal
main_menu