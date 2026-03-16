"""
Veracore Voice Demo — The Good Neighbor Guard
Built by Christopher Hughes · Sacramento, CA
Created with the help of AI collaborators (Claude · GPT · Gemini · Groq)next

Truth · Safety · We Got Your Back
"""

import queue
import threading
import sys
import config

SAMPLE_RATE = 16000
CHUNK_DURATION = 0.5
SILENCE_THRESHOLD = 500


def listen_for_question(timeout: float = 10.0) -> str | None:
    """
    Listen via microphone and return transcribed text.
    Uses Groq Whisper for fast, accurate STT.
    Returns None on failure or timeout.
    """
    if config.DRY_RUN:
        return _dry_run_input()

    try:
        import sounddevice as sd
        import numpy as np
        from groq import Groq
        import io
        import wave

        client = Groq(api_key=config.GROQ_API_KEY)
        audio_queue = queue.Queue()
        recording = []
        silence_count = 0
        max_silence_chunks = int(config.STT_SILENCE_THRESHOLD / CHUNK_DURATION)
        chunk_samples = int(SAMPLE_RATE * CHUNK_DURATION)

        print("[listener] Listening...")

        def callback(indata, frames, time, status):
            audio_queue.put(indata.copy())

        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                            dtype='int16', blocksize=chunk_samples,
                            callback=callback):
            while True:
                try:
                    chunk = audio_queue.get(timeout=timeout)
                    recording.append(chunk)

                    amplitude = np.abs(chunk).mean()
                    if amplitude < SILENCE_THRESHOLD:
                        silence_count += 1
                    else:
                        silence_count = 0

                    if silence_count >= max_silence_chunks and len(recording) > 2:
                        break

                except queue.Empty:
                    break

        if not recording:
            return None

        import numpy as np
        audio_data = np.concatenate(recording, axis=0)
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio_data.tobytes())
        wav_buffer.seek(0)
        wav_buffer.name = "audio.wav"

        transcription = client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=wav_buffer,
            language="en"
        )

        text = transcription.text.strip()
        print(f"[listener] Heard: {text}")
        return text if text else None

    except ImportError as e:
        print(f"[listener] Missing dependency: {e}")
        print("[listener] Run: pip install sounddevice groq numpy")
        return None
    except Exception as e:
        print(f"[listener] Error: {e}")
        return None


def _dry_run_input() -> str | None:
    """Simulate microphone input via keyboard for dry run testing."""
    try:
        text = input("[DRY RUN] Simulate heard question: ").strip()
        return text if text else None
    except (KeyboardInterrupt, EOFError):
        return None
