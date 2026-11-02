"""Check that the processed data files match the codebook (data/codebook.md).

  python tools/validate_data.py --data data
"""
import argparse
import os
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REQUIRED = {   # released files, then tables built by data_build/build_data.py
    "project_outputs_iclr2018_2020.csv": [
        "openreview_id", "committee_score", "score_empiricist", "score_theorist", "score_systems",
        "score_novelty", "openalex_id", "citations_imputed", "topic_cluster"],
    "year_windows.csv": ["year", "cutoff", "bandwidth"],
    "overlap_summary.csv": ["pair_type", "n_papers", "n_pairs", "mean_within_paper", "mean_pooled"],
    "built/papers_iclr2018_2020.csv": [
        "openreview_id", "year", "mean_human_rating", "accepted", "year_cutoff", "in_band",
        "committee_score", "linked", "citations_observed", "citations_imputed", "topic_cluster"],
    "built/human_ratings_iclr2018_2020.csv": ["openreview_id", "year", "rating"],
}
RANGES = {"mean_human_rating": (1, 10), "committee_score": (1, 10), "rating": (1, 10),
          "mean_within_paper": (0, 1), "mean_pooled": (0, 1),
          "accepted": (0, 1), "in_band": (0, 1), "linked": (0, 1)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", default=os.path.join(ROOT, "data"))
    args = ap.parse_args()
    problems = []
    for name, cols in REQUIRED.items():
        path = os.path.join(args.data, name)
        if not os.path.exists(path):
            problems.append("missing file: " + name)
            continue
        df = pd.read_csv(path)
        missing = [c for c in cols if c not in df.columns]
        if missing:
            problems.append("%s: missing columns %s" % (name, missing))
        for col, (lo, hi) in RANGES.items():
            if col in df.columns:
                v = df[col].dropna()
                if len(v) and (v.min() < lo or v.max() > hi):
                    problems.append("%s: %s outside [%s, %s]" % (name, col, lo, hi))
        if name.endswith("papers_iclr2018_2020.csv") and df["openreview_id"].duplicated().any():
            problems.append("papers: duplicate openreview_id")
        if name.endswith("papers_iclr2018_2020.csv") and {"linked", "citations_observed"} <= set(df.columns):
            if df.loc[df["linked"] == 1, "citations_observed"].isna().any():
                problems.append("papers: linked papers with missing citations_observed")
        print("%-40s %6d rows, %2d columns" % (name, len(df), df.shape[1]))
    if problems:
        print("\nProblems:\n  " + "\n  ".join(problems))
        sys.exit(1)
    print("\nAll files match the codebook.")


if __name__ == "__main__":
    main()
