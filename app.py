import streamlit as st
from audiorecorder import audiorecorder
import openai
import io

st.set_page_config(page_title="Realtime Voice Chat")

st.title("Realtime Voice Chat")

openai_api_key = st.text_input("OpenAI API Key", type="password")
if openai_api_key:
    openai.api_key = openai_api_key

if 'messages' not in st.session_state:
    st.session_state.messages = []

for role, content in st.session_state.messages:
    with st.chat_message(role):
        st.markdown(content)

audio = audiorecorder("Start recording", "Stop recording")

if len(audio) > 0 and openai_api_key:
    buf = io.BytesIO()
    audio.export(buf, format="wav")
    buf.seek(0)
    with st.spinner("Transcribing..."):
        transcript = openai.audio.transcribe("whisper-1", buf)
    user_text = transcript["text"].strip()
    st.session_state.messages.append(("user", user_text))
    with st.chat_message("user"):
        st.markdown(user_text)

    with st.spinner("Generating reply..."):
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": role, "content": content} for role, content in st.session_state.messages],
            stream=True,
        )
        assistant_text = ""
        with st.chat_message("assistant"):
            assistant_area = st.empty()
            for chunk in response:
                delta = chunk.choices[0].delta.content or ""
                assistant_text += delta
                assistant_area.markdown(assistant_text)
    st.session_state.messages.append(("assistant", assistant_text))
