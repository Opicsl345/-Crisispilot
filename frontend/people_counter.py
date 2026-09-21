import cv2
from flask import Flask, Response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS so your web page can fetch the stream

# Configuration - using your exact video filename
VIDEO_PATH = "disaster_crowd.mp4"

def generate_frames():
    cap = cv2.VideoCapture(VIDEO_PATH)

    # Background subtractor optimized for high-angle surveillance
    fgbg = cv2.createBackgroundSubtractorMOG2(history=300, varThreshold=40, detectShadows=True)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            # Loop video when it ends
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        # Resize for consistent, fast processing
        frame = cv2.resize(frame, (960, 540))
        
        # Apply background subtraction
        fgmask = fgbg.apply(frame)
        
        # Clean up background noise with morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel)
        fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        person_count = 0
        for c in contours:
            area = cv2.contourArea(c)
            # Filter out tiny noise and massive blobs (like moving cars)
            if 150 < area < 2500:
                (x, y, w, h) = cv2.boundingRect(c)
                
                # Aspect ratio check: pedestrians are generally taller than they are wide (h > w or close)
                aspect_ratio = h / float(w) if w > 0 else 0
                
                if aspect_ratio > 0.8: # Tighter filter for upright pedestrian profiles
                    person_count += 1
                    # Draw green tracking box on detected person
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Display live counter overlay on frame
        cv2.putText(frame, f"PEOPLE DETECTED: {person_count}", (30, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 3)

        # Encode frame to JPEG format for web streaming
        success, buffer = cv2.imencode('.jpg', frame)
        if not success:
            continue
        frame_bytes = buffer.tobytes()

        # Yield frame in MJPEG format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    print("Starting Overhead People Counting Stream Server on http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=False)