import os

import cv2
import streamlit as st

from utils.helpers import ffprobe, human_duration, human_size, json_download, parse_fraction, show_table, temp_file


def _thumbnail(path: str, duration: float):
    cap = cv2.VideoCapture(path)
    try:
        if duration:
            cap.set(cv2.CAP_PROP_POS_MSEC, duration * 0.1 * 1000)
        ok, frame = cap.read()
        if not ok:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = cap.read()
        if not ok:
            return None
        h, w = frame.shape[:2]
        if w > 640:
            frame = cv2.resize(frame, (640, int(h * 640 / w)))
        ok, buf = cv2.imencode(".jpg", frame)
        return buf.tobytes() if ok else None
    finally:
        cap.release()


@st.cache_data(show_spinner=False)
def analyze(data: bytes, filename: str):
    with temp_file(data, os.path.splitext(filename)[1]) as path:
        info = ffprobe(path)
        fmt = info.get("format", {})
        streams = info.get("streams", [])
        v = next((s for s in streams if s.get("codec_type") == "video"), None)
        a = next((s for s in streams if s.get("codec_type") == "audio"), None)
        if not v:
            raise RuntimeError("No video stream found in this file.")
        duration = float(fmt.get("duration") or v.get("duration") or 0)
        fps = parse_fraction(v.get("avg_frame_rate")) or parse_fraction(v.get("r_frame_rate"))
        nb = v.get("nb_frames")
        frames, estimated = (int(nb), False) if nb and str(nb).isdigit() else (round(duration * fps), True)
        bitrate = int(fmt.get("bit_rate") or v.get("bit_rate") or 0)
        thumb = _thumbnail(path, duration)
    meta = {
        "filename": filename,
        "container": fmt.get("format_long_name"),
        "duration_seconds": round(duration, 3),
        "width_px": v.get("width"),
        "height_px": v.get("height"),
        "fps": round(fps, 3),
        "video_codec": v.get("codec_long_name") or v.get("codec_name"),
        "bitrate_kbps": round(bitrate / 1000, 1),
        "frame_count": frames,
        "frame_count_estimated": estimated,
        "file_size_bytes": len(data),
        "audio_codec": a.get("codec_name") if a else None,
        "audio_sample_rate_hz": a.get("sample_rate") if a else None,
        "audio_channels": a.get("channels") if a else None,
        "ffprobe_raw": info,
    }
    return meta, thumb


def render():
    st.header("🎬 Video Metadata Analyzer")
    up = st.file_uploader("Drag and drop a video", type=["mp4", "avi", "mov", "mkv"], key="vid_meta")
    if not up:
        st.info("Upload an MP4, AVI, MOV or MKV video to begin.")
        return
    data = up.getvalue()
    try:
        with st.spinner("Running FFprobe..."):
            meta, thumb = analyze(data, up.name)
    except Exception as e:
        st.error(f"Could not analyze this video: {e}")
        return
    st.success("Analysis complete.")

    c = st.columns(4)
    c[0].metric("Duration", human_duration(meta["duration_seconds"]))
    c[1].metric("Resolution", f"{meta['width_px']}×{meta['height_px']}")
    c[2].metric("FPS", meta["fps"])
    c[3].metric("Codec", meta["video_codec"].split(" ")[0] if meta["video_codec"] else "—")
    c = st.columns(3)
    c[0].metric("Bitrate", f"{meta['bitrate_kbps']} kbps")
    c[1].metric("Frames", f"{meta['frame_count']}" + (" (est.)" if meta["frame_count_estimated"] else ""))
    c[2].metric("File size", human_size(meta["file_size_bytes"]))

    left, right = st.columns(2)
    with left:
        st.subheader("Preview")
        st.video(data)
    with right:
        st.subheader("Thumbnail")
        if thumb:
            st.image(thumb, caption="Frame at ~10% of the video")
            st.download_button("⬇️ Download thumbnail", thumb, f"{up.name.rsplit('.', 1)[0]}_thumb.jpg", "image/jpeg")
        else:
            st.warning("Could not generate a thumbnail for this file.")

    st.subheader("Details")
    show_table({k: v for k, v in meta.items() if k not in ("ffprobe_raw", "frame_count_estimated")})
    json_download("⬇️ Export metadata as JSON", meta, f"{up.name.rsplit('.', 1)[0]}_metadata.json")
