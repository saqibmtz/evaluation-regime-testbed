"""Agreement between AI decision configurations and historical decisions.

Proposal: the best decision configuration agrees with human acceptance
decisions in 73.6% of cases; configurations accept 20.7-46.1% of papers
against 48.7% historically; recall of historical accepts.
"""
import pandas as pd

from common import load, parse_args, write_table

CONFIGS = {
    "committee score threshold": "head_threshold_accept",
    "decision head: DeepSeek-V3.1": "head_deepseek_accept",
    "decision head: Gemma-2-9B": "head_gemma9b_accept",
}


def main():
    args = parse_args(__doc__).parse_args()
    df = load(args.data, "papers")
    df = df[df["in_band"] == 1]
    rows = []
    for name, col in CONFIGS.items():
        if col not in df.columns:
            continue
        d = df[df[col].notna() & df["accepted"].notna()]
        pred, actual = d[col].astype(int), d["accepted"].astype(int)
        tp = int(((pred == 1) & (actual == 1)).sum())
        precision = tp / max(int(pred.sum()), 1)
        recall = tp / max(int(actual.sum()), 1)
        rows.append({
            "configuration": name,
            "n": len(d),
            "predicted_accept_rate": pred.mean(),
            "actual_accept_rate": actual.mean(),
            "agreement": (pred == actual).mean(),
            "recall_of_accepts": recall,
            "precision": precision,
            "f1": 2 * precision * recall / max(precision + recall, 1e-12),
        })
    write_table(pd.DataFrame(rows), args.out, "01_agreement",
                "Agreement with historical decisions (analysis sample)")


if __name__ == "__main__":
    main()
