const express = require('express');
const router = express.Router();
const LicensePlate = require('../models/LicensePlate');
const Student = require('../models/Student');
const Faculty = require('../models/Faculty');
const UnauthorizedVehicle = require('../models/Unauthorized');

router.post('/check', async (req, res) => {
  try {
    const { carNumber } = req.body;
    
    // Check authorization
    const student = await Student.findOne({ carNumber });
    if (student) {
      return res.json({ authorized: true, userType: 'student', details: student });
    }
    
    const faculty = await Faculty.findOne({ carNumber });
    if (faculty) {
      return res.json({ authorized: true, userType: 'faculty', details: faculty });
    }
    
    // If unauthorized
    const scannedPlate = await LicensePlate.findOne({ carNumber });
    if (!scannedPlate) {
      return res.status(404).json({ error: 'License plate not scanned' });
    }
    
    const unauthorizedVehicle = await UnauthorizedVehicle.create({
      carNumber,
      location: scannedPlate.location || 'Main Parking',
      imageUrl: scannedPlate.imageUrl,
      status: 'pending'
    });
    
    res.json({ 
      authorized: false,
      vehicle: unauthorizedVehicle
    });
    
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;