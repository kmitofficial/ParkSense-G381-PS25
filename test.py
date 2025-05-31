# test.py

import cv2
from ultralytics import YOLO
from paddleocr import PaddleOCR
import numpy as np
import re
import requests
import threading
from dronekit import connect, VehicleMode
from pymavlink import mavutil
import time
import signal
import sys
import base64
from datetime import datetime

BACKEND_URL = "http://172.168.0.152:5000/upload_plate"
PLATE_PATTERN = r'^[A-Z]{2}\d{2}[A-Z]{1,2}\d{4}$'

CENTER = 1500
TURN_AMOUNT = 0
THROTTLE_NEUTRAL = 1500
THROTTLE_MAX = 2000
THROTTLE_MIN = 1000

THROTTLE_CH = 3
STEERING_CH = 1

current_throttle = THROTTLE_NEUTRAL
current_steering = CENTER
initial_yaw = None
should_stop = False
vehicle = None

distance_covered = 0
slot_counter = 0
last_distance_slot = -1
slot_plate_memory = {}  # {slot_number: set(plates_sent)}

def signal_handler(sig, frame):
    global should_stop, vehicle
    print("\nCtrl+C detected. Stopping rover and cleaning up...")
    should_stop = True
    if vehicle:
        vehicle.channels.overrides = {}
        vehicle.close()
    cv2.destroyAllWindows()
    sys.exit(0)

def clean_ocr_text(text):
    raw = text.upper()
    cleaned = re.sub(r'[^A-Z0-9]', '', raw)
    if not re.fullmatch(PLATE_PATTERN, cleaned):
        corrected = cleaned.replace('O', '0').replace('I', '1').replace('Z', '2').replace('S', '5')
        cleaned = corrected
    return cleaned if re.fullmatch(PLATE_PATTERN, cleaned) else None

def assign_slot_by_distance(distance_m):
    global slot_counter, last_distance_slot
    slot_group = int(distance_m // 2)

    if slot_group != last_distance_slot:
        slot_counter += 1
        last_distance_slot = slot_group

    group_letter = chr(65 + (slot_counter // 6) % 4)  # A-D
    index = slot_counter % 6 + 1
    return f"{group_letter}{index}"

def encode_image_to_base64(image):
    _, buffer = cv2.imencode('.jpg', image)
    return base64.b64encode(buffer).decode('utf-8')

def send_to_backend(plate, slot, confidence, plate_img):
    try:
        encoded_img = encode_image_to_base64(plate_img)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        data = {
            "license_plate": plate,
            "slot": slot,
            "confidence": float(confidence),
            "timestamp": timestamp,
            "image": encoded_img
        }

        response = requests.post(BACKEND_URL, json=data)
        print(f"[Backend] ✅ Sent: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[Backend] ❌ Error sending: {e}")

def get_yaw():
    attitude = vehicle.attitude
    return attitude.yaw * (180.0 / 3.14159)

def correct_drift():
    global current_steering
    if initial_yaw is None:
        return
    yaw = get_yaw()
    deviation = yaw - initial_yaw

    if deviation > 1:
        current_steering = CENTER + TURN_AMOUNT
    elif deviation < -1:
        current_steering = CENTER - TURN_AMOUNT
    else:
        current_steering = CENTER

    send_rc_override(current_throttle, current_steering)

def send_rc_override(throttle, steering):
    vehicle.channels.overrides = {
        THROTTLE_CH: throttle,
        STEERING_CH: steering
    }

def move_rover(direction, throttle_percent, duration=None):
    global current_throttle, initial_yaw, should_stop, distance_covered

    if direction == 'forward':
        current_throttle = THROTTLE_NEUTRAL + int(500 * (throttle_percent / 100))
    elif direction == 'backward':
        current_throttle = THROTTLE_NEUTRAL - int(500 * (throttle_percent / 100))
    else:
        print("Invalid direction")
        return

    initial_yaw = get_yaw()
    print(f"Moving {direction}...")

    if duration:
        start_time = time.time()
        while (time.time() - start_time < duration) and not should_stop:
            correct_drift()
            time.sleep(0.1)
            distance_covered += 0.2
        stop_rover()
    else:
        while not should_stop:
            correct_drift()
            time.sleep(0.1)
            distance_covered += 0.2

def stop_rover():
    global current_throttle
    current_throttle = THROTTLE_NEUTRAL
    send_rc_override(current_throttle, CENTER)
    print("Rover stopped")

def detection_loop():
    global distance_covered
    yolo_model = YOLO("best.pt")
    ocr_model = PaddleOCR(use_angle_cls=True, lang='en')

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[Camera] ❌ Failed to open camera")
        return

    while not should_stop:
        ret, frame = cap.read()
        if not ret:
            print("[Camera] ❌ Failed to capture frame")
            break

        results = yolo_model(frame)[0]
        detections = 0

        for box in results.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            if conf < 0.4:
                continue

            detections += 1
            plate_img = frame[y1:y2, x1:x2].copy()

            try:
                ocr_result = ocr_model.ocr(plate_img, cls=True)
                if ocr_result and len(ocr_result) > 0:
                    for line in ocr_result[0]:
                        if len(line) >= 2:
                            raw_text = line[1][0]
                            conf_score = line[1][1]
                            cleaned = clean_ocr_text(raw_text)

                            if not cleaned or conf_score < 0.8:
                                continue

                            slot = assign_slot_by_distance(distance_covered)
                            if slot not in slot_plate_memory:
                                slot_plate_memory[slot] = set()

                            if cleaned not in slot_plate_memory[slot]:
                                send_to_backend(cleaned, slot, conf_score, plate_img)
                                slot_plate_memory[slot].add(cleaned)
                                label = f"{slot}: {cleaned} ({conf_score:.2f})"
                                print(f"[OCR] ✅ {label}")

                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                            cv2.putText(frame, cleaned, (x1, y1 - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            except Exception as e:
                print(f"[OCR] ❌ Error: {e}")

        cv2.putText(frame, f"Detections: {detections}", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("License Plate Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def main():
    global vehicle, should_stop
    signal.signal(signal.SIGINT, signal_handler)

    try:
        vehicle = connect('/dev/ttyUSB0', baud=57600, wait_ready=False)
        print("Connected to vehicle")
    except Exception as e:
        print(f"Failed to connect to vehicle: {e}")
        return

    detection_thread = threading.Thread(target=detection_loop)
    detection_thread.daemon = True
    detection_thread.start()

    try:
        while not should_stop:
            direction = input("Enter direction (forward/backward/stop): ").strip().lower()

            if direction == 'stop':
                stop_rover()
                continue

            if direction not in ["forward", "backward"]:
                print("Invalid direction.")
                continue

            try:
                throttle = int(input("Throttle % (0–100): "))
                duration = input("Duration (sec) or press Enter: ")
                duration = float(duration) if duration else None
            except ValueError:
                print("Invalid input")
                continue

            move_thread = threading.Thread(target=move_rover, args=(direction, throttle, duration))
            move_thread.daemon = True
            move_thread.start()
    finally:
        should_stop = True
        stop_rover()
        if vehicle:
            vehicle.channels.overrides = {}
            vehicle.close()
        cv2.destroyAllWindows()
        print("Exited cleanly")

if __name__ == "__main__":
    main()