
import cv2
import threading
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from config import CAMERA_SOURCE
from vision.stream import CameraStream
from vision.detector import ObjectDetector

app = FastAPI(title="Blind Assist API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

state = {
    "running": False,
    "status": "Stopped",
    "error": None,
    "detections": [],
    "frame": None,
}

lock = threading.Lock()
stop_event = threading.Event()
camera = None
detector = None


def detection_worker():
    global camera, detector

    try:
        camera = CameraStream(source=CAMERA_SOURCE)
        camera.start()

        detector = ObjectDetector()

        with lock:
            state["running"] = True
            state["status"] = "Running"
            state["error"] = None

        while not stop_event.is_set():
            frame = camera.get_frame()

            if frame is None:
                time.sleep(0.05)
                continue

            detections = detector.detect(frame)

            display_frame = frame.copy()

            if detector.latest_results:
                display_frame = detector.latest_results[0].plot()

            with lock:
                state["frame"] = display_frame
                state["detections"] = detections

            time.sleep(0.01)

    except Exception as e:
        with lock:
            state["error"] = str(e)
            state["status"] = "Error"

    finally:
        if camera:
            camera.stop()

        with lock:
            state["running"] = False
            if state["status"] != "Error":
                state["status"] = "Stopped"


@app.get("/api/status")
def get_status():
    with lock:
        return {
            "running": state["running"],
            "status": state["status"],
            "error": state["error"],
            "detections": state["detections"],
        }


@app.post("/api/start")
def start_detection():
    if state["running"]:
        return {"message": "Already running"}

    stop_event.clear()

    thread = threading.Thread(
        target=detection_worker,
        daemon=True
    )
    thread.start()

    return {"message": "Detection starting"}


@app.post("/api/stop")
def stop_detection():
    stop_event.set()
    return {"message": "Stopping detection"}


def video_generator():
    while True:
        with lock:
            frame = state["frame"]

        if frame is None:
            time.sleep(0.1)
            continue

        success, buffer = cv2.imencode(".jpg", frame)

        if success:
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + buffer.tobytes()
                + b"\r\n"
            )

        time.sleep(0.04)


@app.get("/api/video")
def video_feed():
    return StreamingResponse(
        video_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
