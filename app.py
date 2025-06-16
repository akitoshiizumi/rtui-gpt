import os
import ssl
import json
import asyncio
import threading
import nest_asyncio
from dotenv import load_dotenv
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import websockets
import base64
import av

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Load OpenAI API key from .env
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4o-realtime-preview-2024-10-01"
WS_URL = f"wss://api.openai.com/v1/realtime?model={MODEL}"

st.title("🎤 リアルタイム音声チャット (Streamlit + OpenAI Realtime API)")
if not API_KEY:
    st.error("`OPENAI_API_KEY` を `.env` に設定してください。")
    st.stop()

# Audio processor
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.buffer = b""
        self.lock = threading.Lock()

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        pcm = frame.to_ndarray().tobytes()
        with self.lock:
            self.buffer += pcm
        return frame

# Use public STUN server for ICE negotiation
webrtc_ctx = webrtc_streamer(
    key="audio",
    mode=WebRtcMode.SENDONLY,
    audio_processor_factory=AudioProcessor,
    rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}],
        "iceTransportPolicy": "all"
    },
)

async def run_realtime(audio_proc, text_placeholder):
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    headers = {"Authorization": f"Bearer {API_KEY}", "OpenAI-Beta": "realtime=v1"}
    async with websockets.connect(WS_URL, extra_headers=headers, ssl=ssl_ctx) as ws:
        session_cfg = {
            "type": "session.update",
            "session": {
                "modalities": ["audio", "text"],
                "instructions": "You are a helpful assistant.",
                "voice": "alloy",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {"model": "whisper-1"},
                "turn_detection": {"type": "server_vad", "threshold": 0.5, "prefix_padding_ms": 300, "silence_duration_ms": 600},
                "temperature": 0.6
            }
        }
        await ws.send(json.dumps(session_cfg))
        await ws.send(json.dumps({"type": "response.create"}))
        text_placeholder.text("🟢 Connected. Speak now...")

        async def recv_loop():
            async for msg in ws:
                evt = json.loads(msg)
                if evt.get("type") == "response.text.delta":
                    prev = text_placeholder._value or ""
                    text_placeholder.text(prev + evt["delta"])

        recv_task = asyncio.create_task(recv_loop())
        try:
            while True:
                await asyncio.sleep(0.1)
                with audio_proc.lock:
                    if audio_proc.buffer:
                        chunk = audio_proc.buffer
                        audio_proc.buffer = b""
                        await ws.send(json.dumps({"type": "input.audio.buffer", "audio": base64.b64encode(chunk).decode()}))
        except asyncio.CancelledError:
            pass
        finally:
            recv_task.cancel()

if webrtc_ctx.state.playing:
    placeholder = st.empty()
    if st.button("Start Conversation"):
        asyncio.run(run_realtime(webrtc_ctx.audio_processor, placeholder))
