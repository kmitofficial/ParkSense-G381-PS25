const mongoose = require('mongoose');

const testDB = mongoose.createConnection('mongodb+srv://suryateja2neti:Suryateja@parksense.coocf1i.mongodb.net/test', {
  useNewUrlParser: true,
  useUnifiedTopology: true,
});

const parksenseDB = mongoose.createConnection('mongodb+srv://suryateja2neti:Suryateja@parksense.coocf1i.mongodb.net/parksense', {
  useNewUrlParser: true,
  useUnifiedTopology: true,
});

module.exports = { testDB, parksenseDB };
