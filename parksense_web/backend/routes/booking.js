const express = require('express');
const router = express.Router();
const Booking = require('../models/Booking');

router.post('/', async (req, res) => {
  try {
    const { phoneNumber, carNumber, slotNumber } = req.body;

    const existing = await Booking.findOne({ slotNumber, isActive: true });
    if (existing) return res.status(400).json({ message: 'Slot already booked' });

    const booking = new Booking({ phoneNumber, carNumber, slotNumber });
    await booking.save();

    setTimeout(async () => {
      const latest = await Booking.findById(booking._id);
      if (latest && latest.isActive) {
        latest.isActive = false;
        await latest.save();
        console.log(`Slot ${latest.slotNumber} auto-released after 30 mins.`);
      }
    }, 30 * 60 * 1000); 

    res.status(201).json({ message: 'Slot booked successfully', booking });
  } catch (err) {
    res.status(500).json({ message: 'Error booking slot', error: err.message });
  }
});

router.get('/active', async (req, res) => {
  try {
    const bookings = await Booking.find({ isActive: true });
    res.json(bookings);
  } catch (err) {
    res.status(500).json({ message: 'Error fetching bookings', error: err.message });
  }
});
router.post('/unbook', async (req, res) => {
  try {
    const { slotNumber } = req.body;
    const booking = await Booking.findOne({ slotNumber, isActive: true });
    if (!booking) return res.status(404).json({ message: 'Active booking not found' });

    booking.isActive = false;
    await booking.save();

    res.json({ message: 'Slot unbooked successfully' });
  } catch (err) {
    res.status(500).json({ message: 'Error unbooking slot', error: err.message });
  }
});

module.exports = router;
