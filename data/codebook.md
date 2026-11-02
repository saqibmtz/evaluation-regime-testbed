# Codebook

The repository releases only what the project produced. Public records are downloaded by
`data_build/` and combined with the released files into the analysis tables. Missing values
are empty cells.

## Released files (`data/`)

### `project_outputs_iclr2018_2020.csv` — one row per ICLR 2018–2020 submission

| Column | Type | Description |
|---|---|---|
| `openreview_id` | str | OpenReview forum ID |
| `committee_score` | float | AI committee rating: weighted mean of persona ratings (1–10) |
| `score_empiricist`, `score_theorist`, `score_systems`, `score_novelty` | float | Persona ratings (1–10): Empiricist, Theorist, Systems Pragmatist, Novelty Gatekeeper |
| `head_threshold_accept` | 0/1 | Committee score-threshold rule |
| `head_deepseek_accept`, `head_deepseek_p` | 0/1, float | Decision stage on DeepSeek-V3.1: decision and probability of acceptance |
| `head_gemma9b_accept`, `head_gemma9b_p` | 0/1, float | Decision stage on Gemma-2-9B: decision and probability of acceptance |
| `arxiv_id`, `openalex_id` | str | Linkage to a later public version (our matching); empty if unmatched |
| `citations_imputed` | float | Imputed citations from a model on full-text embeddings (used for unlinked papers) |
| `topic_cluster` | int | Coarse topic cluster from full-text embeddings (fixed effects) |

### `year_windows.csv` — analysis choices for the acceptance-threshold design

| Column | Type | Description |
|---|---|---|
| `year` | int | Conference year |
| `cutoff` | float | Year-specific acceptance cutoff on the mean human rating |
| `bandwidth` | float | Year-specific bandwidth; papers within it form the analysis sample |

### `overlap_summary.csv` — topic overlap between reviews of the same paper (aggregated)

| Column | Type | Description |
|---|---|---|
| `pair_type` | str | `ai-ai`, `human-human`, `human-ai`, or `human-best AI persona` |
| `n_papers`, `n_pairs` | int | Papers and review pairs (for `human-best AI persona`: human reviews) |
| `mean_within_paper` | float | Mean overlap per paper, averaged across papers (0–1) |
| `mean_pooled` | float | Mean overlap across all pairs (0–1) |

Topic overlap: each review is split into atomic topics, topics are embedded (all-MiniLM-L6-v2), and a topic counts as matched if any topic in the other review has cosine similarity ≥ 0.5; the balanced overlap averages both directions. Review text is not released.

## Downloaded public records (`data/raw/`, not committed)

| File | Source | Script |
|---|---|---|
| `openreview_submissions_<year>.csv` | OpenReview: submission, decision text, accepted, tier | `fetch_openreview.py` |
| `openreview_ratings_<year>.csv` | OpenReview: one row per human review (rating, confidence) | `fetch_openreview.py` |
| `openalex_iclr2018_2020.csv` | OpenAlex: total citations, citations through a fixed year, retrieval date | `fetch_openalex.py` |

Decisions: oral, spotlight, and poster (and ICLR 2020 "talk") count as accepted; ICLR 2018 workshop invitations count as not accepted to the main conference.

## Analysis tables (`data/built/`, built by `build_data.py`, not committed)

`papers_iclr2018_2020.csv` adds to the released outputs: `year`, `accepted`, `decision_tier`, `mean_human_rating`, `n_human_reviews` (OpenReview); `year_cutoff`, `bandwidth`, `in_band` (|mean rating − cutoff| ≤ bandwidth); `citations_observed`, `citation_basis`, `linked` (OpenAlex). For linked papers `citations_imputed` is cleared.

`human_ratings_iclr2018_2020.csv`: one row per human review (`openreview_id`, `year`, `rating`, `confidence`).
