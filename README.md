# Voice Agent Quickstart

This project demonstrates a realtime voice assistant using the [OpenAI Agents SDK](https://github.com/openai/openai-agents-js).
The server issues ephemeral client tokens which the browser uses to connect to the Realtime API.

## Requirements

- Node.js >= 18
- An OpenAI API key with access to the Realtime API

## Setup

1. Install dependencies:

```bash
npm install
```

2. Copy `.env.example` to `.env` and set your `OPENAI_API_KEY`:

```bash
cp .env.example .env
# edit .env
```

3. Start the server:

```bash
npm start
```

Visit [http://localhost:3000](http://localhost:3000) and click **Start Conversation**.
Grant microphone access and you can speak with the assistant. Both sides of the
conversation are displayed on the page.
