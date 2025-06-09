const express = require('express');
const app = express();

app.get("/", (req, res) => {
  res.send("Welcome to the booking system");
});

const PORT = 5000;
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
