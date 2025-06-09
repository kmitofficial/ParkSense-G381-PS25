import re
import base64
import datetime
from io import BytesIO
import os
import cv2
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import qrcode
from ultralytics import YOLO
from paddleocr import PaddleOCR

app = Flask(__name__)

# Configure CORS to allow frontend URLs for detection and QR endpoints
CORS(app, resources={
    r"/detect": {"origins": [
        "http://localhost:5173", 
        "http://172.168.0.152:5173",
        "http://192.168.1.37:5173",
        "http://172.168.0.67:5173",
        "http://172.168.0.90:5173",
        "https://parksense-frontend-omega.vercel.app"
    ]},
    r"/get-qr": {"origins": "*"},
    r"/upload_plate": {"origins": "*"},
    r"/check-scan": {"origins": "*"},
    r"/slot-status": {"origins": "*"}
})

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Initialize models (YOLO + PaddleOCR)
model = YOLO("best.pt")
ocr = PaddleOCR(use_angle_cls=True, lang="en")

# MongoDB client and database setup
client = MongoClient("mongodb+srv://suryateja2neti:Suryateja@parksense.coocf1i.mongodb.net/")
db = client["parksense"]
license_plate_collection = db["license_plates"]
slots_collection = db["slots"]
qr_collection = db["qr_codes"]

# ----------------- Utility Functions -----------------

def normalize_plate(plate):
    return ' '.join(plate.upper().split())

def fix_ocr_errors(plate):
    plate = plate.upper().replace(" ", "")
    replacements = {
        'O': '0',
        'I': '1',
        'L': '1',
        'S': '5',
        'Z': '2',
        'B': '8',
        'G': '6',
        'Q': '0',
    }
    corrected = ''.join(replacements.get(c, c) for c in plate)
    pattern = re.compile(r'^[A-Z]{2}\d{1,2}[A-Z]{1,2}\d{4}$')
    if pattern.match(corrected):
        return corrected
    else:
        return corrected

def decode_image(image_data):
    try:
        if ',' in image_data:
            img_bytes = base64.b64decode(image_data.split(',')[1])
        else:
            img_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        print("Error decoding image:", e)
        return None

def generate_qr(data):
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{img_str}"

# ----------------- Routes -----------------

@app.route('/upload_plate', methods=['POST'])
def upload_plate():
    print("hi")
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON payload received"}), 400

    plate = data.get('license_plate')
    slot = data.get('slot')
    confidence = data.get('confidence')
    image_base64 = data.get('image')

    if not plate or not slot or float(confidence) < 0.8:
        return jsonify({"error": "Invalid or low-confidence data"}), 400

    normalized_plate = normalize_plate(plate)
    new_slot = slot

    record = {
        "license_plate": normalized_plate,
        "slot": new_slot,
        "confidence": float(confidence),
        "timestamp": datetime.datetime.utcnow()
    }

    if image_base64:
        record["imageBase64"] = image_base64

    slot_record = slots_collection.find_one({
        "carNumber": {"$regex": f"^{normalized_plate}$", "$options": "i"}
    })

    existing_plate = license_plate_collection.find_one({
        "license_plate": normalized_plate
    })

    if not slot_record:
        record['unauthorized'] = True
        if existing_plate:
            license_plate_collection.update_one(
                {"_id": existing_plate["_id"]},
                {"$set": {**record, "unauthorized": True}}
            )
            return jsonify({"message": "Unauthorized plate updated."}), 200
        else:
            license_plate_collection.insert_one(record)
            return jsonify({"message": "Unauthorized plate inserted."}), 200

    correct_slot = slot_record.get('slotNumber')
    if correct_slot != new_slot:
        slots_collection.update_one(
            {"_id": slot_record["_id"]},
            {"$set": {"slotNumber": new_slot}}
        )

    if existing_plate:
        update_needed = (
            existing_plate.get('slot') != new_slot or
            existing_plate.get('unauthorized', True)
        )
        if update_needed:
            update_fields = {
                "slot": new_slot,
                "unauthorized": False
            }
            if image_base64:
                update_fields["imageBase64"] = image_base64

            license_plate_collection.update_one(
                {"_id": existing_plate["_id"]},
                {"$set": update_fields}
            )
            return jsonify({"message": "Slot updated and plate marked authorized."}), 200
        else:
            return jsonify({"message": "Plate already exists, no update needed."}), 200
    else:
        record['unauthorized'] = False
        license_plate_collection.insert_one(record)
        return jsonify({"message": "License plate uploaded and marked authorized."}), 200

@app.route('/detect', methods=['POST'])
def detect():
    print("hi")
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({"error": "No image provided"}), 400

        image_data = data['image']
        if len(image_data) > 10 * 1024 * 1024:  # 10MB limit
            return jsonify({"error": "Image too large (max 10MB)"}), 413

        img = decode_image(image_data)
        if img is None:
            return jsonify({"error": "Invalid image format"}), 400

        # Run YOLO detection
        results = model(img)
        detected_text = None

        for result in results:
            boxes = result.boxes.xyxy.cpu().numpy()
            for box in boxes:
                x1, y1, x2, y2 = map(int, box)
                cropped_plate = img[y1:y2, x1:x2]
                if cropped_plate.size == 0:
                    continue

                ocr_result = ocr.ocr(cropped_plate, cls=True)
                raw_text = "".join([word_info[1][0] for line in ocr_result for word_info in line]).replace(" ", "")

                # Fix OCR errors here
                detected_text = fix_ocr_errors(raw_text)
                break
            if detected_text:
                break

        if not detected_text:
            detected_text = "NoNumberPlateDetected"

        # Generate QR code URL and image
        base_url = "https://parksense-frontend-omega.vercel.app/entry/"
        qr_data = base_url + detected_text
        qr_image = generate_qr(qr_data)

        # Store or update QR code info in MongoDB
        qr_collection.update_one(
            {"plate_number": detected_text},
            {
                "$set": {
                    "plate_number": detected_text,
                    "qr_image": qr_image,
                    "created_at": datetime.datetime.utcnow(),
                    "status": "active"
                }
            },
            upsert=True
        )

        # Create or update slot record in slots collection
        slots_collection.update_one(
            {"plate_number": detected_text},
            {
                "$set": {
                    "plate_number": detected_text,
                    "status": "occupied",
                    "entry_time": datetime.datetime.utcnow(),
                    "qr_code": qr_image
                }
            },
            upsert=True
        )

        return jsonify({
            "number_plate": detected_text,
            "qr_image": qr_image
        })
    except Exception as e:
        print("Server error:", e)
        return jsonify({"error": "Internal server error"}), 500

@app.route('/get-qr', methods=['GET'])
def get_qr():
    try:
        plate_number = request.args.get("plate_number")
        if not plate_number:
            return jsonify({"error": "Missing plate_number"}), 400

        # Check if QR exists in DB
        record = qr_collection.find_one({"plate_number": plate_number})
        if record:
            return jsonify({
                "plate_number": record["plate_number"],
                "qr_image": record["qr_image"]
            })

        # Handle special guest case
        if plate_number == "NONUMBERPLATEDETECTED":
            base_url = "https://parksense-frontend-omega.vercel.app/entry/"
            qr_data = base_url + "guest"
            qr_image = generate_qr(qr_data)

            qr_collection.update_one(
                {"plate_number": "guest"},
                {"$set": {"qr_image": qr_image}},
                upsert=True
            )

            return jsonify({
                "plate_number": "guest",
                "qr_image": qr_image
            })

        # Generate new QR if not found
        base_url = "https://a9ab-2001-4490-4cac-694f-14eb-83d2-ee6e-8a2e.ngrok-free.app/entry/"
        qr_data = base_url + plate_number
        qr_image = generate_qr(qr_data)

        qr_collection.update_one(
            {"plate_number": plate_number},
            {"$set": {"qr_image": qr_image}},
            upsert=True
        )

        return jsonify({
            "plate_number": plate_number,
            "qr_image": qr_image
        })

    except Exception as e:
        print(f"Error in /get-qr: {str(e)}")
        return jsonify({"error": f"Database error: {str(e)}"}), 500

@app.route('/ping')
def ping():
    return "pong"

@app.route('/check-scan', methods=['POST'])
def check_scan():
    try:
        data = request.get_json()
        plate_number = data.get('plate_number')

        if not plate_number:
            return jsonify({"error": "Plate number required"}), 400

        slot = slots_collection.find_one({"plate_number": plate_number})

        if slot:
            if slot.get('status') == 'occupied':
                # Second scan - Release slot
                slots_collection.update_one(
                    {"plate_number": plate_number},
                    {
                        "$set": {
                            "status": "released",
                            "exit_time": datetime.datetime.utcnow()
                        }
                    }
                )
                return jsonify({"message": "Slot released", "status": "released"})
            else:
                # First scan - Occupy slot
                slots_collection.update_one(
                    {"plate_number": plate_number},
                    {
                        "$set": {
                            "status": "occupied",
                            "entry_time": datetime.datetime.utcnow()
                        }
                    },
                    upsert=True
                )
                return jsonify({"message": "Slot occupied", "status": "occupied"})
        else:
            # No slot found, create one as occupied
            slots_collection.insert_one({
                "plate_number": plate_number,
                "status": "occupied",
                "entry_time": datetime.datetime.utcnow()
            })
            return jsonify({"message": "Slot occupied (new record)", "status": "occupied"})

    except Exception as e:
        print(f"Error in /check-scan: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/slot-status', methods=['GET'])
def slot_status():
    try:
        plate_number = request.args.get('plate_number')
        if not plate_number:
            return jsonify({"error": "Plate number required"}), 400

        slot = slots_collection.find_one({"plate_number": plate_number})
        if not slot:
            return jsonify({"error": "No slot found"}), 404

        status = slot.get('status', 'unknown')
        return jsonify({"plate_number": plate_number, "status": status})

    except Exception as e:
        print(f"Error in /slot-status: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

# ----------------- Run Server -----------------



if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # fallback to 5000 for local dev
    app.run(debug=True, host='0.0.0.0', port=port)
