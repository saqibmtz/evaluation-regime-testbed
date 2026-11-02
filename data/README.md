# Data

Public records are not redistributed: the pipeline downloads them. This folder holds only what
the project produced, and the analysis tables are built locally by combining the two.

```bash
pip install -r requirements.txt
python data_build/fetch_openreview.py --years 2018 2019 2020 --out data/raw
python data_build/fetch_openalex.py --links data/project_outputs_iclr2018_2020.csv \
    --through-year 2025 --out data/raw/openalex_iclr2018_2020.csv
python data_build/build_data.py --data data
python tools/validate_data.py --data data
```

| Released here | Contents |
|---|---|
| `project_outputs_iclr2018_2020.csv` | AI committee, persona, and decision-stage outputs; linkage to arXiv/OpenAlex; imputed citations; topic clusters |
| `year_windows.csv` | Year-specific cutoffs and bandwidths used in the analysis |
| `overlap_summary.csv` | Topic overlap between reviews, aggregated by pair type |

| Downloaded by the pipeline | Source and terms |
|---|---|
| Submissions, human reviewer ratings, decisions (2018–2020) | OpenReview public records |
| Citation counts | OpenAlex (CC0) |

Citations are counted through a fixed year from OpenAlex's per-year counts, so rebuilt tables are
stable over time; small differences from the figures in the proposal (which used a dated snapshot)
are expected.

Not released: paper PDFs and full texts, review text (human or AI), and review-level or pair-level
records of AI reviews. Variable definitions are in `codebook.md`.

To test the code without network access, generate synthetic inputs with the same structure:
`python tests/make_synthetic_data.py --out /tmp/synthetic && python data_build/build_data.py --data /tmp/synthetic`
(values are random and carry no information).
