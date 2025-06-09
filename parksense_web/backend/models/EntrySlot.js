const mongoose = require("mongoose");

const slotSchema = new mongoose.Schema({
  slotNumber: { type: String, required: true },  // e.g., 'A1', 'A2'
  isBooked: { type: Boolean, default: false },
  carNumber: { type: String },
  phone: { type: String },
  bookedAt: { type: Date },
  exitedAt: { type: Date },
});

module.exports = mongoose.model("Slot", slotSchema);
