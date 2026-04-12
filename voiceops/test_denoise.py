from voiceops.pipeline.preprocess import preprocess_audio
from voiceops.pipeline.transcribe import Transcriber
from jiwer import wer

transcriber = Transcriber(model_size="base")

reference = "Please continue atorvastatin twenty milligrams every night."

raw_audio = "voiceops/benchmark/audio/augmented/VOX_001_noisy.wav"
denoised_audio = "voiceops/benchmark/audio/denoised/VOX_001_noisy_denoised.wav"

preprocess_audio(
    input_path=raw_audio,
    output_path=denoised_audio,
    target_sr=16000,
    apply_denoise=True,
    apply_normalize=True,
)

raw_hyp = transcriber.transcribe(raw_audio)
denoised_hyp = transcriber.transcribe(denoised_audio)

print("RAW:", raw_hyp)
print("DENOISED:", denoised_hyp)
print("RAW WER:", wer(reference, raw_hyp))
print("DENOISED WER:", wer(reference, denoised_hyp))