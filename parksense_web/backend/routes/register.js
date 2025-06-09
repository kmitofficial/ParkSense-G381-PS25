const express = require('express');
const bcrypt = require('bcryptjs'); 
const router = express.Router();
const User = require('../models/Faculty'); 

router.post('/', async (req, res) => {
  const { phone, carNumber, password, confirmPassword } = req.body;

  if (!phone || phone.trim() === '') {
    return res.status(400).json({ msg: 'Phone number is required' });
  }
  if (!carNumber || carNumber.trim() === '') {
    return res.status(400).json({ msg: 'Car number is required' });
  }
  if (!password || password.trim() === '') {
    return res.status(400).json({ msg: 'Password is required' });
  }
  if (password !== confirmPassword) {
    return res.status(400).json({ msg: 'Passwords do not match' });
  }

  try {
    const existingUser = await User.findOne({ phone });
    if (existingUser) {
      return res.status(400).json({ msg: 'Phone number already registered' });
    }

    const hashedPassword = await bcrypt.hash(password, 10); 

    const newUser = new User({
      phone,
      carNumber,
      password: hashedPassword, 
    });

    await newUser.save();
    return res.status(201).json({ msg: 'Registration successful' });

  } catch (err) {
    console.error('Error during registration:', err);
    return res.status(500).json({ msg: 'Server error' });
  }
});

module.exports = router;
