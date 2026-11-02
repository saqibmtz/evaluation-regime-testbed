"""Generate SYNTHETIC inputs with the same structure as the real pipeline, for testing.

Writes stand-ins for the downloaded public records (data/raw/) and for the
released project outputs (data/), so that data_build/build_data.py, the
analysis scripts, and the testbed can be run end to end. Values are random and
carry no information about the real pilot.

  python tests/make_synthetic_data.py --out /tmp/synthetic
  python data_build/build_data.py --data /tmp/synthetic
"""
import argparse
import os

import numpy as np
import pandas as pd

PERSONAS = ["empiricist", "theorist", "systems", "novelty"]
WINDOWS = {2018: (6.0, 1.5), 2019: (5.7, 1.5), 2020: (5.5, 1.5)}


def make(out, seed=0):
    rng = np.random.default_rng(seed)
    raw = os.path.join(out, "raw")
    os.makedirs(raw, exist_ok=True)
    outputs, alex = [], []
    for year, n in [(2018, 300), (2019, 450), (2020, 550)]:
        cutoff = WINDOWS[year][0]
        quality = rng.normal(0, 1, n)
        subs, ratings = [], []
        for i in range(n):
            pid = "s%d_%04d" % (year, i)
            human = np.clip(np.round(5.5 + 1.1 * quality[i] + rng.normal(0, 1.4, 3)), 1, 10)
            accepted = rng.random() < 1 / (1 + np.exp(-4 * (human.mean() - cutoff)))
            subs.append({"openreview_id": pid, "year": year, "title": "synthetic %s" % pid,
                         "decision_raw": "Accept (Poster)" if accepted else "Reject",
                         "accepted": int(accepted), "decision_tier": "poster" if accepted else "reject"})
            for k, r in enumerate(human):
                ratings.append({"openreview_id": pid, "year": year, "review_id": "%s_r%d" % (pid, k),
                                "rating": int(r), "confidence": int(rng.integers(2, 6))})
            committee = float(np.clip(5.5 + 0.3 * quality[i] + rng.normal(0, 0.35), 3, 8))
            persona = np.clip(np.round(committee + rng.normal(0, 0.4, 4)), 1, 10)
            p_ds = 1 / (1 + np.exp(-3 * (committee - 6.0)))
            p_g = 1 / (1 + np.exp(-3 * (committee - 5.5)))
            linked = rng.random() < 1 / (1 + np.exp(-(human.mean() - 4.5)))
            oa = "W%d%04d" % (year, i) if linked else np.nan
            outputs.append({
                "openreview_id": pid, "committee_score": round(committee, 3),
                **{"score_" + p: v for p, v in zip(PERSONAS, persona)},
                "head_threshold_accept": int(committee >= 6.0),
                "head_deepseek_accept": int(p_ds > 0.5), "head_deepseek_p": round(p_ds, 3),
                "head_gemma9b_accept": int(p_g > 0.5), "head_gemma9b_p": round(p_g, 3),
                "arxiv_id": np.nan, "openalex_id": oa,
                "citations_imputed": round(float(np.exp(2.5 + 0.3 * quality[i])), 1),
                "topic_cluster": int(rng.integers(0, 8)),
            })
            if linked:
                total = float(np.round(np.exp(2.5 + 0.8 * quality[i] + 0.4 * accepted + rng.normal(0, 1))))
                alex.append({"openalex_id": oa, "cited_by_count_total": total,
                             "citations_through_year": round(total * 0.9), "through_year": 2025,
                             "retrieved": "2026-01-01"})
        pd.DataFrame(subs).to_csv(os.path.join(raw, "openreview_submissions_%d.csv" % year), index=False)
        pd.DataFrame(ratings).to_csv(os.path.join(raw, "openreview_ratings_%d.csv" % year), index=False)
    pd.DataFrame(alex).to_csv(os.path.join(raw, "openalex_iclr2018_2020.csv"), index=False)
    pd.DataFrame(outputs).to_csv(os.path.join(out, "project_outputs_iclr2018_2020.csv"), index=False)
    pd.DataFrame([{"year": y, "cutoff": c, "bandwidth": b} for y, (c, b) in WINDOWS.items()]).to_csv(
        os.path.join(out, "year_windows.csv"), index=False)

    pd.DataFrame([
        {"pair_type": "ai-ai", "n_papers": 1300, "n_pairs": 7800, "mean_within_paper": 0.86, "mean_pooled": 0.86},
        {"pair_type": "human-human", "n_papers": 1300, "n_pairs": 3900, "mean_within_paper": 0.40, "mean_pooled": 0.40},
        {"pair_type": "human-ai", "n_papers": 1300, "n_pairs": 15600, "mean_within_paper": 0.33, "mean_pooled": 0.33},
        {"pair_type": "human-best AI persona", "n_papers": 1300, "n_pairs": 3900,
         "mean_within_paper": 0.44, "mean_pooled": 0.44},
    ]).to_csv(os.path.join(out, "overlap_summary.csv"), index=False)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    make(ap.parse_args().out)
