
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

    def start(self):
        self.running = True

        self.thread = threading.Thread(
            target=self.update,
            daemon=True
        )

        self.thread.start()

        print("Camera initialization thread started.")

        return self

    def update(self):

        first_frame = True

        while self.running:

            camera_start = time.perf_counter()

            cap = cv2.VideoCapture(self.source)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 30)

            if not cap.isOpened():
                print("Camera unavailable. Retrying...")
                cap.release()
                time.sleep(2)
                continue

            print(
                f"Camera connected in "
                f"{time.perf_counter() - camera_start:.2f} seconds"
            )

            while self.running:

                success, frame = cap.read()

                if not success:
                    print("Camera disconnected.")
                    break

                with self.lock:
                    self.frame = frame

                if first_frame:
                    print(
                        f"First camera frame received in "
                        f"{time.perf_counter() - camera_start:.2f} seconds"
                    )
                    first_frame = False

            cap.release()
            time.sleep(2)

    def get_frame(self):

        with self.lock:
            if self.frame is None:
                return None

            return self.frame.copy()

    def stop(self):
        self.running = False

        if self.thread:
            self.thread.join(timeout=3)

        print("Camera stopped.")
