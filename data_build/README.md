# Building the analysis tables

| Script | What it does |
|---|---|
| `fetch_openreview.py` | Downloads ICLR submissions, human reviewer ratings, and decisions from OpenReview (API v1 for 2018–2020, API v2 for later years) |
| `fetch_openalex.py` | Downloads citation counts from OpenAlex for linked papers; can count citations through a fixed year |
| `build_data.py` | Combines the downloads with the released project outputs into `data/built/` |
| `download_openreview_pdfs.py` | Downloads submission PDFs, e.g., to rerun the AI committee on a sample |

The released project outputs were produced as follows:

1. **AI evaluations.** `pipeline/committee.py` was run on the full text of each submission.
2. **Linkage.** Submissions were matched to later public versions on arXiv by title and abstract (exact, then fuzzy matching), then to OpenAlex records.
3. **Imputation.** Unlinked submissions received imputed citations from a ridge model on full-text embeddings (SPECTER2, references removed), estimated on linked papers from the same or earlier years.
4. **Analysis windows.** Year-specific cutoffs and bandwidths were selected for the acceptance-threshold design.
5. **Topic overlap.** Reviews were split into atomic topics and compared within paper; only aggregated results are released.

The original scripts for steps 2–5 are in `original/` (see `STATUS.md`).
