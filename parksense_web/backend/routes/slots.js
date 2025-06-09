const express = require('express');
const router = express.Router();
const Slot = require('../models/Slot');

router.get('/occupied', async (req, res) => {
  try {
    const slots = await Slot.find({});
    const formattedSlots = slots.map(slot => ({
      slotNumber: slot.slotNumber,
      carNumber: slot.carNumber,
      userType: slot.userType,
      phoneNumber: slot.phoneNumber,
      bookedAt:slot.bookedAt,
      updatedByAdmin:slot.updatedByAdmin || false,
    }));
    res.json(formattedSlots);
  } catch (err) {
    res.status(500).json({ error: 'Error fetching slots', details: err.message });
  }
});

module.exports = router;