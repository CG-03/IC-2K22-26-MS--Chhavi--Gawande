import io

import cv2
import numpy as np
import streamlit as st
from PIL import Image, ImageEnhance, ImageOps

MAX_OUTPUT_SIDE = 6000


@st.cache_data(show_spinner=False, max_entries=8)
def enhance(data: bytes, brightness: float, contrast: float, sharpness: float,
            saturation: float, denoise: int, scale: int):
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(data)))
    had_alpha = img.mode in ("RGBA", "LA") or "transparency" in img.info
    img = img.convert("RGB")
    limit = min(3000, MAX_OUTPUT_SIDE // scale)
    downscaled = max(img.size) > limit
    if downscaled:
        img.thumbnail((limit, limit), Image.LANCZOS)

    arr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    if denoise > 0:
        arr = cv2.fastNlMeansDenoisingColored(arr, None, denoise, denoise, 7, 21)
    if scale > 1:
        arr = cv2.resize(arr, None, fx=scale, fy=scale, interpolation=cv2.INTER_LANCZOS4)
    out = Image.fromarray(cv2.cvtColor(arr, cv2.COLOR_BGR2RGB))

    out = ImageEnhance.Brightness(out).enhance(brightness)
    out = ImageEnhance.Contrast(out).enhance(contrast)
    out = ImageEnhance.Color(out).enhance(saturation)
    out = ImageEnhance.Sharpness(out).enhance(sharpness)
    return out, downscaled, had_alpha, limit


def render():
    st.header("✨ Image Enhancement")
    up = st.file_uploader("Drag and drop an image", type=["jpg", "jpeg", "png", "webp"], key="img_enh")
    if not up:
        st.info("Upload a JPG, PNG or WEBP image to begin.")
        return
    data = up.getvalue()

    with st.sidebar:
        st.markdown("### Enhancement controls")
        brightness = st.slider("Brightness", 0.5, 2.0, 1.0, 0.05)
        contrast = st.slider("Contrast", 0.5, 2.0, 1.0, 0.05)
        sharpness = st.slider("Sharpness", 0.0, 3.0, 1.0, 0.1)
        saturation = st.slider("Saturation", 0.0, 2.0, 1.0, 0.05)
        denoise = st.slider("Noise reduction", 0, 15, 0, 1, help="Non-local means. Higher = smoother but slower.")
        scale = st.select_slider("Upscale", options=[1, 2, 3], value=1, format_func=lambda x: f"{x}×")

    try:
        with st.spinner("Enhancing..."):
            out, downscaled, had_alpha, limit = enhance(data, brightness, contrast, sharpness,
                                                        saturation, denoise, scale)
    except Exception as e:
        st.error(f"Could not process this image: {e}")
        return

    if downscaled:
        st.warning(f"Large image resized to fit within {limit}px before processing to keep things fast.")
    if had_alpha:
        st.caption("Transparency was removed (image converted to RGB).")

    before, after = st.columns(2)
    before.subheader("Before")
    before.image(data, caption=f"{Image.open(io.BytesIO(data)).size[0]} × {Image.open(io.BytesIO(data)).size[1]} px")
    after.subheader("After")
    after.image(out, caption=f"{out.size[0]} × {out.size[1]} px")

    fmt = st.radio("Download format", ["PNG", "JPEG"], horizontal=True)
    buf = io.BytesIO()
    out.save(buf, format=fmt, **({"quality": 95} if fmt == "JPEG" else {}))
    stem = up.name.rsplit(".", 1)[0]
    st.download_button(f"⬇️ Download enhanced image ({fmt})", buf.getvalue(),
                       f"{stem}_enhanced.{fmt.lower()}", f"image/{fmt.lower()}")
