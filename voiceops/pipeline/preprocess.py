from pathlib import Path
from typing import Optional, Dict

import librosa
import numpy as np
import soundfile as sf
import noisereduce as nr

import subprocess
import tempfile


def convert_to_wav(input_path: str) -> str:
    output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name

    command = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-ac", "1",
        "-ar", "16000",
        output_path
    ]

    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return output_path


def load_audio(audio_path: str, sr: int = 16000):
    y, sr = librosa.load(audio_path, sr=sr, mono=True)
    return y, sr


def peak_normalize(y: np.ndarray, target_peak: float = 0.95) -> np.ndarray:
    peak = np.max(np.abs(y)) if len(y) > 0 else 0.0
    if peak == 0:
        return y
    return y * (target_peak / peak)


def denoise_audio(y: np.ndarray, sr: int) -> np.ndarray:
    if len(y) == 0:
        return y

    # Use first 0.5 sec as noise profile if available
    noise_len = min(len(y), int(sr * 0.5))
    y_noise = y[:noise_len] if noise_len > 0 else y

    reduced = nr.reduce_noise(
        y=y,
        sr=sr,
        y_noise=y_noise,
        stationary=False,
        prop_decrease=0.8,
    )
    return reduced.astype(np.float32)


def preprocess_audio(
    input_path: str,
    output_path: str,
    target_sr: int = 16000,
    apply_denoise: bool = True,
    apply_normalize: bool = True,
) -> Dict:
    input_path = convert_to_wav(input_path)

    y, sr = load_audio(input_path, sr=target_sr)
    original_duration_sec = len(y) / sr if sr > 0 else 0.0

    if apply_denoise:
        y = denoise_audio(y, sr)

    if apply_normalize:
        y = peak_normalize(y)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    sf.write(output_path, y, sr)

    return {
        "input_path": input_path,
        "output_path": output_path,
        "sample_rate": sr,
        "duration_sec": round(original_duration_sec, 3),
        "denoised": apply_denoise,
        "normalized": apply_normalize,
    }