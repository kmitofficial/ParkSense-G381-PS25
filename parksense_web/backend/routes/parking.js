const express = require("express");
const router = express.Router();
const jwt = require("jsonwebtoken");
const Slot = require("../models/Slot");
const LicensePlate = require("../models/LicensePlate");
const asyncHandler = require("express-async-handler");

const JWT_SECRET = process.env.JWT_SECRET || "your_secret_key_should_be_complex";

// Faculty parking slots configuration
const FACULTY_ROWS = ['A', 'B', 'C', 'D'];
const SLOTS_PER_ROW = 6;

// Helper function to find next available faculty slot
const findNextFacultySlot = async () => {
  const bookedSlots = await Slot.find({ isBooked: true });

  const slotMatrix = {};
  FACULTY_ROWS.forEach(row => {
    slotMatrix[row] = Array(SLOTS_PER_ROW).fill(false);
  });

  bookedSlots.forEach(slot => {
    const row = slot.slotNumber.charAt(0);
    const num = parseInt(slot.slotNumber.substring(1));
    if (FACULTY_ROWS.includes(row) && num <= SLOTS_PER_ROW) {
      slotMatrix[row][num - 1] = true;
    }
  });

  for (const row of FACULTY_ROWS) {
    for (let i = 0; i < SLOTS_PER_ROW; i++) {
      if (!slotMatrix[row][i]) {
        return `${row}${i + 1}`;
      }
    }
  }
  return null;
};

// POST /confirm_booking - Assigns a slot and returns JWT
router.post("/confirm_booking", asyncHandler(async (req, res) => {
  const { car_number, phone } = req.body;
  console.log("Confirm booking route")
  if (!car_number || !phone) {
    return res.status(400).json({
      success: false,
      msg: "Car number and phone number are required"
    });
  }

  // Check for existing slot by phone
  const existingSlot = await Slot.findOne({ phone, isBooked: true });
  if (existingSlot) {
    const token = jwt.sign(
      {
        car_number,
        phone,
        slot: existingSlot.slotNumber,
        bookingId: existingSlot._id,
        exp: Math.floor(Date.now() / 1000) + (6 * 60 * 60)
      },
      JWT_SECRET
    );

    return res.json({
      success: true,
      token,
      slot: existingSlot.slotNumber,
      message: "Existing booking found",
      carNumber: car_number,
      phonenumber: phone
    });
  }

  // Get next available faculty slot
  const slotNumber = await findNextFacultySlot();
  if (!slotNumber) {
    return res.status(404).json({
      success: false,
      msg: "No available faculty parking slots"
    });
  }

  const utcDate = new Date(); 
  const formattedISTTime = utcDate.toISOString().slice(0, 19).replace("T", " ");

  // Book slot in database
  const slot = await Slot.findOneAndUpdate(
    { slotNumber },
    {
      isBooked: true,
      carNumber: car_number,
      phone,
      bookedAt: formattedISTTime
    },
    { new: true, upsert: true }
  );

  // Update license plate collection
try {
  await LicensePlate.updateOne(
    { plate: car_number },
    {
      $set: {
        phone,
        slotId: slot._id,
        bookedAt: formattedISTTime,
        status: "booked"
      }
    },
    { upsert: true }
  );
} catch (err) {
  console.error("Error in LicensePlate.updateOne:", err);
}


  // Generate JWT token
  const token = jwt.sign(
    {
      car_number,
      phone,
      slot: slot.slotNumber,
      bookingId: slot._id,
      exp: Math.floor(Date.now() / 1000) + (6 * 60 * 60)
    },
    JWT_SECRET
  );

  // Send response
  res.json({
    success: true,
    token,
    slot: slot.slotNumber,
    expiresIn: "6h",
    bookingDetails: {
      carNumber: car_number,
      phone,
      bookedAt: formattedISTTime,
      slotNumber: slot.slotNumber
    }
  });
}));

module.exports = router;
