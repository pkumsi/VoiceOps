import json
import matplotlib.pyplot as plt


def main():
    with open("voiceops/eval/results_all.json", "r") as f:
        data = json.load(f)

    sample_ids = [d["sample_id"] for d in data]
    raw_wer = [d["baseline_0_raw"]["wer"] for d in data]
    gated_wer = [d["baseline_3_gated_retrieval"]["wer"] for d in data]

    x = range(len(sample_ids))

    plt.figure(figsize=(12, 5))
    plt.plot(x, raw_wer, marker="o", label="Raw Whisper")
    plt.plot(x, gated_wer, marker="o", label="Gated Retrieval Correction")
    plt.xticks(x, sample_ids, rotation=45)
    plt.ylabel("WER")
    plt.title("VoiceOps-HealthBench: Raw vs Corrected WER")
    plt.legend()
    plt.tight_layout()
    plt.savefig("voiceops/eval/wer_comparison.png", dpi=200)
    plt.show()


if __name__ == "__main__":
    main()