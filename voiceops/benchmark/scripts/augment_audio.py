from pathlib import Path
import librosa
import numpy as np
import soundfile as sf


def add_gaussian_noise(y, noise_level=0.01):
    noise = np.random.normal(0, noise_level, len(y))
    return y + noise


def downsample_to_8k(y, sr):
    y_8k = librosa.resample(y, orig_sr=sr, target_sr=8000)
    return y_8k, 8000


def speed_perturb(y, rate=1.1):
    return librosa.effects.time_stretch(y, rate=rate)


def save_audio(path, y, sr):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    sf.write(path, y, sr)


def process_file(input_path, out_noisy, out_8k, out_fast):
    y, sr = librosa.load(input_path, sr=16000)

    y_noisy = add_gaussian_noise(y, noise_level=0.01)
    save_audio(out_noisy, y_noisy, sr)

    y_8k, sr_8k = downsample_to_8k(y, sr)
    save_audio(out_8k, y_8k, sr_8k)

    y_fast = speed_perturb(y, rate=1.08)
    save_audio(out_fast, y_fast, sr)


if __name__ == "__main__":
    base = Path("voiceops/benchmark/audio/clean")

    for wav in base.glob("*.wav"):
        sid = wav.stem
        process_file(
            str(wav),
            f"voiceops/benchmark/audio/augmented/{sid}_noisy.wav",
            f"voiceops/benchmark/audio/augmented/{sid}_8k.wav",
            f"voiceops/benchmark/audio/augmented/{sid}_fast.wav",
        )

    print("Augmented files generated.")