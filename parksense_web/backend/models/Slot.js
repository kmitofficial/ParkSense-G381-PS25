// const mongoose = require('mongoose');

// const SlotSchema = new mongoose.Schema({
//   slotNumber: {
//     type: String,
//     required: true,
//     unique: true
//   },
//   phoneNumber: {
//     type: String,
//     required: true
//   },
//   carNumber: {
//     type: String,
//     required: true
//   },
//   userType: {
//     type: String,
//     immutable: true
//   },
//   bookedAt: {
//     type: Date,
//     default: Date.now 
//   },
//   updatedByAdmin:{
//     type: Boolean,
//     default: false
//   }
// });

// module.exports = mongoose.model('Slot', SlotSchema);

// models/Slot.js\


// const mongoose = require("mongoose");

// const slotSchema = new mongoose.Schema({
//   slotNumber: String,
//   isBooked: { type: Boolean, default: false },
//   carNumber: { type: String, default: null },
//   phone: { type: String, default: null },
// });

// module.exports = mongoose.model("Slot", slotSchema);

const mongoose = require("mongoose");

const slotSchema = new mongoose.Schema({
  slotNumber: { type: String, required: true },  // e.g., 'A1', 'A2'
  isBooked: { type: Boolean, default: false },
  carNumber: { type: String },
  phone: { type: String ,default:new Date().toISOString()},
  bookedAt: { type: Date },
  exitedAt: { type: Date },
  status: { type: String, enum: ["available", "occupied"], default: "available" }
});

module.exports = mongoose.model("Slot", slotSchema);
