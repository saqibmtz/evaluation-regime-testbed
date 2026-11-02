# Selection Regime Testbed

*Anonymized research artifact.*

Organizations select ideas under uncertainty: funders choose proposals, firms choose projects, journals and conferences choose papers. Which ideas advance depends on who evaluates, what information evaluators see, how their judgments are combined, and how many ideas can be supported. We call such a combination a **selection regime**.

This repository is a prototype testbed for comparing human, AI, and hybrid selection regimes **on the same pool of submissions under a common budget**, and for assessing the portfolios they select by later scientific impact. The pilot uses peer review at the International Conference on Learning Representations (ICLR), 2018–2020, where rejected submissions, reviews, scores, and decisions are all public.

AI plays two roles here: it is an **evaluator** whose value we assess, and an **instrument** that makes evaluation systems experimentable. Rerunning a committee over thousands of submissions under different compositions and decision rules is costly and disruptive with human experts, but feasible with AI committees.

## What is in the repository

| Folder | Contents |
|---|---|
| `pipeline/` | The AI review committee: section-level focus notes → persona reviews → area-chair synthesis → decision stage. Runs against any OpenAI-compatible endpoint serving open-weight models. |
| `prompts/` | All prompts used by the committee (see `prompts/README.md`). |
| `configs/` | Model, persona, and weighting configuration. |
| `testbed/` | Selection regimes, portfolio metrics, and a command-line evaluator (`evaluate_regime.py`). |
| `analysis/` | Scripts that reproduce each number reported in the proposal (`run_all.py` runs them all). |
| `data/` | The project's own outputs (AI evaluations, linkage, imputed citations, analysis windows, aggregated overlap), with a codebook. |
| `data_build/` | Scripts that download public records (OpenReview, OpenAlex) and build the analysis tables. |
| `tools/` | Data validation and an anonymity scan. |
| `tests/` | End-to-end tests on synthetic data. |

## Quick start

```bash
pip install -r requirements.txt

# Download public records and build the analysis tables (see data/README.md)
python data_build/fetch_openreview.py --years 2018 2019 2020 --out data/raw
python data_build/fetch_openalex.py --links data/project_outputs_iclr2018_2020.csv --through-year 2025 --out data/raw/openalex_iclr2018_2020.csv
python data_build/build_data.py --data data

# Reproduce the proposal's results (no GPU)
python analysis/run_all.py --data data --out results
# -> results/SUMMARY.md; see REPRODUCE.md for which table backs which claim

# Compare the AI committee with the human score rule within ±0.25 rating points of the cutoff
python testbed/evaluate_regime.py --rule committee --band 0.25

# Hybrid regime: humans decide outside the band, the committee breaks ties inside it
python testbed/evaluate_regime.py --rule tiebreaker --band 0.5

# Alternative decision rules over the same persona judgments
python testbed/evaluate_regime.py --rule persona_max   # one strong advocate can carry a paper
python testbed/evaluate_regime.py --rule persona_min   # any persona can veto
```

## Plug in your own evaluator

Score the submissions with any evaluator (a different model, prompt, or committee), save a CSV with `openreview_id` and your score column, and compare it with the human rule at the same budget:

```bash
python testbed/evaluate_regime.py --rule score --scores-file my_scores.csv --score-column my_model --band 0.5
```

The report gives each regime's portfolio, mean citations, capture of the most highly cited papers, and the papers that enter or leave relative to the comparison regime.

## Run the AI committee

```bash
# Inspect the flow with placeholder outputs (no model needed)
python pipeline/committee.py --paper examples/sample_paper.txt --dry-run

# Run against an endpoint (configure configs/pipeline.yaml first)
export LLM_API_KEY=...
python data_build/download_openreview_pdfs.py --limit 20 --out pdfs/   # then extract text
python pipeline/committee.py --paper paper.txt --decision-head deepseek --out review.json
```

The pilot used Gemma-4-31B for the committee and DeepSeek-V3.1 and Gemma-2-9B as decision stages.

## Levels of replication

1. **Reproduce every reported number:** download the public records, build the tables, and run `analysis/run_all.py` (no GPU).
2. **Rerun the committee on a sample** of OpenReview submissions and compare with the released committee scores.
3. **Regenerate the project outputs** (linkage, imputation, topic overlap) with the scripts in `data_build/original/`.

## Interpreting the comparisons

Two problems complicate comparisons on citations, and they bias results in opposite directions:

- **Selection effects.** Acceptance itself raises citations, which favors whichever regime most resembles the historical decisions. `analysis/04_acceptance_effect.py` estimates the effect of acceptance at the cutoff; `analysis/05_band_comparison.py` compares regimes on observed citations, where this bias works against papers the AI promotes.
- **Look-ahead bias.** Models trained after these review cycles may know which papers later succeeded. `analysis/05_band_comparison.py` reports results excluding the top citation decile; evaluation on review cycles after the models' training cutoff is planned (see `STATUS.md`).

Citations are an imperfect proxy for scientific value; upper-tail citation impact is used as a proxy for breakthrough potential.

## Data and ethics

All sources are public, and public records are downloaded by the pipeline rather than redistributed. The repository releases only the project's own outputs: AI evaluation scores, linkage, imputed citations, analysis windows, and aggregated topic overlap. It does not include paper PDFs, full texts, or review text. The project involves no human subjects and audits rather than deploys AI evaluators. AI-generated review text is not released in a form that attaches critiques to named authors. See `data/README.md`.

## Status

See `STATUS.md` for what this review version contains and what remains in progress.

## License

Code: MIT (see `LICENSE`). Data: see `data/README.md` for the terms of each source.
