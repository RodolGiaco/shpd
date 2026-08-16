import cv2 as cv
import numpy as np
import json
from mp_utils import pose_posture
from neural_network import pose_recognition
from instructions import gesture_instructions  
from instructions import gesture_buffer
from gui import PostureGUI  # Importa la clase PostureGUI desde gui

def main():
    with open('config_pose.json', 'r') as config_file:
        config = json.load(config_file)
    
    # Configuración de valores predeterminados si faltan
    pose_tracking_confidence = config['constants']['pose'].get('min_pose_tracking_confidence', 0.5)

    # Inicializa PostureGUI desde gui.py
    posture_gui = PostureGUI()

    cap = cv.VideoCapture(0)
    if not cap.isOpened():
        print("Error: No se pudo abrir la cámara")
        return

     # Inicialización del detector de pose (torso)
    pose_detection = pose_posture.PoseDetectionPosture(
        min_pose_detection_confidence=config['constants']['pose']['min_pose_detection_confidence'],
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

        #instructions.send_telegram_message(gesture)

        posture_gui.update_camera_window(main_window_image)
        posture_gui.draw_posture_label(gesture_name)
        posture_gui.show_window()

        cv.moveWindow("Postura", 0, 0)

        key = posture_gui.getKey()
        if key == ord('q'):
            break

    cap.release()
    pose_detection.close()
    posture_gui.close()

if __name__ == "__main__":
    main()