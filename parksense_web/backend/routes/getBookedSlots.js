const express = require("express");
const router = express.Router();
const Slot = require("../models/Slot");

router.get("/", async (req, res) => {
  try {
    const type = req.query.type || 'faculty';
    const totalSlots = 24;
    const bookedSlotsCount = await Slot.countDocuments({ userType: type });
    
    res.status(200).json({
      totalSlots,
      bookedSlots: bookedSlotsCount,
      availableSlots: totalSlots - bookedSlotsCount,
    });
  } catch (error) {
    console.error("Error fetching booked slots:", error);
    res.status(500).json({ message: "Server error" });
  }
});

module.exports = router;