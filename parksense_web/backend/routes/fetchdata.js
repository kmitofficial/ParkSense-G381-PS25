const mongoose = require('mongoose');
const Slot = require('../models/Slot');  

const uri = 'mongodb+srv://suryateja2neti:Suryateja@parksense.coocf1i.mongodb.net/test?retryWrites=true&w=majority';

mongoose.connect(uri)
  .then(async () => {
    console.log('Connected to MongoDB Atlas');

    try {
      const slots = await Slot.find({});
      console.log('\n--- Slot Details ---');
      console.log(slots);
    } catch (err) {
      console.error('Error fetching slots data:', err);
    } finally {
      mongoose.connection.close();
    }
  })
  .catch(err => {
    console.error('MongoDB connection error:', err);
  });
