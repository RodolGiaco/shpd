# -*- coding: utf-8 -*-
"""
Main optimizado para Raspberry Pi 3 Model B Plus
Versión con optimizaciones de rendimiento para ARMv7
"""
import cv2 as cv
import numpy as np
import json
import os
import time
from mp_utils import pose_posture
from neural_network import pose_recognition
from instructions import gesture_instructions
from instructions import gesture_buffer
from gui import PostureGUI

# Configuración específica para Raspberry Pi
os.environ['OPENCV_VIDEOIO_PRIORITY_MSMF'] = '0'

class FrameSkipper:
    """Clase para implementar frame skipping"""
    def __init__(self, skip_frames=2):
        self.skip_frames = skip_frames
        self.frame_count = 0
    
    def should_process(self):
        self.frame_count += 1
        return self.frame_count % (self.skip_frames + 1) == 0

class PerformanceMonitor:
    """Monitor de rendimiento para debugging"""
    def __init__(self, window_size=30):
        self.window_size = window_size
        self.frame_times = []
        self.last_time = time.time()
    
    def tick(self):
        current_time = time.time()
        delta = current_time - self.last_time
        self.last_time = current_time
        
        self.frame_times.append(delta)
        if len(self.frame_times) > self.window_size:
            self.frame_times.pop(0)
    
    def get_fps(self):
        if not self.frame_times:
            return 0
        avg_time = sum(self.frame_times) / len(self.frame_times)
        return 1.0 / avg_time if avg_time > 0 else 0

def load_rpi_config():
    """Carga configuración optimizada para RPi"""
    # Intentar cargar config específica de RPi primero
    config_files = ['config_pose_rpi.json', 'config_pose.json']
    
    for config_file in config_files:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
                print(f"Configuración cargada desde: {config_file}")
                return config
    
    # Configuración por defecto optimizada para RPi
    print("Usando configuración por defecto para RPi")
    return {
        'constants': {
            'pose': {
                'min_pose_detection_confidence': 0.3,
                'min_pose_tracking_confidence': 0.3,
                'min_pose_presence_confidence': 0.3
            },
            'buffer_length': 10,
            'speed': 40
        },
        'model_paths': {
            'pose_recogniser': 'model/keypoint_classifier.tflite',
            'keypoint_classifier_labels': 'model/keypoint_classifier_label.csv'
        },
        'initial_options': {
            'following': False
        },
        'rpi_optimizations': {
            'model_complexity': 0,
            'enable_segmentation': False,
            'smooth_landmarks': False,
            'frame_skip': 2,
            'camera_resolution': [640, 480],
            'camera_fps': 15,
            'processing_resolution': [320, 240]
        }
    }

def initialize_camera(config):
    """Inicializa la cámara con configuración optimizada"""
    rpi_opts = config.get('rpi_optimizations', {})
    resolution = rpi_opts.get('camera_resolution', [640, 480])
    fps = rpi_opts.get('camera_fps', 15)
    
    # Intentar con diferentes backends
    backends = [cv.CAP_V4L2, cv.CAP_ANY]
    
    for backend in backends:
        cap = cv.VideoCapture(0, backend)
        if cap.isOpened():
            print(f"Cámara abierta con backend: {backend}")
            break
    
    if not cap.isOpened():
        print("Error: No se pudo abrir la cámara")
        return None
    
    # Configurar cámara
    cap.set(cv.CAP_PROP_FRAME_WIDTH, resolution[0])
    cap.set(cv.CAP_PROP_FRAME_HEIGHT, resolution[1])
    cap.set(cv.CAP_PROP_FPS, fps)
    cap.set(cv.CAP_PROP_BUFFERSIZE, 1)  # Reducir buffer para menor latencia
    
    # Verificar configuración
    actual_width = cap.get(cv.CAP_PROP_FRAME_WIDTH)
    actual_height = cap.get(cv.CAP_PROP_FRAME_HEIGHT)
    actual_fps = cap.get(cv.CAP_PROP_FPS)
    
    print(f"Cámara configurada: {actual_width}x{actual_height} @ {actual_fps} FPS")
    
    return cap

def process_frame_for_display(frame, processing_resolution):
    """Redimensiona frame para procesamiento"""
    if processing_resolution:
        return cv.resize(frame, tuple(processing_resolution))
    return frame

def main():
    # Limpiar logs anteriores
    open('landmark_log.txt', 'w').close()
    
    # Cargar configuración
    config = load_rpi_config()
    rpi_opts = config.get('rpi_optimizations', {})
    
    # Configuración de valores
    pose_detection_confidence = config['constants']['pose'].get('min_pose_detection_confidence', 0.3)
    pose_tracking_confidence = config['constants']['pose'].get('min_pose_tracking_confidence', 0.3)
    pose_presence_confidence = config['constants']['pose'].get('min_pose_presence_confidence', 0.3)
    
    # Inicializar componentes
    print("Inicializando componentes...")
    
    # GUI simplificada
    posture_gui = PostureGUI()
    
    # Inicializar cámara
    cap = initialize_camera(config)
    if not cap:
        return
    
    # Detector de pose optimizado para RPi
    pose_detection = pose_posture.PoseDetectionPosture(
        static_image_mode=False,  # Importante para tracking
        model_complexity=rpi_opts.get('model_complexity', 0),  # Modelo lite
        min_pose_detection_confidence=pose_detection_confidence,
        min_pose_tracking_confidence=pose_tracking_confidence
    )
    
    # Reconocedor de gestos
    pose_recognizer = pose_recognition.PoseRecognizer(
        model_path=config['model_paths']['pose_recogniser'],
        label_path=config['model_paths']['keypoint_classifier_labels']
    )
    
    # Buffer de gestos
    buffer = gesture_buffer.GestureBuffer(
        buffer_len=config['constants']['buffer_length']
    )
    
    # Instrucciones
    instructions = gesture_instructions.Instructions(
        following=config['initial_options']['following'],
        speed=config['constants']['speed']
    )
    
    # Frame skipper
    frame_skipper = FrameSkipper(skip_frames=rpi_opts.get('frame_skip', 2))
    
    # Monitor de rendimiento
    perf_monitor = PerformanceMonitor()
    
    # Variables para procesamiento
    processing_resolution = rpi_opts.get('processing_resolution', [320, 240])
    last_results = None
    last_gesture_id = -1
    frame_count = 0
    
    print("Sistema iniciado. Presiona 'q' para salir.")
    
    try:
        while True:
            # Capturar frame
            ret, frame = cap.read()
            if not ret:
                print("Error: No se pudo capturar la imagen")
                break
            
            frame_count += 1
            perf_monitor.tick()
            
            # Procesar solo algunos frames
            if frame_skipper.should_process():
                # Redimensionar para procesamiento
                process_frame = process_frame_for_display(frame, processing_resolution)
                
                # Detectar pose
                pose_result = pose_detection.extract_pose(process_frame)
                
                if pose_result and pose_result.pose_landmarks:
                    last_results = pose_result
                    
                    # Reconocer gesto
                    gesture_id, _ = pose_recognizer.recognize_pose(pose_result, process_frame)
                    if gesture_id != -1:
                        last_gesture_id = gesture_id
                        buffer.add_gesture(gesture_id)
            
            # Usar últimos resultados para dibujar (más fluido)
            if last_results:
                # Dibujar en frame original (mayor resolución)
                main_window_image = pose_detection.draw_pose(frame)
            else:
                main_window_image = frame
            
            # Obtener gesto estable
            stable_gesture = buffer.get_gesture()
            gesture_name = pose_recognizer.translate_gesture_id_to_name(stable_gesture)
            
            # Mostrar FPS en la imagen
            fps = perf_monitor.get_fps()
            cv.putText(main_window_image, f"FPS: {fps:.1f}", (10, 30), 
                      cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Actualizar GUI
            posture_gui.update_camera_window(main_window_image)
            posture_gui.draw_posture_label(gesture_name)
            posture_gui.show_window()

            # Posicionar ventana
            cv.moveWindow("Postura", 0, 0)
            
            # Verificar tecla
            key = posture_gui.getKey()
            if key == ord('q'):
                break
            elif key == ord('r'):  # Reset buffer
                buffer = gesture_buffer.GestureBuffer(
                    buffer_len=config['constants']['buffer_length']
                )
                print("Buffer reiniciado")
            elif key == ord('f'):  # Toggle following
                instructions.follow_behaviour = not instructions.follow_behaviour
                print(f"Following: {instructions.follow_behaviour}")
            
            # Limitar FPS si es necesario
            if fps > rpi_opts.get('camera_fps', 15) * 1.5:
                time.sleep(0.01)
    
    except KeyboardInterrupt:
        print("\nInterrumpido por el usuario")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Limpieza
        print("Cerrando aplicación...")
        cap.release()
        pose_detection.close()
        posture_gui.close()
        print("Aplicación cerrada correctamente")

if __name__ == "__main__":
    main()