"""Download public ICLR records from OpenReview: submissions, reviewer ratings, decisions.

  pip install openreview-py
  python data_build/fetch_openreview.py --years 2018 2019 2020 --out data/raw

Writes, for each year, openreview_submissions_<year>.csv (one row per submission,
with the decision) and openreview_ratings_<year>.csv (one row per human review).
ICLR 2018-2020 use OpenReview API v1; later years use API v2 (accepted papers only).
"""
import argparse
import os
import re

import pandas as pd


def value(x):
    """API v2 wraps fields as {"value": ...}; API v1 does not."""
    return x.get("value") if isinstance(x, dict) else x


def leading_int(x):
    """Ratings appear as '6: Marginally above acceptance threshold' or as integers."""
    x = value(x)
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return int(x)
    m = re.match(r"\s*(\d+)", str(x))
    return int(m.group(1)) if m else None


def classify_decision(text):
    """Map decision text to (accepted, tier). Workshop invitations (ICLR 2018) count as
    not accepted to the main conference."""
    s = (value(text) or "").lower()
    if not s:
        return None, None
    if "reject" in s:
        return 0, "reject"
    if "workshop" in s:
        return 0, "workshop"
    if "oral" in s or "talk" in s:        # ICLR 2020 labels orals "Accept (Talk)"
        return 1, "oral"
    for tier in ["spotlight", "poster"]:
        if tier in s:
            return 1, tier
    if "accept" in s:
        return 1, "poster"
    return None, s


def fetch_v1(year):
    import openreview
    client = openreview.Client(baseurl="https://api.openreview.net")
    notes = client.get_all_notes(invitation="ICLR.cc/%d/Conference/-/Blind_Submission" % year,
                                 details="directReplies")
    subs, ratings = [], []
    for n in notes:
        decision = meta = None
        for r in n.details.get("directReplies", []):
            inv, content = r.get("invitation", ""), r.get("content", {})
            if inv.endswith("Official_Review"):
                ratings.append({"openreview_id": n.forum, "year": year, "review_id": r["id"],
                                "rating": leading_int(content.get("rating")),
                                "confidence": leading_int(content.get("confidence"))})
            elif inv.endswith("Decision") or inv.endswith("Acceptance_Decision"):
                decision = content.get("decision")
            elif inv.endswith("Meta_Review"):
                meta = content.get("recommendation")
        raw = decision if decision is not None else meta
        accepted, tier = classify_decision(raw)
        subs.append({"openreview_id": n.forum, "year": year, "title": n.content.get("title"),
                     "decision_raw": raw, "accepted": accepted, "decision_tier": tier})
    return subs, ratings


def fetch_v2(year):
    import openreview
    client = openreview.api.OpenReviewClient(baseurl="https://api2.openreview.net")
    notes = client.get_all_notes(content={"venueid": "ICLR.cc/%d/Conference" % year}, details="replies")
    subs, ratings = [], []
    for n in notes:
        venue = value(n.content.get("venue"))
        accepted, tier = classify_decision(venue)
        subs.append({"openreview_id": n.forum, "year": year, "title": value(n.content.get("title")),
                     "decision_raw": venue, "accepted": accepted, "decision_tier": tier})
        for r in n.details.get("replies", []):
            if any(i.endswith("Official_Review") for i in r.get("invitations", [])):
                content = r.get("content", {})
                ratings.append({"openreview_id": n.forum, "year": year, "review_id": r["id"],
                                "rating": leading_int(content.get("rating")),
                                "confidence": leading_int(content.get("confidence"))})
    return subs, ratings


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--years", type=int, nargs="+", default=[2018, 2019, 2020])
    ap.add_argument("--out", default="data/raw")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for year in a.years:
        subs, ratings = (fetch_v2 if year >= 2024 else fetch_v1)(year)
        pd.DataFrame(subs).to_csv(os.path.join(a.out, "openreview_submissions_%d.csv" % year), index=False)
        pd.DataFrame(ratings).to_csv(os.path.join(a.out, "openreview_ratings_%d.csv" % year), index=False)
        print("%d: %d submissions, %d reviews" % (year, len(subs), len(ratings)))


if __name__ == "__main__":
    main()
