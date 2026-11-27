
import time
import torch
from ultralytics import YOLO

from vision.logic import VisionLogic
from vision.quality import FrameQuality

from config import (
    MODEL_PATH,
    FOCAL_PX,
    KNOWN_OBJECT_HEIGHT_CM
)


class ObjectDetector:

    def __init__(self, model_path=None):
        torch.set_num_threads(2)

        try:
            torch.set_num_interop_threads(1)
        except RuntimeError:
            pass

        if model_path is None:
            model_path = MODEL_PATH

        print(f"Loading YOLO model: {model_path}")
        self.model = YOLO(model_path)

        print("Model classes:", self.model.names)

        self.logic = VisionLogic(
            focal_px=FOCAL_PX,
            known_object_height_cm=KNOWN_OBJECT_HEIGHT_CM
        )

        self.quality = FrameQuality()
        self.latest_results = None
        self.frame_status = {}

        self.total_frames = 0
        self.total_time = 0.0
        self.current_fps = 0.0
        self.average_fps = 0.0

    def detect(self, frame):
        start_time = time.perf_counter()

        self.frame_status = self.quality.check(frame)

        # Run YOLO only once per frame.
        results = self.model.track(
            frame,
            persist=True,
            tracker="bytetrack.yaml",
            conf=0.20,
            imgsz=320,
            device="cpu",
            max_det=30,
            verbose=False
        )

        self.latest_results = results

        detections = []

        for result in results:

            if result.boxes is None or len(result.boxes) == 0:
                continue

            boxes = result.boxes
            track_ids = boxes.id

            for i, box in enumerate(boxes):

                coordinates = box.xyxy[0].tolist()
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])

                label = self.model.names[class_id]

                track_id = (
                    int(track_ids[i])
                    if track_ids is not None
                    else None
                )

                zone = self.logic.get_zone(
                    coordinates,
                    frame.shape[1]
                )

                distance_cm = self.logic.get_distance_cm(
                    coordinates,
                    label
                )

                distance = self.logic.get_distance(
                    coordinates,
                    label
                )

                approaching = (
                    self.logic.is_approaching(track_id, coordinates)
                    if track_id is not None
                    else False
                )

                detections.append({
                    "label": "cupboard" if label == "refrigerator" else str(label).lower(),
                    "id": track_id,
                    "conf": confidence,
                    "zone": zone,
                    "dist": distance,
                    "distance_cm": distance_cm,
                    "approaching": approaching,
                    "unknown_obstacle": False
                })

        elapsed_time = time.perf_counter() - start_time

        self.total_frames += 1
        self.total_time += elapsed_time

        self.current_fps = (
            1 / elapsed_time if elapsed_time > 0 else 0
        )

        self.average_fps = (
            self.total_frames / self.total_time
            if self.total_time > 0 else 0
        )

        print(
            f"Detection FPS: {self.current_fps:.2f} | "
            f"Average FPS: {self.average_fps:.2f} | "
            f"Objects: {len(detections)} | "
            f"Labels: {[d['label'] for d in detections]}"
        )

        return detections
