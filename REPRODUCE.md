# Reproducing the proposal's results

First download the public records and build the analysis tables (see `data/README.md`), then:

```bash
python analysis/run_all.py --data data --out results
```

Rebuilt tables count citations through a fixed year, so small differences from the proposal's
figures (which used a dated citation snapshot) are expected.

| Claim in the proposal | Script | Output | Value reported |
|---|---|---|---|
| The best decision configuration agrees with historical decisions | `analysis/01_agreement.py` | `results/01_agreement.csv` | 73.6% |
| Decision configurations accept far fewer papers than historically | `analysis/01_agreement.py` | `results/01_agreement.csv` | 20.7% / 24.0% / 46.1% vs. 48.7% |
| Two decision heads given the same committee evidence differ | `analysis/01_agreement.py` | `results/01_agreement.csv` | 20.7% vs. 46.1% accepted; 63.1% vs. 73.6% agreement |
| AI personas' reviews overlap far more than human reviews | `analysis/02_review_similarity.py` | `results/02_review_similarity.csv` | 0.86 vs. 0.40 |
| Human–AI overlap is meaningful but incomplete | `analysis/02_review_similarity.py` | `results/02_review_similarity.csv` | 0.33 (best persona match 0.44) vs. 0.40 |
| AI scores are compressed before aggregation | `analysis/03_score_dispersion.py` | `results/03a_score_dispersion.csv` | SD 0.59 vs. 1.44 |
| Committee scores correlate moderately with human scores | `analysis/03_score_dispersion.py` | `results/03b_committee_vs_human.csv` | r = 0.38 |
| Acceptance increases subsequent citations | `analysis/04_acceptance_effect.py` | `results/04_acceptance_effect.csv` | positive (reduced form and Wald reported) |
| Committee-only selections have higher observed citations in all three bands | `analysis/05_band_comparison.py` | `results/05a_band_swaps.csv` | ±0.25, ±0.5, ±0.75 |
| The advantage disappears without the top citation decile | `analysis/05_band_comparison.py` | `results/05a_band_swaps.csv` (`excluding top decile`) | — |

Notes

- The analysis sample is the set of papers within the year-specific bandwidth around the acceptance cutoff (`in_band == 1`).
- Topic overlap is reported from the released aggregate (`data/overlap_summary.csv`). Score dispersion uses downloaded human ratings and the released persona ratings.
- Band comparisons hold the number selected fixed within each year and band. Observed-citation results use linked papers only; `filled` results add imputed citations for unlinked papers.
