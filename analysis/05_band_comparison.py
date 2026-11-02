"""Committee vs. human score rule within bands around the cutoff.

Proposal: within bands of +/-0.25, 0.5, and 0.75 rating points, holding the
number selected fixed, papers selected only by the committee have higher
average observed citations than papers selected only by the human score rule;
the advantage is concentrated among the most highly cited papers and
disappears when the top citation decile is excluded.

The top decile is defined within year over the full analysis sample, not
within each band. Outcomes: 'observed' uses linked papers only; 'filled'
adds imputed citations for unlinked papers.
"""
import pandas as pd

from common import load, parse_args, write_table
from testbed import metrics, regimes

BANDS = [0.25, 0.5, 0.75]


def main():
    parser = parse_args(__doc__)
    parser.add_argument("--rule", default="committee", help="AI regime to compare (see testbed/regimes.py)")
    parser.add_argument("--top-q", type=float, default=0.9, help="quantile defining the upper tail")
    args = parser.parse_args()
    df = load(args.data, "papers")
    base = regimes.pool_mask(df)

    rows, tail_rows = [], []
    for band in BANDS:
        pool = regimes.pool_mask(df, band=band)
        human = regimes.select(df, "human", pool)
        ai = regimes.select(df, args.rule, pool)
        for mode in ["observed", "filled"]:
            y = metrics.outcome(df, mode)
            top = metrics.top_flags(y.where(base), df["year"], args.top_q)
            for subset, mask in [("all", pool), ("excluding top decile", pool & ~top)]:
                s = metrics.swap_summary(ai, human, mask, y)
                rows.append({"band": band, "outcome": mode, "papers": subset,
                             "n_in_band": int(pool.sum()), "n_selected": int(human.sum()),
                             "n_swapped_each_way": int((pool & ai & ~human).sum()),
                             "mean_ai_only": s["mean_only_a"], "mean_human_only": s["mean_only_b"],
                             "difference": s["difference"],
                             "n_ai_only_with_outcome": s["n_only_a_with_outcome"],
                             "n_human_only_with_outcome": s["n_only_b_with_outcome"]})
            for name, sel in [("human", human), (args.rule, ai)]:
                p = metrics.portfolio_summary(sel, pool, y, top)
                tail_rows.append({"band": band, "outcome": mode, "regime": name,
                                  "mean_citations": p["mean_citations"],
                                  "top_in_band": p["top_in_pool"], "top_captured": p["top_captured"],
                                  "top_capture_share": p["top_capture_share"]})

    write_table(pd.DataFrame(rows), args.out, "05a_band_swaps",
                "Papers selected only by the AI regime vs. only by the human score rule")
    write_table(pd.DataFrame(tail_rows), args.out, "05b_band_portfolios",
                "Portfolio mean citations and upper-tail capture within bands")


if __name__ == "__main__":
    main()
