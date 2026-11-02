"""Run the full analysis and testbed on synthetic data: python -m pytest tests"""
import os
import subprocess
import sys

import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests"))
from make_synthetic_data import make  # noqa: E402
from testbed import metrics, regimes  # noqa: E402


@pytest.fixture(scope="module")
def data_dir(tmp_path_factory):
    d = tmp_path_factory.mktemp("synthetic")
    make(str(d))
    subprocess.check_call([sys.executable, "data_build/build_data.py", "--data", str(d)], cwd=ROOT)
    return str(d)


def run(*args):
    subprocess.check_call([sys.executable] + list(args), cwd=ROOT)


def test_validate(data_dir):
    run("tools/validate_data.py", "--data", data_dir)


def test_run_all(data_dir, tmp_path):
    out = str(tmp_path / "results")
    run("analysis/run_all.py", "--data", data_dir, "--out", out)
    for name in ["01_agreement", "02_review_similarity", "03a_score_dispersion",
                 "03b_committee_vs_human", "04_acceptance_effect", "05a_band_swaps",
                 "05b_band_portfolios"]:
        assert os.path.exists(os.path.join(out, name + ".csv")), name
    assert os.path.exists(os.path.join(out, "SUMMARY.md"))


@pytest.mark.parametrize("rule", ["committee", "persona_max", "persona_min", "head:deepseek"])
def test_budget_is_matched(data_dir, rule):
    df = pd.read_csv(os.path.join(data_dir, "built", "papers_iclr2018_2020.csv"))
    pool = regimes.pool_mask(df, band=0.5)
    human = regimes.select(df, "human", pool)
    other = regimes.select(df, rule, pool)
    for year in df["year"].unique():
        in_year = df["year"] == year
        assert (human & in_year).sum() == (other & in_year).sum()


def test_tiebreaker_keeps_total(data_dir):
    df = pd.read_csv(os.path.join(data_dir, "built", "papers_iclr2018_2020.csv"))
    base = regimes.pool_mask(df)
    hybrid = regimes.tiebreaker(df, 0.25)
    human = regimes.select(df, "human", base)
    assert hybrid.sum() == human.sum()


def test_cli(data_dir, tmp_path):
    out = str(tmp_path / "sel.csv")
    run("testbed/evaluate_regime.py", "--data", data_dir, "--rule", "committee",
        "--band", "0.25", "--out", out)
    run("testbed/evaluate_regime.py", "--data", data_dir, "--rule", "tiebreaker", "--band", "0.5")
    assert len(pd.read_csv(out)) > 0
