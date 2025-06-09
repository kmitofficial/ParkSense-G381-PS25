const express = require('express');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const Faculty = require('../models/Faculty'); 
const router = express.Router();
router.post('/', async (req, res) => {
  const { phone, password } = req.body;
  // res.status(200).json({ message: "Hello from Vercel backend!" });
  console.log("Received phone: ", phone); 

  try {
    const faculty = await Faculty.findOne({ phone });

    if (!faculty) {
      return res.status(400).json({ msg: 'Phone number not found' });
    }

    const isMatch = await bcrypt.compare(password, faculty.password);
    if (!isMatch) {
      return res.status(401).json({ msg: 'Incorrect password' });
    }

    const token = jwt.sign(
      { id: faculty._id, phone: faculty.phone },
      process.env.JWT_SECRET, 
      { expiresIn: '1h' }
    );
    return res.status(200).json({
      msg: 'Login successful',
      user: {
        id: faculty._id,
        phone: faculty.phone,
        carNumber: faculty.carNumber, 
      },
      token,
      role: 'faculty',
    });
  } catch (err) {
    console.error('Login error:', err.message);
    return res.status(500).json({ msg: 'Internal server error' });
  }
});

module.exports = router;
