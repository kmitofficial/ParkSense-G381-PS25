import React, { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Car } from "lucide-react";

function EntryForm() {
  const navigate = useNavigate();
  const { carNumber } = useParams(); // Get car number from route
  const [phoneNumber, setPhoneNumber] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    const data = {
      car_number: carNumber,
      phone: phoneNumber,
    };

    try {
      const response = await fetch("http://localhost:5000/api/confirm_booking", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });

      const result = await response.json();

      if (response.status === 200) {
        // Redirect to dashboard with token (or slot info)
        navigate(`/dashboard/${result.token}`);
      } else {
        setError(result.msg || "Something went wrong.");
      }
    } catch (err) {
      console.error("Booking error:", err);
      setError("Server error. Please try again.");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-black">
      <div className="w-full max-w-md rounded-lg border border-gray-700 bg-gray-900 p-8 shadow-md">
        <div className="text-center mb-6">
          <Car className="mx-auto h-10 w-10 text-blue-500" />
          <h2 className="mt-4 text-2xl font-bold text-white">ParkSense Entry</h2>
          <p className="mt-1 text-gray-400">Confirm your phone number to get a slot</p>
        </div>

        <div className="mb-4 text-center text-white">
          <strong>Car Number:</strong> {carNumber}
        </div>

        {error && (
          <div className="mb-4 text-center text-sm text-red-500">{error}</div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="phone" className="block text-sm font-medium text-gray-300">
              Phone Number
            </label>
            <input
              id="phone"
              type="tel"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              required
              placeholder="Enter your phone number"
              className="mt-1 w-full rounded-md bg-gray-800 border border-gray-700 p-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <button
            type="submit"
            className="w-full rounded-md bg-blue-600 hover:bg-blue-700 p-2 font-semibold text-white transition"
          >
            Confirm & Get Slot
          </button>
        </form>
      </div>
    </div>
  );
}

export default EntryForm;
