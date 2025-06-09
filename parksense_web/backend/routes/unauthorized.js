const express = require('express');
const router = express.Router();
const { testDB, parksenseDB } = require('../models/dbConnections');

// Import schemas
const studentSchema = require('../models/Student').schema;
const facultySchema = require('../models/Faculty').schema;
const licensePlateSchema = require('../models/LicensePlate').schema;

// Models with explicit collection name for LicensePlate
const Student = testDB.model('Student', studentSchema);
const Faculty = testDB.model('Faculty', facultySchema);
const LicensePlate = parksenseDB.model('LicensePlate', licensePlateSchema, 'license_plates'); // explicit
const SlotCollection = testDB.collection('slots');

// Helper to normalize plate strings
const normalizePlate = (plate) =>
  plate.replace(/\s+/g, ' ').trim().toUpperCase();

// GET all scanned plates, classify authorized and unauthorized
router.get('/check-plates', async (req, res) => {
  try {
    const scannedPlates = await LicensePlate.find();
    console.log('Scanned Plates:', scannedPlates);

    const studentCars = await Student.find().select('carNumber -_id');
    const facultyCars = await Faculty.find().select('carNumber -_id');

    const authorizedSet = new Set([
      ...studentCars.map(s => normalizePlate(s.carNumber)),
      ...facultyCars.map(f => normalizePlate(f.carNumber)),
    ]);

    console.log('Student Cars:', [...studentCars.map(s => s.carNumber)]);
    console.log('Faculty Cars:', [...facultyCars.map(f => f.carNumber)]);

    const authorized = [];
    const unauthorized = [];

    for (const plateObj of scannedPlates) {
      const plate = normalizePlate(plateObj.license_plate);
      if (authorizedSet.has(plate)) {
        if (!authorized.includes(plate)) authorized.push(plate);
      } else {
        // Filter out resolved unauthorized plates (optional)
        if (plateObj.status !== 'resolved' || plateObj.unauthorized === true) {
          unauthorized.push({
            license_plate: plate,
            confidence: plateObj.confidence,
            _id: plateObj._id,
            slot: plateObj.slot || '',
            reportedAt: plateObj.createdAt || plateObj.reportedAt || '',
            action: plateObj.action || '',
            status: plateObj.status || '',
          });
          console.log('Unauthorized plate:', plate);
        }
      }
    }

    res.json({
      success: true,
      authorized,
      unauthorized,
      unauthorizedCount: unauthorized.length,
    });

  } catch (error) {
    console.error('Error in /check-plates:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to check license plates',
      error: error.message,
    });
  }
});

router.patch('/check-plates/:license_plate', async (req, res) => {
  try {
    console.log('PATCH /check-plates/:license_plate body:', req.body);

    const { license_plate } = req.params;
    const { action, status, correctedCarNumber } = req.body;

    if (!action || !status) {
      return res.status(400).json({ success: false, message: 'Action and status required' });
    }

    // Use corrected number if provided, otherwise original
    const plateToUpdate = correctedCarNumber || license_plate;
    const normalizedPlate = normalizePlate(plateToUpdate);
    const originalNormalizedPlate = normalizePlate(license_plate);

    // 1. Update license_plates collection
    const updatedPlate = await LicensePlate.findOneAndUpdate(
      { license_plate: { $regex: `^${originalNormalizedPlate}$`, $options: 'i' } },
      {
        $set: {
          license_plate: normalizedPlate,
          userType: action,
          status: status,
          unauthorized: false,
          updatedByAdmin: true,
        }
      },
      { new: true }
    );

    if (!updatedPlate) {
      return res.status(404).json({ success: false, message: 'License plate not found' });
    }

    // 2. Get phone number - prioritize corrected number lookup
    let phoneNumber = 'updated by admin';
    let foundUser = null;
    
    if (action === 'faculty') {
      // First check corrected number (if provided)
      if (correctedCarNumber) {
        foundUser = await Faculty.findOne({
          carNumber: { $regex: `^${normalizedPlate}$`, $options: 'i' }
        });
      }
      // If not found, check original number
      if (!foundUser) {
        foundUser = await Faculty.findOne({
          carNumber: { $regex: `^${originalNormalizedPlate}$`, $options: 'i' }
        });
      }
      if (foundUser) phoneNumber = foundUser.phoneNumber;
    } 
    else if (action === 'student') {
      // First check corrected number (if provided)
      if (correctedCarNumber) {
        foundUser = await Student.findOne({
          carNumber: { $regex: `^${normalizedPlate}$`, $options: 'i' }
        });
      }
      // If not found, check original number
      if (!foundUser) {
        foundUser = await Student.findOne({
          carNumber: { $regex: `^${originalNormalizedPlate}$`, $options: 'i' }
        });
      }
      if (foundUser) phoneNumber = foundUser.phoneNumber;
    }

    // 3. Update slots collection
    const slotUpdateResult = await SlotCollection.updateOne(
      { 
        $or: [
          { carNumber: { $regex: `^${originalNormalizedPlate}$`, $options: 'i' } },
          { slotNumber: updatedPlate.slot }
        ]
      },
      {
        $set: {
          carNumber: normalizedPlate,
          slotNumber: updatedPlate.slot || 'UNKNOWN',
          userType: action,
          updatedByAdmin: true,
          phoneNumber: phoneNumber,
        }
      },
      { upsert: true }
    );

    res.json({
      success: true,
      message: `Vehicle updated to ${action} parking`,
      updatedPlate: {
        license_plate: normalizedPlate,
        userType: action,
        status: status,
        phoneNumber: phoneNumber // Include the phone number in response
      }
    });

  } catch (error) {
    console.error('Error updating license plate:', error);
    res.status(500).json({ 
      success: false, 
      message: 'Server error',
      error: error.message 
    });
  }
});
module.exports = router;
