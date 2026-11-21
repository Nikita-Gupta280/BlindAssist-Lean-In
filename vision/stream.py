
import cv2
import threading
import time


class CameraStream:

    def __init__(self, source=0):
        self.source = source
        self.frame = None
        self.lock = threading.Lock()
        self.running = False
        self.thread = None
        self.start_lock = threading.Lock()

    def start(self):
        with self.start_lock:
            if self.running and self.thread and self.thread.is_alive():
                return self

            self.running = True

            self.thread = threading.Thread(
                target=self.update,
                daemon=True
            )

            self.thread.start()

        return self

    def update(self):

        while self.running:
            cap = None

            # Try DirectShow first, then Media Foundation.
            backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF]

            for backend in backends:
                if not self.running:
                    break

                try:
                    camera = cv2.VideoCapture(self.source, backend)

                    if camera.isOpened():
                        cap = camera
                        break

                    camera.release()

                except Exception as error:
                    print(f"Camera opening error: {error}")

            if cap is None or not cap.isOpened():
                print("Camera unavailable. Retrying...")
                if cap is not None:
                    cap.release()
                time.sleep(2)
                continue

            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 30)

            print("Camera connected!")

            while self.running:
                success, frame = cap.read()

                if not success or frame is None:
                    print("Camera disconnected. Reconnecting...")
                    break

                with self.lock:
                    self.frame = frame

            cap.release()
            time.sleep(1)

        print("Camera capture thread ended.")

    def get_frame(self):
        with self.lock:
            if self.frame is None:
                return None

            return self.frame.copy()

    def stop(self):
        self.running = False

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=3)

        with self.lock:
            self.frame = None

        print("Camera stopped.")
