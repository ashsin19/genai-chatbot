// server.js

const express = require('express');
const cors = require('cors');
const axios = require('axios');
const cookieParser = require('cookie-parser');

const app = express();
const port = 5000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(cookieParser());

// External API endpoint (replace with the actual chatbot API URL)
const CHATBOT_API_URL = 'http://127.0.0.1:8000/api/messages';  // Replace with real API URL

// Define the route to handle chat messages from the frontend
app.post('/api/messages', async (req, res) => {
  const userMessage = req.body.message;
  const userID = req.body.username;
  try {
    // Forward the user message to the external chatbot API
    const apiResponse = await axios.post(CHATBOT_API_URL, {
      username: userID,
      message: userMessage
    },        
    {
      headers: {
        'Content-Type': 'application/json',
        Authorization: `${req.headers['authorization']}`, // Add token here
      },
    }
  );

    // Extract the response from the external API
    const botResponse = apiResponse.data.response;

    // Send the chatbot's response back to the frontend
    res.json({ response: botResponse });

  } catch (error) {
    console.error('Error communicating with the chatbot API:', error);

    // Send an error response if something went wrong
    res.status(500).json({
      error: 'Failed to communicate with the chatbot API. Please try again later.'
    });
  }
});

// Root route for testing
app.get('/', (req, res) => {
  res.send({ message: 'Chatbot backend is running!' });
});

// Start the server
app.listen(port, () => {
  console.log(`Server listening at http://localhost:${port}`);
});
