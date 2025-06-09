// const express = require('express');
// const mongoose = require('mongoose');
// const cors = require('cors');
// require('dotenv').config();

// const studentLogin = require('./routes/studentlogin');
// const facultyLogin = require('./routes/facultylogin');
// const adminLogin = require('./routes/adminlogin');
// const register = require('./routes/register');
// const studentRegister = require('./routes/studentregister');
// const bookingRoutes = require('./routes/booking');
// const slotsRoutes = require('./routes/slot');
// const fetchingslotRoutes = require('./routes/slots');
// const getBookedSlots = require("./routes/getBookedSlots");
// const unauthorizedRoutes = require('./routes/unauthorized');
// const entryRoutes = require('./routes/parking');

// const app = express();

// // ✅ TEMPORARY: Allow all origins for testing (use specific origins in production)
// app.use(cors({
//   origin: ["http://localhost:5173"] , // or use ["http://localhost:5173", "http://192.168.1.33:5173"] when ready
//   methods: ['GET', 'POST', 'PATCH'],
//   allowedHeaders: ['Content-Type', 'Authorization'],
// }));

// app.use(express.json());

// // ✅ Mount routes
// app.use('/api/entry', entryRoutes); 
// app.use('/api/studentlogin', studentLogin);
// app.use('/api/facultylogin', facultyLogin);
// app.use('/api/adminlogin', adminLogin);
// app.use('/api/register', register);
// app.use('/api/studentregister', studentRegister);
// app.use('/api/booking', bookingRoutes);
// app.use('/api/slots', fetchingslotRoutes);     // Route for GET /api/slots
// app.use('/api/slot', slotsRoutes);             // e.g., POST /api/slot/add
// app.use('/api/getBookedSlots', getBookedSlots);
// app.use('/api/unauthorized', unauthorizedRoutes);
// // confirm_booking lives inside here

// // ✅ Health check route
// app.get("/", (req, res) => {
//   res.send("Welcome to the booking system");
// });

// // ✅ MongoDB connection
// mongoose.connect(process.env.MONGO_URI, {
//   useNewUrlParser: true,
//   useUnifiedTopology: true,
// })
// .then(() => console.log('Connected to MongoDB'))
// .catch(err => console.error('MongoDB connection error:', err));

// // ✅ Start server
// const PORT = process.env.PORT || 5000;
// app.listen(PORT,'0.0.0.0', () => {
//   console.log(`Server running on http://localhost:${PORT}`);
// });

const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');

require('dotenv').config();

const studentLogin = require('./routes/studentlogin');
const facultyLogin = require('./routes/facultylogin');
const adminLogin = require('./routes/adminlogin');
const register = require('./routes/register');
const studentRegister = require('./routes/studentregister');
const bookingRoutes = require('./routes/booking');
const slotsRoutes = require('./routes/slot');
const fetchingslotRoutes = require('./routes/slots');
const getBookedSlots = require("./routes/getBookedSlots");
const unauthorizedRoutes = require('./routes/unauthorized');
const entryRoutes = require('./routes/parking');
const licenseplateroutes = require("./routes/licensePlateRoutes");
const app = express();

const corsOptions = {
  origin: [
    "http://localhost:5173", 
    "http://172.168.0.152:5173",
    "http://192.168.1.37:5173",
    "http://172.168.0.67:5173",
    "https://parksense-frontend-omega.vercel.app",
    /https:\/\/.*\.ngrok\.io$/, 
  ],
  methods: ['GET', 'POST','PATCH', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  credentials: true,
};

app.use(cors(corsOptions));
app.use(express.json());
app.use('/api/entry', entryRoutes);
app.use('/api/studentlogin', studentLogin);
app.use('/api/facultylogin', facultyLogin);
app.use('/api/adminlogin', adminLogin);
app.use('/api/register', register);
app.use('/api/studentregister', studentRegister);
app.use('/api/booking', bookingRoutes);
app.use('/api', slotsRoutes);
app.use('/api/slots', fetchingslotRoutes);
app.use("/api/getBookedSlots", getBookedSlots);
app.get("/",(req,res)=>{
  return res.send("Welcome to the booking system");
})  
app.use('/', unauthorizedRoutes);
app.use("/api/admin",licenseplateroutes);
mongoose.connect(process.env.MONGO_URI, {
  useNewUrlParser: true,
  useUnifiedTopology: true,
})
  .then(() => console.log('Connected to MongoDB'))
  .catch(err => console.error('MongoDB connection error:', err));

mongoose.connection.once("open", () => {
  console.log("✅ Connected to DB:", mongoose.connection.name); // should print "parksense"
});


const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
