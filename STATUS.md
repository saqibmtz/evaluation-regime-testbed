# Status of this review version

| Component | Status |
|---|---|
| Testbed: regimes, metrics, `evaluate_regime.py` | Complete |
| Analysis scripts reproducing the proposal's numbers | Complete |
| Download scripts (OpenReview, OpenAlex) and table builder | Complete (tested on synthetic inputs) |
| Codebook, data validation, synthetic-data tests | Complete |
| AI committee pipeline (`pipeline/committee.py`) and prompts | Complete (prompt provenance in `prompts/README.md`) |
| Released project outputs in `data/` (`project_outputs_*.csv`, `year_windows.csv`, `overlap_summary.csv`) | [[TO ADD]] |
| Original pilot scripts (`pipeline/original/`, `data_build/original/`) | [[TO ADD]] |

Planned for the next stage: the out-of-sample check on review cycles after the models' training cutoff (ICLR 2025), deliberation and rule-aware committees (rules communicated to AI reviewers rather than applied after scoring), information-partitioned and multi-model committees, look-ahead diagnostics (recognition probes, anonymized and paraphrased submissions), and extension to later review cycles and other OpenReview venues.
