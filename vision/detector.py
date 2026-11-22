
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

        print(f"Loading custom model: {model_path}")
        self.custom_model = YOLO(model_path)

        # General pretrained COCO model for everyday objects:
        # person, chair, bottle, backpack, car, laptop, etc.
        print("Loading general object model: yolov8n.pt")
        self.general_model = YOLO("yolov8n.pt")

        print("Custom classes:", self.custom_model.names)
        print("General classes:", self.general_model.names)

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

    @staticmethod
    def box_iou(box_a, box_b):
        x1 = max(box_a[0], box_b[0])
        y1 = max(box_a[1], box_b[1])
        x2 = min(box_a[2], box_b[2])
        y2 = min(box_a[3], box_b[3])

        intersection = max(0, x2 - x1) * max(0, y2 - y1)

        area_a = max(0, box_a[2] - box_a[0]) * max(
            0, box_a[3] - box_a[1]
        )
        area_b = max(0, box_b[2] - box_b[0]) * max(
            0, box_b[3] - box_b[1]
        )

        union = area_a + area_b - intersection

        if union <= 0:
            return 0.0

        return intersection / union

    def detect(self, frame):
        start_time = time.perf_counter()

        self.frame_status = self.quality.check(frame)

        # Run the custom model for trained obstacle classes.
        custom_results = self.custom_model.track(
            frame,
            persist=True,
            tracker="bytetrack.yaml",
            conf=0.20,
            imgsz=416,
            device="cpu",
            max_det=20,
            verbose=False
        )

        # Run general COCO detection for common everyday objects.
        general_results = self.general_model.track(
            frame,
            persist=True,
            tracker="bytetrack.yaml",
            conf=0.25,
            imgsz=416,
            device="cpu",
            max_det=30,
            verbose=False
        )

        self.latest_results = general_results

        candidates = []

        # Process detections from both models.
        model_results = [
            (custom_results, self.custom_model, 10000),
            (general_results, self.general_model, 0)
        ]

        for result_group, model, id_offset in model_results:

            for result in result_group:

                if result.boxes is None or len(result.boxes) == 0:
                    continue

                boxes = result.boxes
                track_ids = boxes.id

                for i, box in enumerate(boxes):

                    coordinates = box.xyxy[0].tolist()
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])

                    names = model.names
                    label = (
                        names[class_id]
                        if isinstance(names, dict)
                        else names[class_id]
                    )

                    raw_id = (
                        int(track_ids[i])
                        if track_ids is not None
                        else None
                    )

                    track_id = (
                        raw_id + id_offset
                        if raw_id is not None
                        else None
                    )

                    candidates.append({
                        "label": str(label).lower(),
                        "id": track_id,
                        "conf": confidence,
                        "box": coordinates
                    })

        # Remove duplicate detections when both models see
        # the same object in approximately the same location.
        candidates.sort(
            key=lambda item: item["conf"],
            reverse=True
        )

        unique_candidates = []

        for candidate in candidates:

            duplicate = False

            for existing in unique_candidates:

                same_label = (
                    candidate["label"] == existing["label"]
                )

                overlap = self.box_iou(
                    candidate["box"],
                    existing["box"]
                )

                if same_label and overlap > 0.55:
                    duplicate = True
                    break

            if not duplicate:
                unique_candidates.append(candidate)

        detections = []

        for item in unique_candidates:

            coordinates = item["box"]
            label = item["label"]
            track_id = item["id"]

            if label == "person":
                x1, y1, x2, y2 = coordinates
                height_px = y2 - y1
                print(f"PERSON BOX HEIGHT: {height_px:.1f} pixels")

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

            approaching = self.logic.is_approaching(
                track_id,
                coordinates
            ) if track_id is not None else False

            detections.append({
                "label": "cupboard" if label == "refrigerator" else label,
                "id": track_id,
                "conf": item["conf"],
                "zone": zone,
                "dist": distance,
                "distance_cm": distance_cm,
                "approaching": approaching,
                "unknown_obstacle": False
            })

        # Draw general model detections for the camera preview.
        # API detections include results from both models.
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
