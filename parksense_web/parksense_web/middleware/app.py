
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


from flask import Flask, request, jsonify, send_from_directory
from pymongo import MongoClient
from flask_cors import CORS
import os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# MongoDB setup
client = MongoClient("mongodb+srv://suryateja2neti:Suryateja@parksense.coocf1i.mongodb.net/")
parksense_db = client["parksense"]
test_db = client["test"]

license_plate_collection = parksense_db["license_plates"]
slots_collection = test_db["slots"]

# Upload folder for saving images
UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def normalize_plate(plate):
    return ' '.join(plate.upper().split())

@app.route('/upload_plate', methods=['POST'])
def upload_plate():
    plate = request.form.get('license_plate')
    slot = request.form.get('slot')
    confidence = request.form.get('confidence')

    if not plate or not slot:
        return jsonify({"error": "Missing required fields: license_plate or slot"}), 400

    normalized_plate = normalize_plate(plate)
    new_slot = slot

    data = {
        "license_plate": normalized_plate,
        "slot": new_slot,
        "confidence": float(confidence) if confidence else 0.0,
        "timestamp": datetime.now()
    }

    # Save uploaded image file to disk and store path in DB
    if 'image' in request.files:
        image_file = request.files['image']
        filename = secure_filename(f"{normalized_plate}_{int(datetime.now().timestamp())}.jpg")
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        image_file.save(filepath)
        data["imagePath"] = filepath  # Store file path relative to server

    existing_plate = license_plate_collection.find_one({"license_plate": normalized_plate})

    slot_record = slots_collection.find_one({
        "carNumber": {"$regex": f"^{normalized_plate}$", "$options": "i"}
    })

    if not slot_record:
        # Plate is unauthorized
        data['unauthorized'] = True
        if existing_plate:
            license_plate_collection.update_one(
                {"_id": existing_plate["_id"]},
                {"$set": {**data, "unauthorized": True}}
            )
            return jsonify({"message": "Unauthorized plate updated."}), 200
        else:
            license_plate_collection.insert_one(data)
            return jsonify({"message": "Unauthorized plate inserted."}), 200

    # Plate is authorized
    if slot_record.get('slotNumber') != new_slot:
        slots_collection.update_one(
            {"_id": slot_record["_id"]},
            {"$set": {"slotNumber": new_slot}}
        )

    if existing_plate:
        if existing_plate.get('slot') != new_slot or existing_plate.get('unauthorized', True):
            license_plate_collection.update_one(
                {"_id": existing_plate["_id"]},
                {"$set": {"slot": new_slot, "unauthorized": False}}
            )
            return jsonify({"message": "Slot updated and plate marked authorized."}), 200
        else:
            return jsonify({"message": "Plate already exists, no update needed."}), 200
    else:
        data['unauthorized'] = False
        license_plate_collection.insert_one(data)
        return jsonify({"message": "License plate uploaded and marked authorized."}), 200

# Optional: Serve uploaded images via HTTP
@app.route('/uploads/<filename>')
def serve_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

