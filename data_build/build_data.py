"""Combine downloaded public records with the project's outputs into analysis tables.

  python data_build/build_data.py --data data

Inputs
  data/raw/openreview_submissions_<year>.csv, data/raw/openreview_ratings_<year>.csv  (fetch_openreview.py)
  data/raw/openalex_iclr2018_2020.csv                                                 (fetch_openalex.py)
  data/project_outputs_iclr2018_2020.csv                                              (released)
  data/year_windows.csv                                                               (released)
Outputs (data/built/)
  papers_iclr2018_2020.csv, human_ratings_iclr2018_2020.csv
"""
import argparse
import os

import pandas as pd

YEARS = [2018, 2019, 2020]


def read_years(raw, stem, years):
    frames = [pd.read_csv(os.path.join(raw, "%s_%d.csv" % (stem, y))) for y in years]
    return pd.concat(frames, ignore_index=True)


def human_summary(ratings):
    g = ratings.dropna(subset=["rating"]).groupby("openreview_id")["rating"]
    return pd.DataFrame({"mean_human_rating": g.mean(), "n_human_reviews": g.size()}).reset_index()


def citations(path, prefer_through_year=True):
    c = pd.read_csv(path)
    col = "citations_through_year" if prefer_through_year and c["citations_through_year"].notna().any() \
        else "cited_by_count_total"
    out = c[["openalex_id", col]].rename(columns={col: "citations_observed"})
    out["citation_basis"] = ("through %d" % int(c["through_year"].dropna().iloc[0])
                             if col == "citations_through_year" else "total as of " + str(c["retrieved"].iloc[0]))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default="data")
    a = ap.parse_args()
    raw, built = os.path.join(a.data, "raw"), os.path.join(a.data, "built")
    os.makedirs(built, exist_ok=True)

    # ICLR 2018-2020
    subs = read_years(raw, "openreview_submissions", YEARS)
    ratings = read_years(raw, "openreview_ratings", YEARS)
    ratings[["openreview_id", "year", "rating", "confidence"]].to_csv(
        os.path.join(built, "human_ratings_iclr2018_2020.csv"), index=False)
    papers = subs.merge(human_summary(ratings), on="openreview_id", how="left")

    windows = pd.read_csv(os.path.join(a.data, "year_windows.csv"))
    papers = papers.merge(windows.rename(columns={"cutoff": "year_cutoff"}), on="year", how="left")
    papers["in_band"] = ((papers["mean_human_rating"] - papers["year_cutoff"]).abs()
                         <= papers["bandwidth"]).astype(int)

    outputs = pd.read_csv(os.path.join(a.data, "project_outputs_iclr2018_2020.csv"))
    papers = papers.merge(outputs, on="openreview_id", how="left")
    cites = citations(os.path.join(raw, "openalex_iclr2018_2020.csv"))
    papers["openalex_id"] = papers["openalex_id"].map(lambda x: str(x).rsplit("/", 1)[-1] if pd.notna(x) else x)
    papers = papers.merge(cites, on="openalex_id", how="left")
    papers["linked"] = papers["citations_observed"].notna().astype(int)
    papers.loc[papers["linked"] == 1, "citations_imputed"] = float("nan")
    papers.to_csv(os.path.join(built, "papers_iclr2018_2020.csv"), index=False)

    print("papers: %d (in analysis sample: %d, linked: %d)"
          % (len(papers), papers["in_band"].sum(), papers["linked"].sum()))


if __name__ == "__main__":
    main()
