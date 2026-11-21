# BlindAssist – AI-Powered Smart Cane Assistance System

BlindAssist is an AI-powered assistive technology prototype designed to help visually impaired individuals become more aware of nearby obstacles through real-time object detection, spatial positioning, approximate distance estimation, and voice alerts.

The system uses a camera to capture the surroundings, processes video frames using YOLO-based object detection, and provides audio information about detected objects in the user's environment.

The project aims to make everyday navigation more accessible through an affordable, camera-based approach.

---

## Features

### 1. Real-Time Object Detection
- Uses YOLOv8n for lightweight object detection.
- Identifies supported objects in the camera feed.
- Uses ByteTrack for object tracking across frames.
- Applies a configurable confidence threshold.

### 2. Spatial Position Detection
Divides the camera frame into five regions to identify the approximate position of detected objects:

- Far Left
- Left
- Center
- Right
- Far Right

### 3. Approximate Distance Estimation
- Estimates object distance using bounding-box height and camera calibration parameters.
- Categorizes detected objects as Close, Medium, or Far.
- Uses configurable distance thresholds.
- Provides approximate distance information in Detailed mode.

*Note: Distance estimation is based on assumed object heights and camera calibration. It is not a precise depth measurement.*

### 4. Approaching Object Detection
- Uses changes in the bounding-box height of tracked objects.
- Identifies potential approaching objects using a configurable threshold.
- Supports approaching-object voice warnings.

This is a basic visual heuristic, not a reliable collision prediction system.

### 5. Frame Quality Assessment
Evaluates incoming camera frames before object detection.

- **Blur Detection:** Uses the variance of the Laplacian to estimate image sharpness.
- **Low-Light Detection:** Checks average frame brightness.
- Frames that fail the configured quality checks can be rejected before detection.

### 6. Multilingual Voice Alerts
Provides spoken alert messages in:
- English
- Hindi

Alerts communicate the detected object, its approximate direction, and distance category.

### 7. Three Alert Modes

| Mode | Behaviour |
|---|---|
| Normal | Provides standard obstacle alerts. |
| Quiet | Filters out chairs and benches to reduce unnecessary alerts. |
| Detailed | Provides more detailed information, including approximate distance when available. |

### 8. Intelligent Alert Management
- Considers detections across the last five frames.
- Requires an object to appear in at least three of those frames before generating an alert.
- Prioritizes selected obstacle categories.
- Implements a 10-second cooldown for each tracked object.
- Generates at most one alert message per processed frame.

---

## Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Object Detection | Ultralytics YOLOv8n |
| Object Tracking | ByteTrack |
| Computer Vision | OpenCV |
| Deep Learning | PyTorch |
| User Interface | Streamlit |
| Numerical Processing | NumPy |
| Concurrency | Python Threading |
| Voice Alerts | Speech and audio modules |

---

## Project Structure

```text
BlindAssist/
│
├── app.py
├── config.py
├── requirements.txt
├── yolov8n.pt
│
├── vision/
│   ├── detector.py
│   ├── stream.py
│   ├── logic.py
│   └── quality.py
│
├── alerts/
│   ├── alert_manager.py
│   ├── speech.py
│   ├── phrases.py
│   └── audio/
│
├── tools/
│
├── P3_Data_Model/
│   ├── eval/
│   ├── model/
│   ├── p3_detector.py
│   ├── free_space.py
│   └── model_failures.md
│
├── test_camera.py
├── test_detector.py
├── test_quality.py
│
├── .gitignore
└── README.md
```

---

## System Workflow

```text
       Camera Input
            |
            v
      Frame Capture
            |
            v
     Frame Quality Check
       /           \
    Valid          Invalid
      |                |
      v                v
 Object Detection    Skip Frame
      |
      v
   YOLOv8n
      |
      v
  ByteTrack
      |
      v
 Spatial & Distance Analysis
      |
      v
 Approaching Object Analysis
      |
      v
  Alert Management
      |
      v
 Priority + Cooldown Filtering
      |
      v
  Hindi / English Alerts
      |
      v
    Audio Output
```

---

## Installation and Setup

### Prerequisites

- Python 3.10 or later
- Git
- Webcam or compatible camera
- Windows, Linux, or another supported Python environment

### 1. Clone the Repository

```bash
git clone https://github.com/Nikita-Gupta280/BlindAssist-Lean-In.git
```

### 2. Navigate to the Project

```bash
cd BlindAssist-Lean-In
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the Application

```bash
streamlit run app.py
```

The Streamlit application will open in your browser.

---

## Configuration

The main configuration parameters are defined in `config.py`.

| Parameter | Default Value | Description |
|---|---:|---|
| CAMERA_SOURCE | 0 | Default camera source |
| MODEL_PATH | yolov8n.pt | YOLO model path |
| CONFIDENCE_THRESHOLD | 0.35 | Detection confidence threshold |
| FOCAL_PX | 420.5 | Camera focal-length calibration |
| KNOWN_OBJECT_HEIGHT_CM | 100 | Default reference object height |
| BLUR_THRESHOLD | 60 | Blur detection threshold |
| BRIGHTNESS_THRESHOLD | 50 | Low-light threshold |
| CLOSE_DISTANCE | 100 cm | Close-object threshold |
| MEDIUM_DISTANCE | 250 cm | Medium-object threshold |
| APPROACHING_THRESHOLD | 1.10 | Bounding-box growth threshold |

These values can be adjusted according to the camera and testing environment.

---

## Experimental P3 Hazard Detection

The repository also contains a separate experimental module under `P3_Data_Model/`.

It includes custom models for:
- Door detection
- Stair detection
- Pothole detection

The module also contains evaluation results and experimental free-space analysis.

**Important:** These models are experimental and are not part of the verified core navigation pipeline. Their detection performance and suitability for real-world use require further testing and improvement.

---

## Current Limitations

- Distance estimation depends on assumed object dimensions and camera calibration.
- Approaching-object detection uses bounding-box growth as a heuristic.
- Detection performance depends on lighting, camera quality, hardware, and object visibility.
- Camera initialization may take time depending on the hardware and camera driver.
- Experimental hazard-detection models require further validation.
- The system has not been established as a certified mobility or navigation aid.

---

## Future Improvements

- Integration of improved hazard detection models.
- More reliable depth estimation.
- Better spatial awareness and obstacle prioritization.
- Optimization for faster processing on resource-constrained devices.
- Wireless camera and smart-cane integration.
- Improved real-world testing and accessibility.
- More robust navigation assistance.

---

## Safety Disclaimer

BlindAssist is an experimental assistive technology prototype developed for educational and research purposes.

It is intended to provide supplementary environmental awareness through object detection and audio alerts. It is not a certified navigation or collision-avoidance system and must not replace a white cane, guide dog, established mobility techniques, or appropriate human assistance.

Real-world use requires extensive testing, validation, and safety improvements.

---

## Project Demo

[Watch the BlindAssist Demo](https://drive.google.com/file/d/1CDTJ0sJ-_GfmFUqyIDP8dCcxYcEMl__m/view?usp=drivesdk)

---

## Project Repository

[BlindAssist – GitHub](https://github.com/Nikita-Gupta280/BlindAssist-Lean-In)

---

**BlindAssist – Making surroundings more accessible through AI and assistive technology.**