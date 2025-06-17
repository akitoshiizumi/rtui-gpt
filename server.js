import dotenv from 'dotenv';
import express from 'express';
import axios from 'axios';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;
const MODEL = process.env.MODEL || 'gpt-4o-realtime-preview-2025-06-03';

app.use(express.static('public'));

app.get('/token', async (req, res) => {
  try {
    const resp = await axios.post(
      'https://api.openai.com/v1/realtime/sessions',
      { model: MODEL },
      {
        headers: {
          Authorization: `Bearer ${process.env.OPENAI_API_KEY}`,
          'Content-Type': 'application/json'
        }
      }
    );
    const token = resp.data.client_secret.value;
    res.json({ token });
  } catch (err) {
    console.error(err.response?.data || err.message);
    res.status(500).json({ error: 'Failed to create token' });
  }
});

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
