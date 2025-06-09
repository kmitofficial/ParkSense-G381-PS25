# from flask import Flask, request, jsonify
# from flask_cors import CORS
# import base64
# import cv2
# import numpy as np
# from ultralytics import YOLO
# from paddleocr import PaddleOCR
# import qrcode
# from io import BytesIO
# import base64

# app = Flask(__name__)
# CORS(app)

# # Load YOLO model (your custom trained best.pt)
# model = YOLO("best.pt")  
# ocr = PaddleOCR(use_angle_cls=True, lang="en")  # OCR model

# def decode_image(image_data):
#     """ Convert base64 image to OpenCV format """
#     try:
#         img_bytes = base64.b64decode(image_data.split(',')[1])
#         nparr = np.frombuffer(img_bytes, np.uint8)
#         img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
#         return img
#     except Exception as e:
#         print("Error decoding image:", e)
#         return None

# def generate_qr(data):
#     qr = qrcode.QRCode(version=1, box_size=10, border=2)
#     qr.add_data(data)
#     qr.make(fit=True)
#     img = qr.make_image(fill="black", back_color="white")
#     buffered = BytesIO()
#     img.save(buffered, format="PNG")
#     qr_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
#     return "data:image/png;base64," + qr_b64

# @app.route('/detect', methods=['POST'])
# def detect():
#     try:
#         data = request.get_json()
#         image_data = data.get("image")
#         if not image_data:
#             return jsonify({"error": "No image provided"}), 400

#         # Decode base64 image to OpenCV image
#         img = decode_image(image_data)
#         if img is None:
#             return jsonify({"error": "Invalid image format"}), 400

#         # Run YOLO detection
#         results = model(img)
#         detected_text = None

#         # Loop over detected boxes and run OCR on each cropped plate
#         for result in results:
#             boxes = result.boxes.xyxy.cpu().numpy()  # Bounding boxes
#             for box in boxes:
#                 x1, y1, x2, y2 = map(int, box)
#                 cropped_plate = img[y1:y2, x1:x2]
#                 if cropped_plate.size == 0:
#                     continue

#                 ocr_result = ocr.ocr(cropped_plate, cls=True)
#                 # Concatenate all detected words for the plate
#                 detected_text = " ".join([word_info[1][0] for line in ocr_result for word_info in line])
#                 break  # Use first detected plate only
#             if detected_text:
#                 break

#         if not detected_text:
#             detected_text = "No Number Plate Detected"

#         # Generate QR code with detected number plate text (or error message)
#         qr_image = generate_qr(detected_text)

#         return jsonify({
#             "number_plate": detected_text,
#             "qr_image": qr_image
#         })

#     except Exception as e:
#         print("Error:", e)
#         return jsonify({"error": str(e)}), 500

# if __name__ == "__main__":
#     app.run(debug=True, host="0.0.0.0", port=5000)


# from flask import Flask, request, jsonify
# from flask_cors import CORS
# import base64
# import cv2
# import numpy as np
# from ultralytics import YOLO
# from paddleocr import PaddleOCR
# import qrcode
# from io import BytesIO
# import datetime
# from pymongo import MongoClient

# app = Flask(__name__)
# CORS(app)
# app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

# # Initialize models
# model = YOLO("best.pt")
# ocr = PaddleOCR(use_angle_cls=True, lang="en")

# # MongoDB setup
# client = MongoClient("mongodb+srv://suryateja2neti:Suryateja@parksense.coocf1i.mongodb.net/")
# db = client["parksense"]
# qr_collection = db["qr_codes"]

# def decode_image(image_data):
#     try:
#         if ',' in image_data:
#             img_bytes = base64.b64decode(image_data.split(',')[1])
#         else:
#             img_bytes = base64.b64decode(image_data)
#         nparr = np.frombuffer(img_bytes, np.uint8)
#         img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
#         return img
#     except Exception as e:
#         print("Error decoding image:", e)
#         return None

# def generate_qr(data):
#     qr = qrcode.QRCode(version=1, box_size=10, border=2)
#     qr.add_data(data)
#     qr.make(fit=True)
#     img = qr.make_image(fill="black", back_color="white")
#     buffered = BytesIO()
#     img.save(buffered, format="PNG")
#     qr_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
#     return "data:image/png;base64," + qr_b64

# @app.route('/detect', methods=['POST'])
# def detect():
#     try:
#         data = request.get_json()
#         if not data or 'image' not in data:
#             return jsonify({"error": "No image provided"}), 400

#         image_data = data['image']
#         if len(image_data) > 10 * 1024 * 1024:  # 10MB
#             return jsonify({"error": "Image too large (max 10MB)"}), 413

#         img = decode_image(image_data)
#         if img is None:
#             return jsonify({"error": "Invalid image format"}), 400

#         # Run detection
#         results = model(img)
#         detected_text = None

#         for result in results:
#             boxes = result.boxes.xyxy.cpu().numpy()
#             for box in boxes:
#                 x1, y1, x2, y2 = map(int, box)
#                 cropped_plate = img[y1:y2, x1:x2]
#                 if cropped_plate.size == 0:
#                     continue
                
#                 ocr_result = ocr.ocr(cropped_plate, cls=True)
#                 detected_text = " ".join([word_info[1][0] for line in ocr_result for word_info in line]).replace(" ", "")
#                 break
#             if detected_text:
#                 break

#         if not detected_text:
#             detected_text = "NoNumberPlateDetected"

#         # Generate QR code
#         base_url = "http://172.168.0.152:5173/entry/"
#         qr_data = base_url + detected_text
#         qr_image = generate_qr(qr_data)

#         # Store in MongoDB
#         qr_collection.update_one(
#             {"plate_number": detected_text},
#             {
#                 "$set": {
#                     "plate_number": detected_text,
#                     "qr_image": qr_image,
#                     "created_at": datetime.datetime.utcnow()
#                 }
#             },
#             upsert=True
#         )

#         return jsonify({
#             "number_plate": detected_text,
#             "qr_image": qr_image
#         })

#     except Exception as e:
#         print("Server error:", e)
#         return jsonify({"error": "Internal server error"}), 500

# @app.route('/get-qr', methods=['GET'])
# def get_qr():
#     try:
#         plate_number = request.args.get("plate_number")
#         if not plate_number:
#             return jsonify({"error": "Missing plate_number"}), 400

#         record = qr_collection.find_one({"plate_number": plate_number})
#         if not record:
#             return jsonify({"error": "QR not found"}), 404

#         return jsonify({
#             "plate_number": record["plate_number"],
#             "qr_image": record["qr_image"]
#         })

#     except Exception as e:
#         print("Error retrieving QR:", e)
#         return jsonify({"error": "Database error"}), 500

# if __name__ == "__main__":
#     app.run(debug=True, host="0.0.0.0", port=5000)


# from flask import Flask, request, jsonify
# from pymongo import MongoClient
# from flask_cors import CORS

# app = Flask(__name__)
# CORS(app)

# client = MongoClient("mongodb+srv://suryateja2neti:Suryateja@parksense.coocf1i.mongodb.net/")
# parksense_db = client["parksense"]
# test_db = client["test"]

# license_plate_collection = parksense_db["license_plates"]
# slots_collection = test_db["slots"]

# def normalize_plate(plate):
#     return ' '.join(plate.upper().split())



# @app.route('/upload_plate', methods=['POST'])
# def upload_plate():
#     data = request.json

#     # Validate required fields
#     if 'license_plate' not in data:
#         return jsonify({"error": "license_plate is required"}), 400
#     if 'slot' not in data:
#         return jsonify({"error": "slot is required"}), 400

#     # Normalize plate for consistent storage
#     normalized_plate = normalize_plate(data['license_plate'])
#     data['license_plate'] = normalized_plate
#     new_slot = data['slot']

#     # Check if plate already exists in license_plates collection
#     existing_plate = license_plate_collection.find_one({"license_plate": normalized_plate})

#     # Check if plate exists in slots collection (case-insensitive)
#     slot_record = slots_collection.find_one({
#         "carNumber": {"$regex": f"^{normalized_plate}$", "$options": "i"}
#     })

#     if not slot_record:
#         # Plate NOT found in slots collection -> Unauthorized
#         data['unauthorized'] = True

#         if existing_plate:
#             # Update existing unauthorized record (timestamp, confidence, etc.)
#             license_plate_collection.update_one(
#                 {"_id": existing_plate["_id"]},
#                 {"$set": {**data, "unauthorized": True}}
#             )
#             return jsonify({"message": "Unauthorized plate updated in license_plate collection."}), 200
#         else:
#             # Insert new unauthorized plate record
#             license_plate_collection.insert_one(data)
#             return jsonify({"message": "Unauthorized plate inserted in license_plate collection."}), 200

#     # Plate found in slots collection -> Authorized

#     # Update slot number in slots collection if changed
#     if slot_record.get('slotNumber') != new_slot:
#         slots_collection.update_one(
#             {"_id": slot_record["_id"]},
#             {"$set": {"slotNumber": new_slot}}
#         )

#     if existing_plate:
#         # Update slot and mark authorized if slot changed or unauthorized was True
#         if existing_plate.get('slot') != new_slot or existing_plate.get('unauthorized', True):
#             license_plate_collection.update_one(
#                 {"_id": existing_plate["_id"]},
#                 {"$set": {"slot": new_slot, "unauthorized": False}}
#             )
#             return jsonify({"message": "Slot updated and plate marked authorized."}), 200
#         else:
#             return jsonify({"message": "Plate already exists, slot matches, no update needed."}), 200
#     else:
#         # Insert new authorized plate record
#         data['unauthorized'] = False
#         license_plate_collection.insert_one(data)
#         return jsonify({"message": "License plate uploaded and slot updated if needed."}), 200

# if __name__ == '__main__':
#     app.run(debug=True, host='0.0.0.0', port=5000)


# from flask import Flask, request, jsonify, send_from_directory
# from pymongo import MongoClient
# from flask_cors import CORS
# import os
# from datetime import datetime
# from werkzeug.utils import secure_filename

# app = Flask(__name__)
# CORS(app)

# # MongoDB setup
# client = MongoClient("mongodb+srv://suryateja2neti:Suryateja@parksense.coocf1i.mongodb.net/")
# parksense_db = client["parksense"]
# test_db = client["test"]

# license_plate_collection = parksense_db["license_plates"]
# slots_collection = test_db["slots"]

# # Upload folder for saving images
# UPLOAD_FOLDER = './uploads'
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# def normalize_plate(plate):
#     return ' '.join(plate.upper().split())

# @app.route('/upload_plate', methods=['POST'])
# def upload_plate():
#     plate = request.form.get('license_plate')
#     slot = request.form.get('slot')
#     confidence = request.form.get('confidence')

#     if not plate or not slot:
#         return jsonify({"error": "Missing required fields: license_plate or slot"}), 400

#     normalized_plate = normalize_plate(plate)
#     new_slot = slot

#     data = {
#         "license_plate": normalized_plate,
#         "slot": new_slot,
#         "confidence": float(confidence) if confidence else 0.0,
#         "timestamp": datetime.now()
#     }

#     # Save uploaded image file to disk and store path in DB
#     if 'image' in request.files:
#         image_file = request.files['image']
#         filename = secure_filename(f"{normalized_plate}_{int(datetime.now().timestamp())}.jpg")
#         filepath = os.path.join(UPLOAD_FOLDER, filename)
#         image_file.save(filepath)
#         data["imagePath"] = filepath  # Store file path relative to server

#     existing_plate = license_plate_collection.find_one({"license_plate": normalized_plate})

#     slot_record = slots_collection.find_one({
#         "carNumber": {"$regex": f"^{normalized_plate}$", "$options": "i"}
#     })

#     if not slot_record:
#         # Plate is unauthorized
#         data['unauthorized'] = True
#         if existing_plate:
#             license_plate_collection.update_one(
#                 {"_id": existing_plate["_id"]},
#                 {"$set": {**data, "unauthorized": True}}
#             )
#             return jsonify({"message": "Unauthorized plate updated."}), 200
#         else:
#             license_plate_collection.insert_one(data)
#             return jsonify({"message": "Unauthorized plate inserted."}), 200

#     # Plate is authorized
#     if slot_record.get('slotNumber') != new_slot:
#         slots_collection.update_one(
#             {"_id": slot_record["_id"]},
#             {"$set": {"slotNumber": new_slot}}
#         )

#     if existing_plate:
#         if existing_plate.get('slot') != new_slot or existing_plate.get('unauthorized', True):
#             license_plate_collection.update_one(
#                 {"_id": existing_plate["_id"]},
#                 {"$set": {"slot": new_slot, "unauthorized": False}}
#             )
#             return jsonify({"message": "Slot updated and plate marked authorized."}), 200
#         else:
#             return jsonify({"message": "Plate already exists, no update needed."}), 200
#     else:
#         data['unauthorized'] = False
#         license_plate_collection.insert_one(data)
#         return jsonify({"message": "License plate uploaded and marked authorized."}), 200

# # Optional: Serve uploaded images via HTTP
# @app.route('/uploads/<filename>')
# def serve_image(filename):
#     return send_from_directory(UPLOAD_FOLDER, filename)

# if __name__ == '__main__':
#     app.run(debug=True, host='0.0.0.0', port=5000)


# from flask import Flask, request, jsonify
# from pymongo import MongoClient
# from flask_cors import CORS
# import base64
# from datetime import datetime

# app = Flask(__name__)  # ✅ Fixed: __name_ instead of name
# CORS(app)

# # MongoDB setup
# client = MongoClient("mongodb+srv://suryateja2neti:Suryateja@parksense.coocf1i.mongodb.net/")
# parksense_db = client["parksense"]
# test_db = client["test"]

# license_plate_collection = parksense_db["license_plates"]
# slots_collection = test_db["slots"]

# def normalize_plate(plate):
#     return ' '.join(plate.upper().split())

# @app.route('/upload_plate', methods=['POST'])
# def upload_plate():
#     data = request.get_json()  # ✅ Accept JSON data

#     if not data:
#         return jsonify({"error": "No JSON payload received"}), 400

#     plate = data.get('license_plate')
#     slot = data.get('slot')
#     confidence = data.get('confidence')
#     image_base64 = data.get('image')  # ✅ base64 image from JSON

#     if not plate or not slot:
#         return jsonify({"error": "Missing required fields: license_plate or slot"}), 400

#     normalized_plate = normalize_plate(plate)
#     new_slot = slot

#     record = {
#         "license_plate": normalized_plate,
#         "slot": new_slot,
#         "confidence": float(confidence) if confidence else 0.0,
#         "timestamp": datetime.now()
#     }

#     if image_base64:
#         record["imageBase64"] = image_base64

#     # Check if plate is authorized
#     slot_record = slots_collection.find_one({
#         "carNumber": {"$regex": f"^{normalized_plate}$", "$options": "i"}
#     })

#     existing_plate = license_plate_collection.find_one({
#         "license_plate": normalized_plate
#     })

#     if not slot_record:
#         # Plate is unauthorized
#         record['unauthorized'] = True
#         if existing_plate:
#             license_plate_collection.update_one(
#                 {"_id": existing_plate["_id"]},
#                 {"$set": {**record, "unauthorized": True}}
#             )
#             return jsonify({"message": "Unauthorized plate updated."}), 200
#         else:
#             license_plate_collection.insert_one(record)
#             return jsonify({"message": "Unauthorized plate inserted."}), 200

#     # Plate is authorized
#     correct_slot = slot_record.get('slotNumber')
#     if correct_slot != new_slot:
#         slots_collection.update_one(
#             {"_id": slot_record["_id"]},
#             {"$set": {"slotNumber": new_slot}}
#         )

#     if existing_plate:
#         update_needed = (
#             existing_plate.get('slot') != new_slot or
#             existing_plate.get('unauthorized', True)
#         )
#         if update_needed:
#             update_fields = {
#                 "slot": new_slot,
#                 "unauthorized": False
#             }
#             if image_base64:
#                 update_fields["imageBase64"] = image_base64

#             license_plate_collection.update_one(
#                 {"_id": existing_plate["_id"]},
#                 {"$set": update_fields}
#             )
#             return jsonify({"message": "Slot updated and plate marked authorized."}), 200
#         else:
#             return jsonify({"message": "Plate already exists, no update needed."}), 200
#     else:
#         record['unauthorized'] = False
#         license_plate_collection.insert_one(record)
#         return jsonify({"message": "License plate uploaded and marked authorized."}), 200

# if __name__ == '__main__':  # ✅ Fixed: 'main_'
#     app.run(debug=True, host='0.0.0.0', port=5000)

# app.py



# from flask import Flask, request, jsonify
# from pymongo import MongoClient
# from flask_cors import CORS
# import base64
# from datetime import datetime

# app = Flask(__name__)
# CORS(app)

# client = MongoClient("mongodb+srv://suryateja2neti:Suryateja@parksense.coocf1i.mongodb.net/")
# parksense_db = client["parksense"]
# test_db = client["test"]

# license_plate_collection = parksense_db["license_plates"]
# slots_collection = test_db["slots"]

# def normalize_plate(plate):
#     return ' '.join(plate.upper().split())

# @app.route('/upload_plate', methods=['POST'])
# def upload_plate():
#     data = request.get_json()
#     print("Hi")
#     if not data:
#         return jsonify({"error": "No JSON payload received"}), 400

#     plate = data.get('license_plate')
#     slot = data.get('slot')
#     confidence = data.get('confidence')
#     image_base64 = data.get('image')

#     if not plate or not slot or float(confidence) < 0.8:
#         return jsonify({"error": "Invalid or low-confidence data"}), 400

#     normalized_plate = normalize_plate(plate)
#     new_slot = slot

#     record = {
#         "license_plate": normalized_plate,
#         "slot": new_slot,
#         "confidence": float(confidence),
#         "timestamp": datetime.now()
#     }

#     if image_base64:
#         record["imageBase64"] = image_base64

#     slot_record = slots_collection.find_one({
#         "carNumber": {"$regex": f"^{normalized_plate}$", "$options": "i"}
#     })

#     existing_plate = license_plate_collection.find_one({
#         "license_plate": normalized_plate
#     })

#     if not slot_record:
#         record['unauthorized'] = True
#         if existing_plate:
#             license_plate_collection.update_one(
#                 {"_id": existing_plate["_id"]},
#                 {"$set": {**record, "unauthorized": True}}
#             )
#             return jsonify({"message": "Unauthorized plate updated."}), 200
#         else:
#             license_plate_collection.insert_one(record)
#             return jsonify({"message": "Unauthorized plate inserted."}), 200

#     correct_slot = slot_record.get('slotNumber')
#     if correct_slot != new_slot:
#         slots_collection.update_one(
#             {"_id": slot_record["_id"]},
#             {"$set": {"slotNumber": new_slot}}
#         )

#     if existing_plate:
#         update_needed = (
#             existing_plate.get('slot') != new_slot or
#             existing_plate.get('unauthorized', True)
#         )
#         if update_needed:
#             update_fields = {
#                 "slot": new_slot,
#                 "unauthorized": False
#             }
#             if image_base64:
#                 update_fields["imageBase64"] = image_base64

#             license_plate_collection.update_one(
#                 {"_id": existing_plate["_id"]},
#                 {"$set": update_fields}
#             )
#             return jsonify({"message": "Slot updated and plate marked authorized."}), 200
#         else:
#             return jsonify({"message": "Plate already exists, no update needed."}), 200
#     else:
#         record['unauthorized'] = False
#         license_plate_collection.insert_one(record)
#         return jsonify({"message": "License plate uploaded and marked authorized."}), 200

# if __name__ == '__main__':
#     app.run(debug=True, host='0.0.0.0', port=5000)
