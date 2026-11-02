"""Download citation counts from OpenAlex for papers linked to a public version.

  python data_build/fetch_openalex.py --links data/project_outputs_iclr2018_2020.csv \
      --through-year 2025 --out data/raw/openalex_iclr2018_2020.csv

Counting citations through a fixed year (from OpenAlex's per-year counts) gives
a stable outcome that does not drift as new citations accrue. Without
--through-year, the current total is recorded with the retrieval date.
"""
import argparse
import datetime
import os
import time

import pandas as pd
import requests

API = "https://api.openalex.org/works"


def short_id(x):
    return str(x).rsplit("/", 1)[-1]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--links", required=True, help="CSV with an openalex_id column")
    ap.add_argument("--through-year", type=int, default=None)
    ap.add_argument("--out", required=True)
    ap.add_argument("--mailto", default=None, help="optional contact address for OpenAlex's polite pool")
    ap.add_argument("--sleep", type=float, default=0.2)
    a = ap.parse_args()

    ids = sorted({short_id(x) for x in pd.read_csv(a.links)["openalex_id"].dropna()})
    rows = []
    for start in range(0, len(ids), 50):
        batch = ids[start:start + 50]
        params = {"filter": "ids.openalex:" + "|".join(batch), "per-page": 50,
                  "select": "id,cited_by_count,counts_by_year"}
        if a.mailto:
            params["mailto"] = a.mailto
        r = requests.get(API, params=params, timeout=60)
        r.raise_for_status()
        for w in r.json().get("results", []):
            through = None
            if a.through_year is not None:
                through = sum(c["cited_by_count"] for c in w.get("counts_by_year", [])
                              if c["year"] <= a.through_year)
            rows.append({"openalex_id": short_id(w["id"]), "cited_by_count_total": w["cited_by_count"],
                         "citations_through_year": through, "through_year": a.through_year})
        time.sleep(a.sleep)
    out = pd.DataFrame(rows)
    out["retrieved"] = datetime.date.today().isoformat()
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    out.to_csv(a.out, index=False)
    print("%d of %d works retrieved" % (len(out), len(ids)))


if __name__ == "__main__":
    main()
