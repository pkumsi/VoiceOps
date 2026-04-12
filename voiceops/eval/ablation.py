import json
import statistics as stats


def avg(items, key):
    vals = [x[key] for x in items]
    return round(stats.mean(vals), 4)


def summarize(entries, field):
    rows = [e[field] for e in entries]
    return {
        "wer": avg(rows, "wer"),
        "cer": avg(rows, "cer"),
        "keyword_acc": avg(rows, "keyword_acc"),
        "numeric_acc": avg(rows, "numeric_acc"),
        "negation_acc": avg(rows, "negation_acc"),
    }


def main():
    with open("voiceops/eval/results_all.json", "r") as f:
        data = json.load(f)

    summary = {
        "baseline_0_raw": summarize(data, "baseline_0_raw"),
        "baseline_1_normalized": summarize(data, "baseline_1_normalized"),
        "baseline_2_retrieval": summarize(data, "baseline_2_retrieval"),
        "baseline_3_gated_retrieval": summarize(data, "baseline_3_gated_retrieval"),
    }

    with open("voiceops/eval/ablation_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()