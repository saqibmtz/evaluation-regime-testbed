"""Topic overlap between reviews of the same paper.

Proposal: within-paper topic overlap is 0.86 among AI personas versus 0.40
among human reviewers; human-AI overlap is 0.33, rising to 0.44 when each
human review is matched with its closest AI persona (a best-of-four measure).

Overlap is computed upstream from review text, which is not redistributed:
each review is split into atomic topics, topics are embedded, a topic counts
as matched if any topic in the other review has cosine similarity >= 0.5, and
the balanced overlap averages both directions. The repository provides the
aggregated results by pair type (data/overlap_summary.csv).
"""
from common import load, parse_args, write_table

ORDER = ["ai-ai", "human-human", "human-ai", "human-best AI persona"]


def main():
    args = parse_args(__doc__).parse_args()
    table = load(args.data, "overlap")
    table["order"] = table["pair_type"].map({k: i for i, k in enumerate(ORDER)})
    table = table.sort_values("order").drop(columns="order")
    write_table(table, args.out, "02_review_similarity", "Topic overlap between reviews",
                note="Within-paper: mean overlap per paper, averaged across papers. "
                     "Pooled: mean over all pairs. 'human-best AI persona' takes, for each human "
                     "review, the most similar of the AI persona reviews of the same paper.")


if __name__ == "__main__":
    main()
