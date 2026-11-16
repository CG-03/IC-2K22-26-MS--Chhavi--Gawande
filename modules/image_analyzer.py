import io

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from PIL import ExifTags, Image
from PIL.TiffImagePlugin import IFDRational

from utils.helpers import human_size, json_download, show_table


def _clean(v):
    if isinstance(v, IFDRational):
        f = float(v)
        return None if f != f else f
    if isinstance(v, bytes):
        return v.decode("utf-8", "ignore").strip("\x00")[:200]
    if isinstance(v, (tuple, list)):
        return [_clean(x) for x in v]
    if isinstance(v, dict):
        return {str(k): _clean(x) for k, x in v.items()}
    if isinstance(v, (int, float, str)):
        return v
    return str(v)


def _read_exif(img) -> dict:
    exif = img.getexif()
    out = {ExifTags.TAGS.get(t, str(t)): _clean(v) for t, v in exif.items()}
    for ifd_id, tagmap in ((0x8769, ExifTags.TAGS), (0x8825, ExifTags.GPSTAGS)):
        try:
            ifd = exif.get_ifd(ifd_id)
        except Exception:
            ifd = {}
        for t, v in ifd.items():
            out[tagmap.get(t, str(t))] = _clean(v)
    for junk in ("ExifOffset", "GPSInfo", "MakerNote"):
        out.pop(junk, None)
    return out


def _gps(exif: dict):
    try:
        conv = lambda v: v[0] + v[1] / 60 + v[2] / 3600
        lat, lon = conv(exif["GPSLatitude"]), conv(exif["GPSLongitude"])
        if exif.get("GPSLatitudeRef") == "S":
            lat = -lat
        if exif.get("GPSLongitudeRef") == "W":
            lon = -lon
        return round(lat, 6), round(lon, 6)
    except Exception:
        return None


@st.cache_data(show_spinner=False)
def analyze(data: bytes, filename: str):
    img = Image.open(io.BytesIO(data))
    exif = _read_exif(img)
    w, h = img.size
    dpi = img.info.get("dpi")
    camera = {k: exif[k] for k in ("Make", "Model", "LensModel", "FNumber", "ExposureTime",
                                   "ISOSpeedRatings", "FocalLength", "Software") if k in exif}
    meta = {
        "filename": filename,
        "format": img.format,
        "width_px": w,
        "height_px": h,
        "megapixels": round(w * h / 1e6, 2),
        "resolution_dpi": [round(float(x)) for x in dpi] if dpi else None,
        "file_size_bytes": len(data),
        "file_size": human_size(len(data)),
        "color_mode": img.mode,
        "camera": camera,
        "date_captured": exif.get("DateTimeOriginal") or exif.get("DateTime"),
        "gps_decimal": _gps(exif),
        "exif": exif,
    }
    rgb = np.array(img.convert("RGB"))
    hist = [np.bincount(rgb[..., i].ravel(), minlength=256).tolist() for i in range(3)]
    return meta, hist


def render():
    st.header("🖼️ Image Metadata Analyzer")
    up = st.file_uploader("Drag and drop an image", type=["jpg", "jpeg", "png", "webp"], key="img_meta")
    if not up:
        st.info("Upload a JPG, JPEG, PNG or WEBP image to begin.")
        return
    data = up.getvalue()
    try:
        with st.spinner("Analyzing image..."):
            meta, hist = analyze(data, up.name)
    except Exception as e:
        st.error(f"Could not read this image: {e}")
        return
    st.success("Analysis complete.")

    left, right = st.columns(2)
    left.image(data, caption=up.name)
    with right:
        st.subheader("General")
        dpi = meta["resolution_dpi"]
        show_table({
            "Filename": meta["filename"],
            "Format": meta["format"],
            "Dimensions": f"{meta['width_px']} × {meta['height_px']} px ({meta['megapixels']} MP)",
            "Resolution": f"{dpi[0]} × {dpi[1]} DPI" if dpi else None,
            "File size": meta["file_size"],
            "Color mode": meta["color_mode"],
            "Date captured": meta["date_captured"],
        })

    st.subheader("Camera details")
    if meta["camera"]:
        show_table(meta["camera"])
    else:
        st.caption("No camera information found (screenshots and messaging apps usually strip EXIF).")

    if meta["gps_decimal"]:
        st.subheader("GPS location")
        lat, lon = meta["gps_decimal"]
        st.write(f"{lat}, {lon}")
        st.map(pd.DataFrame({"lat": [lat], "lon": [lon]}))

    st.subheader("Histogram")
    fig = go.Figure()
    for counts, name, color in zip(hist, ("Red", "Green", "Blue"), ("#ff4b4b", "#2ecc71", "#4b8bff")):
        fig.add_trace(go.Scatter(y=counts, mode="lines", name=name, line=dict(color=color, width=1.5)))
    fig.update_layout(template="plotly_dark", height=320, xaxis_title="Pixel value (0–255)",
                      yaxis_title="Pixel count", margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig)

    with st.expander("All EXIF tags"):
        if meta["exif"]:
            show_table(meta["exif"])
        else:
            st.caption("This image contains no EXIF data.")
    json_download("⬇️ Export metadata as JSON", meta, f"{up.name.rsplit('.', 1)[0]}_metadata.json")
