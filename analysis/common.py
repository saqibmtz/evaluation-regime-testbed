"""Shared helpers for the analysis scripts: data loading and table output."""
import argparse
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

FILES = {   # paths relative to the data folder
    "papers": os.path.join("built", "papers_iclr2018_2020.csv"),
    "human_ratings": os.path.join("built", "human_ratings_iclr2018_2020.csv"),
    "overlap": "overlap_summary.csv",
}


def parse_args(description):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--data", default=os.path.join(ROOT, "data"),
                        help="folder containing the processed CSV files")
    parser.add_argument("--out", default=os.path.join(ROOT, "results"),
                        help="folder for output tables")
    return parser


def load(data_dir, key):
    path = os.path.join(data_dir, FILES[key])
    if not os.path.exists(path):
        sys.exit("Missing %s. Build the analysis tables first (see data/README.md):\n"
                 "  python data_build/fetch_openreview.py\n  python data_build/fetch_openalex.py ...\n"
                 "  python data_build/build_data.py" % path)
    return pd.read_csv(path)


def ols_hc1(y, X):
    """OLS with heteroskedasticity-robust (HC1) standard errors.

    y: Series; X: DataFrame of regressors (include a constant column).
    Returns (coefficients, standard errors) as Series indexed by column name.
    """
    Xv, yv = X.to_numpy(dtype=float), y.to_numpy(dtype=float)
    n, k = Xv.shape
    xtx_inv = np.linalg.pinv(Xv.T @ Xv)
    beta = xtx_inv @ Xv.T @ yv
    resid = yv - Xv @ beta
    meat = (Xv * resid[:, None] ** 2).T @ Xv
    cov = xtx_inv @ meat @ xtx_inv * n / max(n - k, 1)
    return pd.Series(beta, index=X.columns), pd.Series(np.sqrt(np.diag(cov)), index=X.columns)


def fixed_effects(df, columns):
    """Dummy variables for one or more categorical columns (first level dropped)."""
    key = df[columns].astype(str).agg("_".join, axis=1) if len(columns) > 1 else df[columns[0]].astype(str)
    return pd.get_dummies(key, prefix="fe", drop_first=True, dtype=float)


def _fmt(value):
    if isinstance(value, (float, np.floating)):
        if np.isnan(value):
            return ""
        return "%.3f" % value
    return str(value)


def to_markdown(df):
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(_fmt(row[c]) for c in cols) + " |")
    return "\n".join(lines)


def write_table(df, out_dir, name, title=None, note=None):
    """Write a result table as CSV and Markdown, and echo it to the console."""
    os.makedirs(out_dir, exist_ok=True)
    df.to_csv(os.path.join(out_dir, name + ".csv"), index=False)
    md = ["## " + (title or name), "", to_markdown(df)]
    if note:
        md += ["", note]
    with open(os.path.join(out_dir, name + ".md"), "w") as fh:
        fh.write("\n".join(md) + "\n")
    print("\n".join(md) + "\n")
