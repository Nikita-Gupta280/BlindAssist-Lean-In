
from config import (
    CLOSE_DISTANCE,
    MEDIUM_DISTANCE,
    APPROACHING_THRESHOLD
)


class VisionLogic:

    # Approximate real-world object heights in centimetres.
    # These are assumptions, not exact measurements.
    OBJECT_HEIGHTS = {
        "person": 170,
        "bicycle": 110,
        "car": 150,
        "motorcycle": 110,
        "airplane": 300,
        "bus": 300,
        "train": 300,
        "truck": 300,
        "boat": 150,
        "traffic light": 90,
        "fire hydrant": 75,
        "stop sign": 75,
        "parking meter": 120,
        "bench": 90,
        "bird": 20,
        "cat": 25,
        "dog": 50,
        "horse": 150,
        "sheep": 80,
        "cow": 140,
        "elephant": 250,
        "bear": 150,
        "zebra": 140,
        "giraffe": 400,
        "backpack": 45,
        "umbrella": 90,
        "handbag": 30,
        "tie": 140,
        "suitcase": 60,
        "bottle": 25,
        "wine glass": 20,
        "cup": 12,
        "fork": 20,
        "knife": 25,
        "spoon": 18,
        "bowl": 12,
        "banana": 20,
        "apple": 9,
        "sandwich": 10,
        "orange": 8,
        "broccoli": 15,
        "carrot": 18,
        "hot dog": 15,
        "pizza": 30,
        "donut": 10,
        "cake": 15,
        "chair": 90,
        "couch": 85,
        "potted plant": 60,
        "bed": 60,
        "dining table": 75,
        "toilet": 75,
        "tv": 55,
        "laptop": 22,
        "mouse": 5,
        "remote": 18,
        "keyboard": 4,
        "cell phone": 15,
        "microwave": 30,
        "oven": 60,
        "toaster": 20,
        "sink": 25,
        "refrigerator": 110,
        "book": 25,
        "clock": 30,
        "vase": 30,
        "scissors": 15,
        "teddy bear": 30,
        "hair drier": 20,
        "toothbrush": 18,
    }

    def __init__(self, focal_px, known_object_height_cm):
        self.focal_px = float(focal_px)
        self.known_object_height_cm = known_object_height_cm
        self.previous_heights = {}

    @staticmethod
    def normalize_label(label):
        if label is None:
            return ""

        return " ".join(str(label).lower().replace("_", " ").split())

    def get_zone(self, box, frame_width):
        x1, y1, x2, y2 = box

        if frame_width <= 0:
            return "center"

        center_x = (x1 + x2) / 2
        position = center_x / frame_width

        if position < 0.2:
            return "far_left"
        elif position < 0.4:
            return "left"
        elif position < 0.6:
            return "center"
        elif position < 0.8:
            return "right"
        else:
            return "far_right"

    def get_distance_cm(self, box, label=None):
        x1, y1, x2, y2 = box
        height_px = y2 - y1

        if height_px <= 0 or self.focal_px <= 0:
            return None

        normalized_label = self.normalize_label(label)
        real_height_cm = self.OBJECT_HEIGHTS.get(normalized_label)

        if real_height_cm is None:
            return None

        distance_cm = (real_height_cm * self.focal_px) / height_px

        if not 0 < distance_cm < 2000:
            return None

        return round(distance_cm, 1)
    def get_distance(self, box, label=None):
        distance_cm = self.get_distance_cm(box, label)

        if distance_cm is None:
            return "unavailable"

        if distance_cm < CLOSE_DISTANCE:
            return "close"
        elif distance_cm < MEDIUM_DISTANCE:
            return "medium"

        return "far"

    def is_approaching(self, track_id, box):
        if track_id is None:
            return False

        x1, y1, x2, y2 = box
        current_height = y2 - y1

        if current_height <= 0:
            return False

        previous_height = self.previous_heights.get(track_id)
        self.previous_heights[track_id] = current_height

        if previous_height is None or previous_height <= 0:
            return False

        growth = current_height / previous_height

        return growth > APPROACHING_THRESHOLD
