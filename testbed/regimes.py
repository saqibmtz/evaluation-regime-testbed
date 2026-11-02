"""Selection regimes: rules that turn evaluator judgments into a selected portfolio.

A regime combines (i) a score that orders submissions, (ii) a decision rule,
and (iii) a capacity constraint. Regimes are applied within year because ICLR
acceptance thresholds differ by year.
"""
import numpy as np
import pandas as pd

PERSONA_COLS = ["score_empiricist", "score_theorist", "score_systems", "score_novelty"]

RULES = {
    "human": "mean human reviewer rating (the historical score rule)",
    "committee": "AI committee score (weighted mean of persona ratings)",
    "persona_mean": "unweighted mean of the four persona ratings",
    "persona_max": "maximum persona rating: one strong advocate can carry a paper",
    "persona_min": "minimum persona rating: any one persona can veto",
    "head:<name>": "decision-stage probability column head_<name>_p",
    "score": "any user-supplied score column (--score-column)",
    "actual": "historical accept/reject decisions (not budget-matched)",
}


def running_variable(df):
    """Distance of the mean human rating from the year-specific cutoff."""
    return df["mean_human_rating"] - df["year_cutoff"]


def regime_scores(df, rule, score_column=None):
    """Return the score each regime ranks submissions by (higher is better)."""
    if rule == "human":
        return df["mean_human_rating"]
    if rule == "committee":
        return df["committee_score"]
    if rule == "persona_mean":
        return df[PERSONA_COLS].mean(axis=1)
    if rule == "persona_max":
        return df[PERSONA_COLS].max(axis=1)
    if rule == "persona_min":
        return df[PERSONA_COLS].min(axis=1)
    if rule.startswith("head:"):
        col = "head_%s_p" % rule.split(":", 1)[1]
        if col not in df.columns:
            raise ValueError("column %s not found for rule %s" % (col, rule))
        return df[col]
    if rule == "score":
        if not score_column:
            raise ValueError("rule 'score' needs a score column")
        return df[score_column]
    raise ValueError("unknown rule: %s (known: %s)" % (rule, ", ".join(RULES)))


def pool_mask(df, band=None, use_in_band=True):
    """Papers eligible for comparison: the analysis sample, optionally narrowed
    to a band of +/- `band` rating points around the year-specific cutoff."""
    mask = pd.Series(True, index=df.index)
    if use_in_band and "in_band" in df.columns:
        mask &= df["in_band"] == 1
    if band is not None:
        mask &= running_variable(df).abs() <= band
    return mask


def _budget_for(budget, n_pool, n_human):
    if budget == "match_human":
        return n_human
    if isinstance(budget, float) and 0 < budget < 1:
        return int(round(budget * n_pool))
    return min(int(budget), n_pool)


def select(df, rule, pool, budget="match_human", score_column=None,
           tie_column="mean_human_rating"):
    """Apply a regime within each year of the pool.

    budget: "match_human" (the number the human score rule accepts in the same
    pool and year), an int per year, or a float in (0, 1) as a share of the pool.
    Returns a boolean Series (True = selected); False outside the pool.
    """
    selected = pd.Series(False, index=df.index)
    if rule == "actual":
        return pool & (df["accepted"] == 1)
    human_accepts = running_variable(df) >= 0
    if rule == "human" and budget == "match_human":
        return pool & human_accepts
    scores = regime_scores(df, rule, score_column)
    for _, idx in df[pool].groupby("year").groups.items():
        k = _budget_for(budget, len(idx), int(human_accepts.loc[idx].sum()))
        order = pd.DataFrame({
            "score": scores.loc[idx],
            "tie": df.loc[idx, tie_column] if tie_column in df.columns else 0.0,
        }).sort_values(["score", "tie"], ascending=False, na_position="last")
        selected.loc[order.index[:k]] = True
    return selected


def tiebreaker(df, band, rule="committee", score_column=None, base_pool=None):
    """Hybrid regime: humans decide outside the band; inside it, the AI regime
    reorders papers while holding the number accepted fixed."""
    if base_pool is None:
        base_pool = pool_mask(df)
    inside = base_pool & (running_variable(df).abs() <= band)
    outside = base_pool & ~inside
    human_outside = outside & (running_variable(df) >= 0)
    ai_inside = select(df, rule, inside, "match_human", score_column)
    return human_outside | ai_inside
