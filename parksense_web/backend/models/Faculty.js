const mongoose = require('mongoose');

const facultySchema = new mongoose.Schema({
  phone: { 
    type: String, 
    required: true, 
    unique: true,
    trim: true
  },
  carNumber: { 
    type: String, 
    required: true,
    trim: true
  },
  password: { 
    type: String, 
    required: true
  }
}, { timestamps: true });

module.exports = mongoose.model('Faculty', facultySchema);
