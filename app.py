import shutil

import streamlit as st
from dotenv import load_dotenv

load_dotenv()
st.set_page_config(page_title="AI Multimedia Toolkit", page_icon="🎛️", layout="wide")

from modules import audio_analyzer, image_analyzer, image_enhancer, video_analyzer, voice_cloning  # noqa: E402

FEATURES = [
    ("🖼️", "Image Metadata", "EXIF, camera details, dimensions, histogram and JSON export.", image_analyzer.render),
    ("🎬", "Video Metadata", "FFprobe analysis, thumbnail, preview and JSON export.", video_analyzer.render),
    ("🎧", "Audio Metadata", "Tags, bitrate, sample rate, waveform and JSON export.", audio_analyzer.render),
    ("🎙️", "Voice Cloning", "Clone an authorized voice with ElevenLabs and generate speech.", voice_cloning.render),
    ("✨", "Image Enhancement", "Brightness, contrast, sharpness, saturation, denoise, upscale.", image_enhancer.render),
]
PAGES = {title: render for _, title, _, render in FEATURES}
NAV = ["Home"] + list(PAGES)

st.session_state.setdefault("page", "Home")


def go(page: str):
    st.session_state["page"] = page


def home():
    st.title("🎛️ AI-Powered Multimedia Toolkit")
    st.caption("Analyze, clone and enhance media — all in one lightweight dashboard.")
    cols = st.columns(3)
    for i, (icon, title, desc, _) in enumerate(FEATURES):
        with cols[i % 3]:
            with st.container(border=True):
                st.subheader(f"{icon} {title}")
                st.write(desc)
                st.button("Open", key=f"open_{title}", on_click=go, args=(title,))


with st.sidebar:
    st.title("🎛️ Multimedia Toolkit")
    st.radio("Navigation", NAV, key="page")
    st.divider()
    if shutil.which("ffprobe") and shutil.which("ffmpeg"):
        st.success("FFmpeg detected")
    else:
        st.error("FFmpeg not found — video/audio modules need it. See README.")

page = st.session_state["page"]
if page == "Home":
    home()
else:
    PAGES[page]()
