import queue
import sys
import tempfile
import threading
import time
from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf

from voiceops.pipeline.preprocess import preprocess_audio
from voiceops.pipeline.transcribe import Transcriber
from voiceops.pipeline.normalize import normalize_transcript
from voiceops.pipeline.correct import correct_transcript_with_gated_retrieval


SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_SECONDS = 4

audio_queue = queue.Queue()
stop_flag = threading.Event()


def audio_callback(indata, frames, time_info, status):
    if status:
        print(status, file=sys.stderr)
    audio_queue.put(indata.copy())


def save_chunk(audio_np: np.ndarray, out_path: str):
    sf.write(out_path, audio_np, SAMPLE_RATE)


def transcribe_chunk(transcriber: Transcriber, chunk_path: str):
    preprocessed_path = chunk_path.replace(".wav", "_prep.wav")

    preprocess_audio(
        input_path=chunk_path,
        output_path=preprocessed_path,
        target_sr=16000,
        apply_denoise=True,
        apply_normalize=True,
    )

    raw = transcriber.transcribe(preprocessed_path)
    norm = normalize_transcript(raw)
    corrected = correct_transcript_with_gated_retrieval(norm)["corrected_text"]
    return raw, corrected


def main():
    transcriber = Transcriber(model_size="base")
    transcript_parts = []

    print("Recording near-live chunks. Press Ctrl+C to stop.\n")

    try:
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="float32",
            callback=audio_callback,
        ):
            buffer = []
            start_time = time.time()

            while True:
                data = audio_queue.get()
                buffer.append(data)

                elapsed = time.time() - start_time
                if elapsed >= CHUNK_SECONDS:
                    chunk_audio = np.concatenate(buffer, axis=0)

                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                        chunk_path = tmp.name

                    save_chunk(chunk_audio, chunk_path)
                    raw, corrected = transcribe_chunk(transcriber, chunk_path)

                    transcript_parts.append(corrected)

                    print("\n--- chunk transcript ---")
                    print("RAW      :", raw)
                    print("CORRECTED:", corrected)
                    print("\nLIVE TRANSCRIPT:")
                    print(" ".join(transcript_parts))
                    print("------------------------")

                    buffer = []
                    start_time = time.time()

    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()