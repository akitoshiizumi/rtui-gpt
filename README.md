# rtui-gpt

This repository contains a simple Streamlit application that demonstrates a realtime voice chat interface using OpenAI APIs.

## Requirements

- Python 3.12
- ffmpeg (for audio processing)
- See `requirements.txt` for Python dependencies.

### Installing ffmpeg

Ubuntu/Debian:

```bash
sudo apt-get update && sudo apt-get install -y ffmpeg
```

macOS (with Homebrew):

```bash
brew install ffmpeg
```

## Usage

Install the requirements and run the Streamlit app:

```bash
pip install -r requirements.txt
streamlit run app.py
```

When the app loads, enter your OpenAI API key, record your message, and the assistant will reply using the Chat Completion API.

