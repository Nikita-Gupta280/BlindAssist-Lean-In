
from config import (
    CLOSE_DISTANCE,
    MEDIUM_DISTANCE,
    APPROACHING_THRESHOLD
)


class VisionLogic:

    # Approximate reference heights in centimetres.
    OBJECT_HEIGHTS = {
        "person": 170,
        "bottle": 25,
        "cell phone": 15,
        "chair": 90,
        "bench": 90,
        "car": 150,
        "motorcycle": 110,
        "bicycle": 110,
        "bus": 300,
        "truck": 300,
        "laptop": 22,
        "book": 25,
        "cup": 12,
        "dining table": 75,
        "couch": 85,
        "bed": 60,
        "refrigerator": 170,
    }

    def __init__(self, focal_px, known_object_height_cm):
        self.focal_px = focal_px
        self.known_object_height_cm = known_object_height_cm
        self.previous_heights = {}

    def get_zone(self, box, frame_width):

        x1, y1, x2, y2 = box
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

        if height_px <= 0:
            return None

        known_height = (
            30 if str(label).lower() == "bottle"
            else self.known_object_height_cm
        )

        distance_cm = (known_height * self.focal_px) / height_px

        return distance_cm

    def get_distance(self, box, label=None):

        distance_cm = self.get_distance_cm(box, label)

        if distance_cm is None:
            return "far"

        if distance_cm < CLOSE_DISTANCE:
            return "close"
        elif distance_cm < MEDIUM_DISTANCE:
            return "medium"
        else:
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
