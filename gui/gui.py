
import cv2 as cv
import numpy as np

class ThirdPersonGUI():

    def __init__(self, hand_window_height, hand_window_width) -> None:
        self.hand_window = None
        self.camera_window = None
        self.info_window = None
        self.key = None
        self.hand_window_height = hand_window_height
        self.hand_window_width = hand_window_width

    def close(self):
        cv.destroyAllWindows()

    def show_window(self):
        cv.imshow("ThirdPerson", self.camera_window)
        cv.imshow("Info", self.info_window)
   	 # if self.hand_window is not None:
   	 #     cv.imshow("hand", self.hand_window)
        self.key = cv.waitKey(1)




    def getKey(self):
        return self.key

    def landing(self):
        cv.putText(self.camera_window, "Landing...", (300, 400), cv.FONT_HERSHEY_SIMPLEX, 3, (200, 0, 0), 2)

    def update_hand_window(self, hand_window_image):
        self.hand_window = hand_window_image
    
    def update_camera_window(self, camera_window_image):
        self.camera_window = camera_window_image
    
    def overlay_text_on_rect(self, frame, text, rect_position, text_position, font_scale=1, color=(255, 255, 255), thickness=2):
        rect_width = 300
        rect_height = 200
        rect_end_x = rect_position[0] + rect_width
        rect_end_y = rect_position[1] + rect_height
        cv.rectangle(frame, rect_position, (rect_end_x, rect_end_y), (0, 0, 0), -1)
        cv.putText(frame, str(text), text_position, cv.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness, cv.LINE_AA)

    def update_info_window(self, follow_state, move, battery, gesture_name):
        height, width, _ = self.camera_window.shape
        self.info_window = np.zeros((400, 300, 3), dtype=np.uint8)
        if follow_state:
            self.overlay_text_on_rect(self.info_window, 'Following', (20, 20), (30, 60))
        else:
            self.overlay_text_on_rect(self.info_window, 'Not following', (20, 20), (30, 60))
        self.overlay_text_on_rect(self.info_window, move, (20, 80), (30, 120))
        self.overlay_text_on_rect(self.info_window, f'{battery}%', (20, 140), (30, 180))
        self.overlay_text_on_rect(self.info_window, gesture_name, (20, 200), (30, 240))
