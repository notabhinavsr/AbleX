"""
stt_handler.py — Speech-to-Text using Sarvam AI
Records from microphone, detects silence, sends to Sarvam REST API.
Supports state callbacks for GUI / notification integration.
"""

import io
import wave
import time
import threading
import numpy as np
import sounddevice as sd
import requests
import pyautogui

from config import (
    SARVAM_API_KEY,
    SARVAM_MODEL,
    SARVAM_MODE,
    SILENCE_TIMEOUT,
    SILENCE_THRESHOLD,
    SAMPLE_RATE,
)


_listening = False
_lock = threading.Lock()
_state_callbacks = []       # list of fn(state_str) to call on state changes


def add_state_callback(fn):
    """Register a callback: fn("listening") / fn("typing") / fn("done") / fn("error")."""
    _state_callbacks.append(fn)


def _notify_state(state):
    """Notify all registered callbacks."""
    for fn in _state_callbacks:
        try:
            fn(state)
        except Exception:
            pass


def is_listening():
    return _listening


def _rms(audio_chunk):
    return np.sqrt(np.mean(audio_chunk.astype(np.float64) ** 2))


def _record_until_silence():
    chunk_duration = 0.5
    chunk_samples  = int(SAMPLE_RATE * chunk_duration)
    silence_start  = None
    frames = []

    print("[STT] 🎙️  Listening... (speak now)")
    _notify_state("listening")

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16") as stream:
        while True:
            data, _ = stream.read(chunk_samples)
            frames.append(data.copy())
            level = _rms(data)

            if level < SILENCE_THRESHOLD:
                if silence_start is None:
                    silence_start = time.time()
                elif time.time() - silence_start >= SILENCE_TIMEOUT:
                    print("[STT] ⏹️  Silence detected — stopping")
                    break
            else:
                silence_start = None

    audio = np.concatenate(frames, axis=0)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio.tobytes())
    buf.seek(0)
    return buf


def _transcribe(wav_buf):
    url = "https://api.sarvam.ai/speech-to-text"
    headers = {"api-subscription-key": SARVAM_API_KEY}
    files = {"file": ("recording.wav", wav_buf, "audio/wav")}
    data = {
        "model": SARVAM_MODEL,
        "language_code": "unknown",
        "mode": SARVAM_MODE,
    }

    print("[STT] ☁️  Transcribing...")
    _notify_state("transcribing")

    try:
        resp = requests.post(url, headers=headers, files=files, data=data, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        transcript = result.get("transcript", "").strip()
        print(f"[STT] 📝 Transcript: {transcript}")
        return transcript
    except requests.exceptions.RequestException as e:
        print(f"[STT] ❌ API error: {e}")
        _notify_state("error")
        return ""


def _type_text(text):
    if not text:
        print("[STT] ⚠️  No text to type")
        return
    print(f"[STT] ⌨️  Typing: {text}")
    _notify_state("typing")
    pyautogui.write(text, interval=0.02)


def start_stt():
    global _listening
    with _lock:
        if _listening:
            print("[STT] Already listening, ignoring...")
            return
        _listening = True

    try:
        wav_buf = _record_until_silence()
        transcript = _transcribe(wav_buf)
        _type_text(transcript)
    except Exception as e:
        print(f"[STT] ❌ Error: {e}")
        _notify_state("error")
    finally:
        _listening = False
        _notify_state("done")
        print("[STT] ✅ Done\n")


def trigger_stt():
    t = threading.Thread(target=start_stt, daemon=True)
    t.start()
