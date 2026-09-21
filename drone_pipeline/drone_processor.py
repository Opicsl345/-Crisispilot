import cv2
import time
import requests
from ultralytics import YOLO

# API Configuration
BACKEND_API_URL = "http://127.0.0.1:8000/api/v1/drone/observation"
VIDEO_PATH = "media/disaster_sample.mp4"
DRONE_ID = "SIM-DRONE-NEPAL-01"

# Base Location Simulation (Kathmandu / Sindhupalchok region)
START_LAT = 27.82000
START_LNG = 85.73000
ALTITUDE_METERS = 50.0

print("[INFO] Loading YOLOv8 Model onto GPU/CPU...")
model = YOLO("yolov8n.pt")  # Downloads weights automatically on first run

cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    print(f"[ERROR] Cannot open video: {VIDEO_PATH}")
    print("[ACTION REQUIRED] Place your video clip in crisispilot/drone_pipeline/media/disaster_sample.mp4")
    exit()

frame_index = 0
last_api_send_time = 0.0
SEND_INTERVAL_SECONDS = 1.5

print("[INFO] Drone AI Pipeline running...")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0) # Loop video
        continue

    frame_index += 1
    
    # Calculate drifting drone GPS telemetry
    current_lat = START_LAT + (frame_index * 0.00002)
    current_lng = START_LNG + (frame_index * 0.000015)

    # Run YOLO object detection
    results = model(frame, verbose=False)[0]

    detected_hazards = []
    people_count = 0
    formatted_detections = []

    for box in results.boxes:
        cls_id = int(box.cls[0])
        class_name = model.names[cls_id]
        confidence = float(box.conf[0])
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

        if class_name == "person" and confidence > 0.35:
            people_count += 1
            formatted_detections.append({
                "label": "person",
                "confidence": round(confidence, 2),
                "bbox": [x1, y1, x2, y2]
            })
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 0), 2)
            cv2.putText(frame, f"PERSON {confidence:.2f}", (x1, max(y1-5, 15)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

        elif class_name in ["car", "truck", "bus"] and confidence > 0.40:
            if "Road Obstruction" not in detected_hazards:
                detected_hazards.append("Road Obstruction")
            formatted_detections.append({
                "label": class_name,
                "confidence": round(confidence, 2),
                "bbox": [x1, y1, x2, y2]
            })
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(frame, f"{class_name.upper()} {confidence:.2f}", (x1, max(y1-5, 15)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

    hazard_present = people_count > 0 or len(detected_hazards) > 0

    # Draw HUD
    cv2.putText(frame, f"CRISIS PILOT AI - DRONE HUD [{DRONE_ID}]", (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, f"LAT: {current_lat:.6f} | LNG: {current_lng:.6f} | ALT: {ALTITUDE_METERS}m", (20, 65),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
    cv2.putText(frame, f"PEOPLE IN DANGER: {people_count}", (20, 95),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0) if not hazard_present else (0, 0, 255), 2)

    # Send API Payload periodically
    current_time = time.time()
    if current_time - last_api_send_time >= SEND_INTERVAL_SECONDS:
        last_api_send_time = current_time

        payload = {
            "drone_id": DRONE_ID,
            "latitude": round(current_lat, 6),
            "longitude": round(current_lng, 6),
            "altitude_m": ALTITUDE_METERS,
            "status": "PATROLLING_ACTIVE",
            "timestamp": current_time,
            "hazard_detected": hazard_present,
            "detected_hazards": detected_hazards if detected_hazards else ["Landslide / Active Debris"],
            "people_detected_count": people_count,
            "detections": formatted_detections
        }

        try:
            res = requests.post(BACKEND_API_URL, json=payload, timeout=0.5)
            if res.status_code == 200:
                cv2.putText(frame, "API: TRANSMITTED", (frame.shape[1] - 200, 35),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        except Exception:
            cv2.putText(frame, "API: OFFLINE", (frame.shape[1] - 200, 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    cv2.imshow("CrisisPilot AI - Drone Telemetry Stream", frame)

    if cv2.waitKey(20) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()