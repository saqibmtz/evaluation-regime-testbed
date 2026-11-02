"""Dispersion of individual scores and correlation with human scores.

Proposal: individual AI scores have a standard deviation of 0.59 versus 1.44
for human scores, with AI scores clustered at 5-6; committee scores correlate
only moderately with mean human scores (r = 0.38).

Human ratings are the individual OpenReview reviews (downloaded); AI ratings
are the individual persona ratings released with the project outputs.
"""
import numpy as np
import pandas as pd

from common import load, parse_args, write_table


PERSONA_COLS = ["score_empiricist", "score_theorist", "score_systems", "score_novelty"]


def summarize(label, ratings):
    r = ratings.dropna()
    return {"group": label, "n_reviews": len(r), "mean": r.mean(), "sd": r.std(),
            "share_rated_5_or_6": r.between(5, 6).mean()}


def main():
    args = parse_args(__doc__).parse_args()
    papers = load(args.data, "papers")
    human = load(args.data, "human_ratings")
    ai = papers[PERSONA_COLS].stack()
    write_table(pd.DataFrame([summarize("human", human["rating"]), summarize("AI persona", ai)]),
                args.out, "03a_score_dispersion", "Individual review scores")

    rows = []
    for label, d in [("analysis sample", papers[papers["in_band"] == 1]), ("all papers", papers)]:
        d = d[["committee_score", "mean_human_rating"]].dropna()
        rows.append({
            "sample": label,
            "n": len(d),
            "pearson_r": d["committee_score"].corr(d["mean_human_rating"]),
            "spearman_rho": d["committee_score"].corr(d["mean_human_rating"], method="spearman"),
        })
    write_table(pd.DataFrame(rows), args.out, "03b_committee_vs_human",
                "Committee score vs. mean human rating")


if __name__ == "__main__":
    main()
