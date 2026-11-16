import os
import shutil
import subprocess

import mutagen
import numpy as np
import plotly.graph_objects as go
import streamlit as st

from utils.helpers import ffprobe, human_duration, human_size, json_download, show_table, temp_file

TAG_KEYS = ("title", "artist", "album", "date", "genre", "tracknumber")


def _tags(path: str) -> dict:
    try:
        mf = mutagen.File(path, easy=True)
        out = {}
        for k in TAG_KEYS:
            v = mf.get(k) if mf is not None else None
            if v:
                out[k] = ", ".join(map(str, v)) if isinstance(v, (list, tuple)) else str(v)
        return out
    except Exception:
        return {}


def _waveform(path: str, sr: int = 8000):
    """Decode to mono 8 kHz PCM with ffmpeg and reduce to a min/max envelope."""
    if not shutil.which("ffmpeg"):
        return None
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"],
                       capture_output=True, timeout=180)
    if r.returncode != 0 or not r.stdout:
        return None
    x = np.frombuffer(r.stdout, dtype=np.int16).astype(np.float32) / 32768
    n = min(1500, len(x))
    if n == 0:
        return None
    k = len(x) // n
    x = x[: k * n].reshape(n, k)
    t = np.linspace(0, len(r.stdout) / 2 / sr, n)
    return {"t": t.tolist(), "min": x.min(axis=1).tolist(), "max": x.max(axis=1).tolist()}


@st.cache_data(show_spinner=False)
def analyze(data: bytes, filename: str):
    with temp_file(data, os.path.splitext(filename)[1]) as path:
        info = ffprobe(path)
        tags = _tags(path)
        wave = _waveform(path)
    fmt = info.get("format", {})
    a = next((s for s in info.get("streams", []) if s.get("codec_type") == "audio"), None)
    if not a:
        raise RuntimeError("No audio stream found in this file.")
    bitrate = int(a.get("bit_rate") or fmt.get("bit_rate") or 0)
    meta = {
        "filename": filename,
        "format": fmt.get("format_long_name"),
        "codec": a.get("codec_name"),
        "duration_seconds": round(float(fmt.get("duration") or a.get("duration") or 0), 3),
        "bitrate_kbps": round(bitrate / 1000, 1),
        "sample_rate_hz": int(a.get("sample_rate") or 0),
        "channels": a.get("channels"),
        "channel_layout": a.get("channel_layout"),
        "file_size_bytes": len(data),
        "title": tags.get("title"),
        "artist": tags.get("artist"),
        "album": tags.get("album"),
        "other_tags": {k: v for k, v in tags.items() if k not in ("title", "artist", "album")},
    }
    return meta, wave


def render():
    st.header("🎧 Audio Metadata Analyzer")
    up = st.file_uploader("Drag and drop an audio file", type=["mp3", "wav", "flac", "m4a"], key="aud_meta")
    if not up:
        st.info("Upload an MP3, WAV, FLAC or M4A file to begin.")
        return
    data = up.getvalue()
    try:
        with st.spinner("Analyzing audio..."):
            meta, wave = analyze(data, up.name)
    except Exception as e:
        st.error(f"Could not analyze this audio file: {e}")
        return
    st.success("Analysis complete.")

    st.audio(data)
    c = st.columns(4)
    c[0].metric("Duration", human_duration(meta["duration_seconds"]))
    c[1].metric("Sample rate", f"{meta['sample_rate_hz']} Hz")
    c[2].metric("Channels", meta["channels"])
    c[3].metric("Bitrate", f"{meta['bitrate_kbps']} kbps")

    st.subheader("Waveform")
    if wave:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=wave["t"], y=wave["max"], mode="lines", line=dict(width=0), showlegend=False))
        fig.add_trace(go.Scatter(x=wave["t"], y=wave["min"], mode="lines", fill="tonexty",
                                 line=dict(width=0), fillcolor="rgba(124,92,255,0.7)", showlegend=False))
        fig.update_layout(template="plotly_dark", height=260, xaxis_title="Time (s)", yaxis_title="Amplitude",
                          margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig)
    else:
        st.warning("Waveform unavailable (FFmpeg is required to decode the audio).")

    st.subheader("Details")
    show_table({
        "Filename": meta["filename"], "Format": meta["format"], "Codec": meta["codec"],
        "File size": human_size(meta["file_size_bytes"]), "Channel layout": meta["channel_layout"],
        "Title": meta["title"], "Artist": meta["artist"], "Album": meta["album"], **meta["other_tags"],
    })
    json_download("⬇️ Export metadata as JSON", meta, f"{up.name.rsplit('.', 1)[0]}_metadata.json")
