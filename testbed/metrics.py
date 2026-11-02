"""Portfolio metrics: average citation impact and coverage of the upper tail."""
import numpy as np
import pandas as pd


def outcome(df, mode="observed"):
    """Citation outcome used for comparisons.

    observed: citations for papers linked to a public version; NaN otherwise.
    filled:   observed citations where linked, imputed citations otherwise.
    """
    if mode == "observed":
        return df["citations_observed"].where(df["linked"] == 1)
    if mode == "filled":
        return df["citations_observed"].where(df["linked"] == 1, df["citations_imputed"])
    raise ValueError("unknown outcome mode: %s" % mode)


def top_flags(values, groups, q=0.9):
    """True for papers at or above the q-th quantile of the outcome within each
    group (by default, year). Papers with missing outcomes are never flagged."""
    thresh = values.groupby(groups).transform(lambda v: v.quantile(q))
    return (values >= thresh) & values.notna()


def portfolio_summary(selected, pool, y, top):
    """Size, mean outcome, and upper-tail coverage of a selected portfolio."""
    sel = selected & pool
    top_pool = top & pool
    n_top = int(top_pool.sum())
    return {
        "n_pool": int(pool.sum()),
        "n_selected": int(sel.sum()),
        "n_selected_with_outcome": int((sel & y.notna()).sum()),
        "mean_citations": float(y[sel].mean()) if sel.any() else np.nan,
        "top_in_pool": n_top,
        "top_captured": int((top_pool & sel).sum()),
        "top_capture_share": float((top_pool & sel).sum() / n_top) if n_top else np.nan,
    }


def swap_summary(sel_a, sel_b, pool, y):
    """Compare the papers only regime A selects with those only regime B selects."""
    only_a = pool & sel_a & ~sel_b
    only_b = pool & sel_b & ~sel_a
    mean_a = float(y[only_a].mean()) if only_a.any() else np.nan
    mean_b = float(y[only_b].mean()) if only_b.any() else np.nan
    return {
        "n_only_a": int(only_a.sum()),
        "n_only_b": int(only_b.sum()),
        "n_only_a_with_outcome": int((only_a & y.notna()).sum()),
        "n_only_b_with_outcome": int((only_b & y.notna()).sum()),
        "mean_only_a": mean_a,
        "mean_only_b": mean_b,
        "difference": mean_a - mean_b,
    }
