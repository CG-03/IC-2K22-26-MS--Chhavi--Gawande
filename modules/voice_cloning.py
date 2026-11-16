import os

import requests
import streamlit as st

API = "https://api.elevenlabs.io/v1"
MAX_SAMPLE_MB = 10

SETUP = """
1. Create a free account at **elevenlabs.io** and open **Profile → API Keys** to create a key.
2. Copy `.env.example` to `.env` and set `ELEVENLABS_API_KEY=your_key_here`.
3. Restart the app (`Ctrl+C`, then `streamlit run app.py`).

**Note:** creating an *Instant Voice Clone* usually requires a paid plan (e.g. Starter). On the free plan the
API returns a "payment/plan required" error, but you can still generate speech with the built-in voices
(untick *Only my cloned voices* in the second tab). Every generation consumes character quota.
"""


class ElevenLabsError(Exception):
    pass


def _key() -> str:
    return os.getenv("ELEVENLABS_API_KEY", "").strip()


def _explain(r: requests.Response) -> str:
    try:
        detail = r.json().get("detail", "")
        msg = detail.get("message") or detail.get("status") if isinstance(detail, dict) else str(detail)
    except (ValueError, AttributeError):
        msg = r.text[:200]
    low = (msg or "").lower()
    if r.status_code == 401:
        return "Invalid or missing API key. Check ELEVENLABS_API_KEY in your .env file."
    if "quota" in low or "credits" in low:
        return f"Quota exceeded — not enough ElevenLabs credits left. ({msg})"
    if r.status_code in (402, 403) or "subscription" in low or "upgrade" in low:
        return f"Your ElevenLabs plan does not allow this action (voice cloning needs a paid plan). ({msg})"
    if r.status_code == 429:
        return "Rate limit reached (too many requests). Wait a moment and try again."
    return f"ElevenLabs error {r.status_code}: {msg}"


def _call(method: str, path: str, **kwargs) -> requests.Response:
    if not _key():
        raise ElevenLabsError("ELEVENLABS_API_KEY is not set.")
    try:
        r = requests.request(method, f"{API}{path}", headers={"xi-api-key": _key()}, timeout=120, **kwargs)
    except requests.exceptions.RequestException as e:
        raise ElevenLabsError(f"Network error while contacting ElevenLabs: {e}")
    if not r.ok:
        raise ElevenLabsError(_explain(r))
    return r


def list_voices() -> list:
    voices = _call("GET", "/voices").json().get("voices", [])
    return sorted(voices, key=lambda v: (v.get("category") != "cloned", v.get("name", "")))


def clone_voice(name: str, description: str, filename: str, data: bytes, mime: str) -> str:
    r = _call("POST", "/voices/add", data={"name": name, "description": description},
              files=[("files", (filename, data, mime))])
    return r.json()["voice_id"]


def synthesize(voice_id: str, text: str, model_id: str) -> bytes:
    r = _call("POST", f"/text-to-speech/{voice_id}", params={"output_format": "mp3_44100_128"},
              json={"text": text, "model_id": model_id})
    return r.content


def _load_voices(force: bool = False) -> list:
    if force or "voices" not in st.session_state:
        try:
            st.session_state["voices"] = list_voices()
        except ElevenLabsError as e:
            st.error(str(e))
            return []
    return st.session_state["voices"]


def _clone_tab():
    st.markdown("**Consent & authorization** — required before cloning.")
    c1 = st.checkbox("I own this voice, or the speaker has given me explicit permission to clone it.")
    c2 = st.checkbox("I will not use the cloned voice for impersonation, fraud, harassment or deception.")
    name = st.text_input("Name for the new voice", max_chars=50)
    sample = st.file_uploader("Voice sample (clear speech, 1–3 minutes works best)",
                              type=["mp3", "wav", "m4a", "flac", "ogg"], key="clone_sample")
    if sample:
        st.audio(sample.getvalue())
    if sample and sample.size > MAX_SAMPLE_MB * 1024 * 1024:
        st.error(f"Sample is larger than {MAX_SAMPLE_MB} MB. Please upload a shorter clip.")
        return
    ready = bool(c1 and c2 and name.strip() and sample)
    if st.button("Create voice clone", type="primary", disabled=not ready):
        with st.spinner("Uploading sample and creating the voice..."):
            try:
                vid = clone_voice(name.strip(), "Created from Streamlit multimedia project with consent.",
                                  sample.name, sample.getvalue(), sample.type or "audio/mpeg")
            except ElevenLabsError as e:
                st.error(str(e))
            else:
                st.session_state.pop("voices", None)
                st.success(f"Voice “{name.strip()}” created (ID: {vid}). Open the next tab to generate speech.")


def _speech_tab():
    top = st.columns([3, 1])
    only_cloned = top[0].checkbox("Only my cloned voices", value=True)
    if top[1].button("🔄 Refresh voices"):
        _load_voices(force=True)
    voices = _load_voices()
    if only_cloned:
        voices = [v for v in voices if v.get("category") == "cloned"]
    if not voices:
        st.info("No voices to show. Create a clone in the first tab, or untick “Only my cloned voices”.")
        return
    labels = {v["voice_id"]: f"{v['name']} · {v.get('category', 'voice')}" for v in voices}
    voice_id = st.selectbox("Voice", list(labels), format_func=labels.get)
    model = st.selectbox("Model", ["eleven_multilingual_v2", "eleven_flash_v2_5"])
    text = st.text_area("Text to speak", max_chars=2500, height=150,
                        placeholder="Type what you want the voice to say...")
    if st.button("Generate speech", type="primary", disabled=not text.strip()):
        with st.spinner("Generating audio..."):
            try:
                st.session_state["tts_audio"] = synthesize(voice_id, text.strip(), model)
                st.success("Speech generated.")
            except ElevenLabsError as e:
                st.error(str(e))
    audio = st.session_state.get("tts_audio")
    if audio:
        st.audio(audio, format="audio/mp3")
        st.download_button("⬇️ Download MP3", audio, "generated_speech.mp3", "audio/mpeg")


def render():
    st.header("🎙️ AI Voice Cloning")
    with st.expander("ElevenLabs API setup", expanded=not _key()):
        st.markdown(SETUP)
    if not _key():
        st.warning("No API key found. This module is optional — the other four work without it.")
        return
    tab1, tab2 = st.tabs(["1 · Clone a voice", "2 · Generate speech"])
    with tab1:
        _clone_tab()
    with tab2:
        _speech_tab()
