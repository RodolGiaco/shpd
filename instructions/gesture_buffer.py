from collections import deque
from collections import Counter

class GestureBuffer:
    def __init__(self, buffer_len=10):
        self.buffer_len = buffer_len
        self._buffer = deque(maxlen=buffer_len)

    def add_gesture(self, gesture_id):
        self._buffer.append(gesture_id)

    def get_gesture(self):
        counter = Counter(self._buffer).most_common()
        if counter[0][1] >= (self.buffer_len - 1):
            self._buffer.clear()
            return counter[0][0]
        else:
            return