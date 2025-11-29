# camera_mood.py
import cv2
from fer import FER

def detect_mood_camera():
    detector = FER()

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        return None, "Camera not found"

    print("📸 Hold still... detecting mood...")

    mood_result = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Detect emotions in the frame
        emotions = detector.detect_emotions(frame)

        cv2.imshow("Camera Mood Detection - Press Q to Capture", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            # User pressed Q → capture mood
            break

        if emotions:
            # Pick the highest emotion score
            top = emotions[0]['emotions']
            mood_result = max(top, key=top.get)

    cap.release()
    cv2.destroyAllWindows()

    if mood_result is None:
        return None, "No face detected"

    return mood_result, None
