<div align="center">

# Multimedia Systems Lab

**Explore the data behind every image, sound and frame.**

**Chhavi Gawande** · Image · Audio · Video · OCR · AI voice

[**Open the browser demo ↗**](https://multimedia-laboratory-nu.vercel.app) · [Datasets](datasets/README.md) · [Frontend source](https://github.com/ARPANPATRA111/mm-lab/tree/frontend/astro-metadata-lab/frontend)

</div>

---

## What's inside

| Project | What it does | Folder |
| --- | --- | --- |
| **Media analyzer** | Point it at any image, audio or video file and it shows the metadata (size, codec, duration, EXIF, GPS ...) | `main.py` |
| **Image lab** | Image metadata + grayscale, resize, threshold, blur, edges, rotate | `Cluster02-Image-Processing/` |
| **Audio lab** | Audio metadata + stereo-to-mono, normalise, reverse | `Cluster03-Audio-Processing/` |
| **Video lab** | Video metadata + grayscale, resize, thumbnail, frames, trim, reverse | `Cluster04-Video-Processing/` |
| **Task Pipe** | Fixes blurry, dark, rotated or skewed photos, then reads the text in 10+ languages (Hindi, Arabic, Chinese, ...) | [`Cluster05-Task-Pipe/`](Cluster05-Task-Pipe/README.md) |
| **Voice transformer** | Web app: record your voice and hear it in another AI voice | [`voice-transformer/`](voice-transformer/README.md) |

## Setup (once)

You need Python 3.10+ and [FFmpeg](https://ffmpeg.org/download.html) (check with `ffprobe -version`).

```bash
python -m venv .venv
# Windows:      .\.venv\Scripts\Activate.ps1
# macOS/Linux:  source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Run it

Each run writes to a **new** folder under `outputs/`; existing results are never overwritten.

```bash
# Media analyzer: any image, audio or video file (add --json report.json to save)
python main.py datasets/images/camera_canon_40d.jpg
python main.py datasets/video/h264_aac_720p.mp4

# Image / audio / video labs
python Cluster02-Image-Processing/image_processing.py datasets/images/camera_canon_40d.jpg --output-dir outputs/images
python Cluster03-Audio-Processing/audio_processing.py datasets/audio/mono_44k_16bit.wav --output-dir outputs/audio
python Cluster04-Video-Processing/video_processing.py datasets/video/h264_aac_720p.mp4 --output-dir outputs/video --start 1 --duration 2

# Task Pipe: enhance images and read their text (opens a results page in the browser)
python Cluster05-Task-Pipe/task_pipe.py datasets/task-pipe/real/ --output-dir outputs/ocr --open
```

The voice transformer is a separate Next.js app (`cd voice-transformer`, `pnpm install`, `pnpm dev`). It needs an ElevenLabs API key; see [its README](voice-transformer/README.md). Try it live at [voice-transformer.vercel.app](https://voice-transformer.vercel.app).



## Notes

- **Images:** JPEG, PNG, GIF, BMP, TIFF, WebP. HEIC needs an extra Pillow plugin.
- **Audio processing** takes 16-bit PCM WAV. Compressed audio and video metadata need FFprobe.
- **Generated video** is silent MJPEG AVI.
- **Sample files** and their sources are in [`datasets/`](datasets/README.md).
