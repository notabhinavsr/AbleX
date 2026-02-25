"""
stt_handler.py — Speech-to-Text using Sarvam AI
Records from microphone, detects silence, sends to Sarvam REST API.
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


_listening = False          # True while STT is active
_lock = threading.Lock()


def is_listening():
    """Check if STT is currently active."""
    return _listening


def _rms(audio_chunk):
    """Calculate root-mean-square of an audio chunk."""
    return np.sqrt(np.mean(audio_chunk.astype(np.float64) ** 2))


def _record_until_silence():
    """
    Record from the default microphone until SILENCE_TIMEOUT seconds
    of continuous silence is detected.  Returns a WAV file as bytes.
    """
    chunk_duration = 0.5                       # seconds per chunk
    chunk_samples  = int(SAMPLE_RATE * chunk_duration)
    silence_start  = None
    frames = []

    print("[STT] 🎙️  Listening... (speak now)")

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16") as stream:
        while True:
            data, _ = stream.read(chunk_samples)
            frames.append(data.copy())
            level = _rms(data)

            if level < SILENCE_THRESHOLD:
                if silence_start is None:
                    silence_start = time.time()
                elif time.time() - silence_start >= SILENCE_TIMEOUT:
                    print("[STT] ⏹️  Silence detected — stopping recording")
                    break
            else:
                silence_start = None      # reset on speech

    # Build WAV in memory
    audio = np.concatenate(frames, axis=0)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)   # 16-bit
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio.tobytes())
    buf.seek(0)
    return buf


def _transcribe(wav_buf):
    """Send WAV audio to Sarvam STT REST API and return the transcript."""
    url = "https://api.sarvam.ai/speech-to-text"
    headers = {"api-subscription-key": SARVAM_API_KEY}
    files = {"file": ("recording.wav", wav_buf, "audio/wav")}
    data = {
        "model": SARVAM_MODEL,
        "language_code": "unknown",     # auto-detect
        "mode": SARVAM_MODE,
    }

    try:
        resp = requests.post(url, headers=headers, files=files, data=data, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        transcript = result.get("transcript", "").strip()
        print(f"[STT] 📝 Transcript: {transcript}")
        return transcript
    except requests.exceptions.RequestException as e:
        print(f"[STT] ❌ API error: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"[STT]    Response: {e.response.text[:200]}")
        return ""


def _type_text(text):
    """Type the transcribed text at the current cursor position."""
    if not text:
        print("[STT] ⚠️  No text to type")
        return
    print(f"[STT] ⌨️  Typing: {text}")
    pyautogui.write(text, interval=0.02)


def start_stt():
    """
    Main entry — called from a background thread.
    Records → transcribes → types the result.
    """
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
    finally:
        _listening = False
        print("[STT] ✅ Done\n")


def trigger_stt():
    """Launch STT in a background thread (non-blocking)."""
    t = threading.Thread(target=start_stt, daemon=True)
    t.start()
