import os
import numpy as np
import librosa
import soundfile as sf
import random

CLEAN_DIR = "voiceops/benchmark/audio/clean"
NOISE_DIR = "voiceops/benchmark/noise"
OUTPUT_DIR = "voiceops/benchmark/audio/school_noise"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_audio(path, sr=16000):
    audio, _ = librosa.load(path, sr=sr)
    return audio


def match_length(noise, target_len):
    if len(noise) >= target_len:
        start = random.randint(0, len(noise) - target_len)
        return noise[start:start + target_len]
    else:
        repeats = int(np.ceil(target_len / len(noise)))
        noise = np.tile(noise, repeats)
        return noise[:target_len]


def add_noise(clean, noise, snr_db=10):
    clean_power = np.mean(clean ** 2)
    noise_power = np.mean(noise ** 2)

    snr_linear = 10 ** (snr_db / 10)
    scale = np.sqrt(clean_power / (snr_linear * noise_power))

    noisy = clean + noise * scale
    return noisy


def main():
    clean_files = [f for f in os.listdir(CLEAN_DIR) if f.endswith(".wav")]
    noise_files = [f for f in os.listdir(NOISE_DIR) if f.endswith(".wav")]

    for f in clean_files:
        clean_path = os.path.join(CLEAN_DIR, f)
        clean = load_audio(clean_path)

        noise_file = random.choice(noise_files)
        noise_path = os.path.join(NOISE_DIR, noise_file)
        noise = load_audio(noise_path)

        noise = match_length(noise, len(clean))

        # randomize noise level (important)
        snr_db = random.choice([5, 10, 15])

        noisy = add_noise(clean, noise, snr_db)

        # normalize to avoid clipping
        noisy = noisy / np.max(np.abs(noisy) + 1e-6)

        out_path = os.path.join(OUTPUT_DIR, f)
        sf.write(out_path, noisy, 16000)

        print(f"Created noisy file: {out_path} (SNR={snr_db})")


if __name__ == "__main__":
    main()