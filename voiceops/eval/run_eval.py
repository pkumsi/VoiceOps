import json

from voiceops.pipeline.transcribe import Transcriber
from voiceops.pipeline.normalize import normalize_transcript
from voiceops.pipeline.correct import correct_transcript_with_retrieval
from voiceops.eval.lexical import compute_wer, compute_cer
from voiceops.eval.domain import domain_keyword_accuracy
from voiceops.eval.safety import numeric_accuracy, negation_accuracy
from voiceops.pipeline.correct import (
    correct_transcript_with_retrieval,
    correct_transcript_with_gated_retrieval,
)

transcriber = Transcriber(model_size="base")


def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def get_audio_folder(sample):
    if sample.get("accent", "general_american") != "general_american":
        return "accented"

    condition = sample.get("audio_condition", "clean")
    if condition == "clean":
        return "clean"
    if condition == "telephony_8khz":
        return "telephony"
    return "noisy"


def score(sample, ref, hyp):
    return {
        "wer": compute_wer(ref, hyp),
        "cer": compute_cer(ref, hyp),
        "keyword_acc": domain_keyword_accuracy(sample["target_keywords"], hyp),
        "numeric_acc": numeric_accuracy(sample["target_numerics"], hyp),
        "negation_acc": negation_accuracy(sample["target_negations"], hyp),
        "hypothesis": hyp
    }


def run():
    samples = load_json("voiceops/benchmark/scripts/samples.json")
    ground_truth = load_json("voiceops/benchmark/scripts/ground_truth.json")

    results = []

    for sample in samples:
        sid = sample["sample_id"]
        folder = get_audio_folder(sample)
        audio_path = f"voiceops/benchmark/audio/{folder}/{sid}.wav"
        ref = ground_truth[sid]["reference_transcript"]

        raw_hyp = transcriber.transcribe(audio_path)
        norm_hyp = normalize_transcript(raw_hyp)

        retrieval_result = correct_transcript_with_retrieval(raw_hyp)
        retrieval_hyp = retrieval_result["corrected_text"]

        gated_result = correct_transcript_with_gated_retrieval(raw_hyp)
        gated_hyp = gated_result["corrected_text"]

        results.append({
            "sample_id": sid,
            "reference": ref,
            "baseline_0_raw": score(sample, ref, raw_hyp),
            "baseline_1_normalized": score(sample, ref, norm_hyp),
            "baseline_2_retrieval": score(sample, ref, retrieval_hyp),
            "baseline_3_gated_retrieval": score(sample, ref, gated_hyp),
            "baseline_2_corrections": retrieval_result["corrections"],
            "baseline_3_corrections": gated_result["corrections"]
        })

    with open("voiceops/eval/results_all.json", "w") as f:
        json.dump(results, f, indent=2)

    print("Saved full results to voiceops/eval/results_all.json")


if __name__ == "__main__":
    run()