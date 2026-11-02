"""Evaluate a selection regime against a comparison regime on the same pool.

Examples
  # AI committee vs. human score rule, within +/-0.25 points of the cutoff
  python testbed/evaluate_regime.py --rule committee --band 0.25

  # Hybrid: humans decide outside the band, the committee breaks ties inside
  python testbed/evaluate_regime.py --rule tiebreaker --band 0.5

  # Plug in your own evaluator: a CSV with openreview_id and a score column
  python testbed/evaluate_regime.py --rule score --scores-file my_scores.csv --score-column my_model

The report lists the portfolio each regime selects at a common budget, its mean
citations, its capture of the upper tail, and the papers that enter or leave.
"""
import argparse
import os
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from testbed import metrics, regimes  # noqa: E402


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", default=os.path.join(ROOT, "data"))
    p.add_argument("--rule", default="committee",
                   help="regime to evaluate: %s, or tiebreaker" % ", ".join(regimes.RULES))
    p.add_argument("--compare-to", default="human", help="comparison regime (default: human score rule)")
    p.add_argument("--band", type=float, default=None,
                   help="restrict to papers within +/- BAND rating points of the cutoff")
    p.add_argument("--budget", default="match_human",
                   help="'match_human', an integer per year, or a share in (0, 1)")
    p.add_argument("--outcome", default="observed", choices=["observed", "filled"])
    p.add_argument("--top-q", type=float, default=0.9)
    p.add_argument("--scores-file", help="CSV with openreview_id and extra score columns")
    p.add_argument("--score-column", help="column used by --rule score")
    p.add_argument("--out", help="write the per-paper selection table here")
    a = p.parse_args()

    df = pd.read_csv(os.path.join(a.data, "built", "papers_iclr2018_2020.csv"))
    if a.scores_file:
        df = df.merge(pd.read_csv(a.scores_file), on="openreview_id", how="left")
    budget = a.budget
    if budget != "match_human":
        budget = float(budget) if "." in budget else int(budget)

    base = regimes.pool_mask(df)
    if a.rule == "tiebreaker":
        if a.band is None:
            sys.exit("--rule tiebreaker needs --band")
        pool = base
        chosen = regimes.tiebreaker(df, a.band, score_column=a.score_column)
    else:
        pool = regimes.pool_mask(df, band=a.band)
        chosen = regimes.select(df, a.rule, pool, budget, a.score_column)
    compare = regimes.select(df, a.compare_to, pool, budget, a.score_column)

    y = metrics.outcome(df, a.outcome)
    top = metrics.top_flags(y.where(base), df["year"], a.top_q)
    report = pd.DataFrame([dict(regime=a.rule, **metrics.portfolio_summary(chosen, pool, y, top)),
                           dict(regime=a.compare_to, **metrics.portfolio_summary(compare, pool, y, top))])
    swaps = metrics.swap_summary(chosen, compare, pool, y)

    print("Pool: %d papers%s; outcome: %s citations; upper tail: top %.0f%% within year\n"
          % (pool.sum(), "" if a.band is None else " within +/-%.2f of the cutoff" % a.band,
             a.outcome, 100 * (1 - a.top_q)))
    print(report.to_string(index=False, float_format=lambda v: "%.3f" % v))
    print("\nOnly %s: %d papers (mean %.2f); only %s: %d papers (mean %.2f); difference %.2f"
          % (a.rule, swaps["n_only_a"], swaps["mean_only_a"], a.compare_to, swaps["n_only_b"],
             swaps["mean_only_b"], swaps["difference"]))

    if a.out:
        status = pd.Series("neither", index=df.index)
        status[chosen & compare] = "both"
        status[chosen & ~compare] = a.rule + " only"
        status[~chosen & compare] = a.compare_to + " only"
        out = df.loc[pool, ["openreview_id", "year", "mean_human_rating", "committee_score"]].copy()
        out["status"] = status[pool]
        out["citations"] = y[pool]
        out.to_csv(a.out, index=False)
        print("\nPer-paper selections written to " + a.out)


if __name__ == "__main__":
    main()
