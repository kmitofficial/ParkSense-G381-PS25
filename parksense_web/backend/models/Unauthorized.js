// models/Unauthorized.js
const mongoose = require('mongoose');

const unauthorizedSchema = new mongoose.Schema({
  plate: { type: String, required: true, unique: true },  // license plate number
  detectedAt: { type: Date, default: Date.now },
  imageUrl: String,     // optional: store car image URL if you have it
  confidence: Number,   // optional: confidence score from plate recognition
});

module.exports = mongoose.models.Unauthorized || mongoose.model('Unauthorized', unauthorizedSchema);
