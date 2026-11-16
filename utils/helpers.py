import json
import os
import shutil
import subprocess
import tempfile
from contextlib import contextmanager

import streamlit as st


@contextmanager
def temp_file(data: bytes, suffix: str = ""):
    """Write bytes to a temp file, yield its path, always delete it afterwards."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        yield path
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def human_size(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.2f} {unit}"
        n /= 1024
    return f"{n:.2f} TB"


def human_duration(seconds: float) -> str:
    seconds = float(seconds or 0)
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    frac = f"{seconds - int(seconds):.2f}"[1:]
    return f"{h:d}:{m:02d}:{s:02d}{frac}" if h else f"{m:d}:{s:02d}{frac}"


def parse_fraction(value) -> float:
    try:
        text = str(value)
        if "/" in text:
            a, b = text.split("/")
            return float(a) / float(b) if float(b) else 0.0
        return float(text)
    except (TypeError, ValueError):
        return 0.0


def ffprobe(path: str) -> dict:
    if not shutil.which("ffprobe"):
        raise RuntimeError("FFprobe not found. Install FFmpeg and make sure it is on your PATH.")
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", path],
        capture_output=True, text=True, timeout=60,
    )
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or "FFprobe could not read this file.")
    return json.loads(r.stdout)


def show_table(data: dict):
    rows = {"Property": [str(k) for k in data], "Value": ["—" if v in (None, "") else str(v) for v in data.values()]}
    st.dataframe(rows, hide_index=True)


def json_download(label: str, data: dict, filename: str):
    st.download_button(label, json.dumps(data, indent=2, default=str), file_name=filename, mime="application/json")
