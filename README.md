# AI-Powered Multimedia Analysis & Enhancement Tool

Streamlit app with five modules: image / video / audio metadata analyzers, ElevenLabs voice cloning, image enhancement.
CPU only, no large models. Only Module 4 needs an API key.

## 1. Install FFmpeg (provides `ffmpeg` and `ffprobe`)
- Windows: `winget install Gyan.FFmpeg` (then reopen the terminal)
- macOS: `brew install ffmpeg`
- Ubuntu/Debian: `sudo apt install ffmpeg`

Check with `ffprobe -version`.

## 2. Install and run
```bash
cd multimedia_ai
python -m venv venv
# Windows: venv\Scripts\activate      macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```
Opens at http://localhost:8501.

## 3. ElevenLabs setup (optional, Module 4 only)
1. Create an API key at elevenlabs.io (Profile → API Keys).
2. Put it in `.env`: `ELEVENLABS_API_KEY=your_key_here`
3. Restart the app.

Instant voice cloning generally needs a paid ElevenLabs plan; the app shows a clear message if your plan or quota doesn't allow it.
Only clone voices you own or have written permission to use.

## Structure
```
app.py                    dashboard + sidebar navigation
modules/image_analyzer.py Pillow EXIF, histogram, JSON export
modules/video_analyzer.py FFprobe metadata, OpenCV thumbnail
modules/audio_analyzer.py FFprobe + Mutagen tags, waveform
modules/voice_cloning.py  ElevenLabs REST API
modules/image_enhancer.py Pillow + OpenCV enhancement
utils/helpers.py          temp files, ffprobe, formatting
```
