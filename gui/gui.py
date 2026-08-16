
import cv2 as cv
import numpy as np

class PostureGUI():

    def __init__(self) -> None:
        self.camera_window = None
        self.key = None

    def close(self):
        cv.destroyAllWindows()

    def update_camera_window(self, camera_window_image):
        self.camera_window = camera_window_image

    def draw_posture_label(self, gesture_name):
        """Dibuja el nombre de la postura detectada como una franja semitransparente
        en la parte inferior del propio frame de la cámara (sin ventana aparte).
        El tamaño de letra se ajusta solo para que el texto nunca se corte."""
        if self.camera_window is None:
            return

        frame = self.camera_window
        height, width = frame.shape[:2]
        text = gesture_name if gesture_name else "Sin postura detectada"

        font = cv.FONT_HERSHEY_SIMPLEX
        thickness = 2
        font_scale = 0.9
        margin = 24
        (text_w, text_h), _ = cv.getTextSize(text, font, font_scale, thickness)
        while text_w > width - margin * 2 and font_scale > 0.4:
            font_scale -= 0.1
            (text_w, text_h), _ = cv.getTextSize(text, font, font_scale, thickness)

        bar_height = text_h + 30
        overlay = frame.copy()
        cv.rectangle(overlay, (0, height - bar_height), (width, height), (0, 0, 0), -1)
        cv.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

        text_x = (width - text_w) // 2
        text_y = height - (bar_height - text_h) // 2
        cv.putText(frame, text, (text_x, text_y), font, font_scale, (255, 255, 255), thickness, cv.LINE_AA)

    def show_window(self):
        cv.imshow("Postura", self.camera_window)
        self.key = cv.waitKey(1)

    def getKey(self):
        return self.key
