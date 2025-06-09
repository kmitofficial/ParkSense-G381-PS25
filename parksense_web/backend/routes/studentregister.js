const express = require('express');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const Student = require('../models/Student'); 

const router = express.Router();

router.post('/', async (req, res) => {
  const { phone, carNumber, password } = req.body;

  try {
    const existingStudent = await Student.findOne({ phone });
    if (existingStudent) {
      return res.status(400).json({ message: 'Student already registered' });
    }

    const hashedPassword = await bcrypt.hash(password, 10);

    const student = new Student({
      phone,
      carNumber,
      password: hashedPassword,
    });

    await student.save();

    const token = jwt.sign({ id: student._id, role: 'student' }, process.env.JWT_SECRET, { expiresIn: '1h' });

    res.status(201).json({ message: 'Registration successful', token });
  } catch (error) {
    console.error('Registration error:', error);
    res.status(500).json({ message: 'Server error' });
  }
});

module.exports = router;
