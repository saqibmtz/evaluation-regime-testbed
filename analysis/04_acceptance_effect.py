"""Effect of acceptance on citations at the year-specific cutoff.

Local linear regression discontinuity in the analysis sample (papers within
the year-specific bandwidth). Reports, on the same linked sample:
  - naive OLS of log(1 + citations) on acceptance,
  - the first stage (jump in acceptance probability at the cutoff),
  - the reduced form (jump in log citations at the cutoff),
  - the fuzzy-RD (Wald) estimate = reduced form / first stage.
The reduced form and the Wald estimate answer different questions; both are
reported so the proposal's wording can be checked against them.
"""
import numpy as np
import pandas as pd

from common import fixed_effects, load, ols_hc1, parse_args, write_table


def main():
    parser = parse_args(__doc__)
    parser.add_argument("--topic-fe", action="store_true",
                        help="use year-by-topic fixed effects instead of year fixed effects")
    args = parser.parse_args()
    df = load(args.data, "papers")
    d = df[(df["in_band"] == 1) & (df["linked"] == 1)].copy().reset_index(drop=True)
    y = np.log1p(d["citations_observed"])
    running = d["mean_human_rating"] - d["year_cutoff"]
    above = (running >= 0).astype(float)
    fe = fixed_effects(d, ["year", "topic_cluster"] if args.topic_fe else ["year"])
    const = pd.DataFrame({"const": 1.0}, index=d.index)

    rd_X = pd.concat([const, pd.DataFrame({"above": above, "running": running,
                                           "above_x_running": above * running}), fe], axis=1)
    naive_X = pd.concat([const, d[["accepted"]].astype(float), fe], axis=1)

    b_naive, se_naive = ols_hc1(y, naive_X)
    b_first, se_first = ols_hc1(d["accepted"].astype(float), rd_X)
    b_red, se_red = ols_hc1(y, rd_X)
    wald = b_red["above"] / b_first["above"]
    # Delta-method standard error ignoring the covariance between the two equations.
    wald_se = abs(wald) * np.sqrt((se_red["above"] / b_red["above"]) ** 2 +
                                  (se_first["above"] / b_first["above"]) ** 2)

    n = len(d)
    table = pd.DataFrame([
        {"estimate": "naive OLS: log citations on acceptance", "coef": b_naive["accepted"],
         "se": se_naive["accepted"], "n": n},
        {"estimate": "first stage: acceptance jump at cutoff", "coef": b_first["above"],
         "se": se_first["above"], "n": n},
        {"estimate": "reduced form: log-citation jump at cutoff", "coef": b_red["above"],
         "se": se_red["above"], "n": n},
        {"estimate": "fuzzy RD (Wald): effect of acceptance", "coef": wald, "se": wald_se, "n": n},
    ])
    write_table(table, args.out, "04_acceptance_effect",
                "Effect of acceptance on log(1 + citations)",
                note="Fixed effects: %s. Robust (HC1) standard errors; the Wald standard error "
                     "is an approximation." % ("year x topic" if args.topic_fe else "year"))


if __name__ == "__main__":
    main()
