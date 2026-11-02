"""Download submission PDFs from OpenReview for papers listed in the data.

PDFs are not redistributed in this repository. This script fetches them from
OpenReview by ID, for example to rerun the committee on a sample:

  python data_build/download_openreview_pdfs.py --limit 20 --out pdfs/
"""
import argparse
import os
import time

import pandas as pd
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=os.path.join(ROOT, "data", "project_outputs_iclr2018_2020.csv"))
    ap.add_argument("--out", default=os.path.join(ROOT, "pdfs"))
    ap.add_argument("--limit", type=int, default=None, help="download only the first N papers")
    ap.add_argument("--sleep", type=float, default=1.0, help="seconds between requests")
    a = ap.parse_args()

    ids = pd.read_csv(a.data)["openreview_id"].dropna().unique().tolist()[:a.limit]
    os.makedirs(a.out, exist_ok=True)
    for i, pid in enumerate(ids, 1):
        path = os.path.join(a.out, pid + ".pdf")
        if os.path.exists(path):
            continue
        r = requests.get("https://openreview.net/pdf", params={"id": pid}, timeout=60)
        if r.ok and r.content[:4] == b"%PDF":
            with open(path, "wb") as fh:
                fh.write(r.content)
        else:
            print("skipped %s (HTTP %s)" % (pid, r.status_code))
        if i % 50 == 0:
            print("%d / %d" % (i, len(ids)))
        time.sleep(a.sleep)


if __name__ == "__main__":
    main()
