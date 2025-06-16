import streamlit as st
import openai
import io
import os
from dotenv import load_dotenv
import websocket
import json
import base64
import numpy as np
from pydub import AudioSegment
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode
import struct

st.set_page_config(page_title="Realtime Voice Chat (OpenAI Realtime API)")
st.title("Realtime Voice Chat (OpenAI Realtime API)")

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    openai_api_key = st.text_input("OpenAI API Key", type="password")

if 'messages' not in st.session_state:
    st.session_state.messages = []

for role, content in st.session_state.messages:
    with st.chat_message(role):
        st.markdown(content)

class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.audio_buffer = b""
    def recv(self, frame):
        audio_bytes = frame.to_ndarray().tobytes()
        self.audio_buffer += audio_bytes
        return frame

audio_ctx = webrtc_streamer(
    key="audio",
    mode=WebRtcMode.SENDONLY,
    audio_receiver_size=1024,
    media_stream_constraints={
        "audio": True,
        "video": False,
    },
    rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    },
    audio_processor_factory=AudioProcessor,
)

def float_to_16bit_pcm(float32_array):
    clipped = np.clip(float32_array, -1.0, 1.0)
    pcm16 = b''.join(struct.pack('<h', int(x * 32767)) for x in clipped)
    return pcm16

if audio_ctx and audio_ctx.audio_processor:
    if st.button("送信（録音停止後クリック）") and openai_api_key:
        audio_bytes = audio_ctx.audio_processor.audio_buffer
        if not audio_bytes:
            st.warning("音声データがありません")
        else:
            segment = AudioSegment(
                data=audio_bytes,
                sample_width=2,
                frame_rate=16000,
                channels=1
            )
            samples = np.array(segment.get_array_of_samples()).astype(np.float32) / 32768.0
            chunk_size = 16000  # 1秒分（16kHz, 1ch）
            ws = websocket.create_connection(
                "wss://api.openai.com/v1/realtime/conversations",
                header={"Authorization": f"Bearer {openai_api_key}"}
            )
            session_event = {
                "type": "session.update",
                "session": {
                    "model": "gpt-4o-realtime-preview",
                    "voice": "alloy",
                    "instructions": "あなたは親切なアシスタントです。"
                }
            }
            ws.send(json.dumps(session_event))
            # チャンクごとに送信
            for i in range(0, len(samples), chunk_size):
                chunk = samples[i:i+chunk_size]
                pcm16 = float_to_16bit_pcm(chunk)
                audio_b64 = base64.b64encode(pcm16).decode("ascii")
                event = {
                    "type": "input_audio_buffer.append",
                    "audio": audio_b64
                }
                ws.send(json.dumps(event))
            # 入力完了を通知
            ws.send(json.dumps({"type": "input_audio_buffer.commit"}))
            # 応答生成リクエスト
            response_event = {
                "type": "response.create",
                "response": {
                    "modalities": ["text"]
                }
            }
            ws.send(json.dumps(response_event))
            assistant_text = ""
            with st.spinner("Waiting for response..."):
                while True:
                    result = ws.recv()
                    event = json.loads(result)
                    if event.get("type") == "response.text.delta":
                        delta = event["delta"]
                        assistant_text += delta
                        st.session_state.messages.append(("assistant", assistant_text))
                        st.experimental_rerun()
                    if event.get("type") == "response.done":
                        if event["response"]["output"]:
                            assistant_text = event["response"]["output"][0]
                        break
            ws.close()
            st.session_state.messages.append(("assistant", assistant_text))
            with st.chat_message("assistant"):
                st.markdown(assistant_text)
