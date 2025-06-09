const express = require('express');
const router = express.Router();

const ADMIN_USERNAME = 'admin';
const ADMIN_PASSWORD = '12345';

router.post('/', (req, res) => {
  const { un, pass } = req.body;

  if (un === ADMIN_USERNAME && pass === ADMIN_PASSWORD) {
    return res.status(200).json({ msg: 'Admin login successful', token: 'adminToken' });
  } else {
    return res.status(401).json({ msg: 'Invalid admin credentials' });
  }
});

module.exports = router;
