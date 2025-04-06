import cv2 as cv
import numpy as np
import json
from mp_utils import pose_posture
from neural_network import pose_recognition
from instructions import gesture_instructions
from instructions import gesture_buffer
from gui import ThirdPersonGUI  # Importa la clase ThirdPersonGUI desde gui

def main():
    with open('config_pose.json', 'r') as config_file:
        config = json.load(config_file)
    
    # Configuración de valores predeterminados si faltan
    pose_tracking_confidence = config['constants']['pose'].get('min_pose_tracking_confidence', 0.5)
    pose_presence_confidence = config['constants']['pose'].get('min_pose_presence_confidence', 0.5)

    # Inicializa ThirdPersonGUI desde gui.py
    tp_gui = ThirdPersonGUI(config['constants']['gui']['hand_window_height'], config['constants']['gui']['hand_window_width'])

    cap = cv.VideoCapture(0)
    if not cap.isOpened():
        print("Error: No se pudo abrir la cámara")
        return

    # Inicialización del detector de pose (torso)
    pose_detection = pose_posture.PoseDetection(
        min_pose_detection_confidence=config['constants']['pose']['min_pose_detection_confidence'],
        min_pose_presence_confidence=pose_presence_confidence,
        min_pose_tracking_confidence=pose_tracking_confidence
    )

    # Inicialización del reconocedor de gestos
    pose_recognizer = pose_recognition.PoseRecognizer(
        model_path=config['model_paths']['pose_recogniser'],
        label_path=config['model_paths']['keypoint_classifier_labels']
    )

    # Inicialización del buffer de gestos
    buffer = gesture_buffer.GestureBuffer(buffer_len=config['constants']['buffer_length'])

    # Inicialización de las instrucciones
    instructions = gesture_instructions.Instructions(
        following=config['initial_options']['following'],
        speed=config['constants']['speed']
    )

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: No se pudo capturar la imagen")
            break


        pose_result = pose_detection.extract_pose(frame)
        main_window_image = pose_detection.draw_pose(frame)


        # Reconocimiento de gestos
        gesture_id, _ = pose_recognizer.recognize_pose(pose_result, frame)
        gesture_name = pose_recognizer.translate_gesture_id_to_name(buffer.get_gesture())
        buffer.add_gesture(gesture_id)
        gesture = buffer.get_gesture()
        # type_move, move = instructions.calculate_move(gesture, pose_result, frame)
        
        #instructions.send_telegram_message(gesture)

        tp_gui.update_camera_window(main_window_image)
        # tp_gui.update_info_window(instructions.get_follow_state(), move, 100, gesture_name)
        tp_gui.show_window()

        # Mover ventanas para que no se encimen
        cv.moveWindow("ThirdPerson", 0, 0)  # Ventana principal en la esquina superior izquierda
        cv.moveWindow("Info", 640, 0)       # Ventana de información a la derecha de la principal
        cv.moveWindow("hand", 640, 360)     # Ventana de mano debajo de la ventana de información

        key = tp_gui.getKey()
        if key == ord('q'):
            break

    cap.release()
    pose_detection.close()
    tp_gui.close()

if __name__ == "__main__":
    main()
