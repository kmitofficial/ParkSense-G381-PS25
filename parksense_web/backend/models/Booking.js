const mongoose = require('mongoose');

const bookingSchema = new mongoose.Schema({
  phoneNumber: {
    type: String,
    required: true
  },
  carNumber: {
    type: String,
    required: true
  },
  slotNumber: {
    type: String,
    required: true
  },
  bookedAt: {
    type: Date,
    default: Date.now
  },
  isActive: {
    type: Boolean,
    default: true
  }
});

module.exports = mongoose.model('Booking', bookingSchema);
