"""AI review committee: focus notes -> persona reviews -> area-chair synthesis -> decision stage.

Reference implementation of the pilot's committee architecture. Models are
called through any OpenAI-compatible endpoint (vLLM, OpenRouter, ...), so the
open-weight models used in the pilot can be swapped for others.

  # Inspect the flow without a model (placeholder outputs):
  python pipeline/committee.py --paper examples/paper.txt --dry-run

  # Run against an endpoint configured in configs/pipeline.yaml:
  export LLM_API_KEY=...
  python pipeline/committee.py --paper paper.txt --decision-head deepseek --out review.json

Input: a plain-text (or Markdown) paper, or a JSON file with "title",
"abstract", and "text". Output: JSON with focus notes, persona reviews,
committee scores, the synthesized review, and the decision.
"""
import argparse
import json
import os
import re

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMPTS = os.path.join(ROOT, "prompts")
FOCUS = ["intro", "method", "contribution"]
SCORES = ["rating", "confidence", "soundness", "presentation", "contribution"]
REVIEW_FORMAT = (
    'Return one JSON object with keys "rating" (1-10), "confidence" (1-5), '
    '"soundness" (1-4), "presentation" (1-4), "contribution" (1-4), "recommendation", '
    '"summary", "strengths", "weaknesses", and "questions".')


def read_prompt(name):
    with open(os.path.join(PROMPTS, name + ".txt")) as fh:
        return fh.read().strip()


class LLM:
    """Chat model behind an OpenAI-compatible endpoint."""

    def __init__(self, model, base_url, api_key_env, temperature=0.0, max_tokens=1500):
        from openai import OpenAI
        self.client = OpenAI(base_url=base_url, api_key=os.environ.get(api_key_env, "EMPTY"))
        self.model, self.temperature, self.max_tokens = model, temperature, max_tokens

    def __call__(self, system, user):
        resp = self.client.chat.completions.create(
            model=self.model, temperature=self.temperature, max_tokens=self.max_tokens,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}])
        return resp.choices[0].message.content


class MockLLM:
    """Placeholder outputs for --dry-run; they carry no judgment about the paper."""

    def __call__(self, system, user):
        if "decision head" in system:
            return json.dumps({"decision": "reject", "p_accept": 0.5, "margin": 0.0,
                               "top_accept_reasons": ["[dry run]"], "top_reject_reasons": ["[dry run]"],
                               "evidence_used": ["[dry run]"]})
        if "rating" in system and "JSON" in system:
            return json.dumps({"rating": 5, "confidence": 3, "soundness": 3, "presentation": 3,
                               "contribution": 2, "recommendation": "[dry run]", "summary": "[dry run]",
                               "strengths": "[dry run]", "weaknesses": "[dry run]", "questions": "[dry run]"})
        return "[dry run] strengths / weaknesses / questions"


def extract_json(text):
    """Parse the first JSON object in a model response."""
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        return json.loads(text[start:end + 1])
    except ValueError:
        return None


def load_paper(path):
    if path.endswith(".json"):
        with open(path) as fh:
            return json.load(fh)
    with open(path) as fh:
        text = fh.read()
    return {"title": text.strip().splitlines()[0][:200], "abstract": "", "text": text}


def split_sections(text):
    """Split a paper into the three focus segments by common section headings.
    Falls back to fixed shares of the text when headings are not found."""
    heading = re.compile(r"^\s*(?:\d+(?:\.\d+)*\s+)?([A-Z][A-Za-z ]{2,40})\s*$", re.M)
    marks = [(m.start(), m.group(1).lower()) for m in heading.finditer(text)]
    text = re.split(r"\n\s*references\s*\n", text, flags=re.I)[0]   # drop references

    def find(*names):
        for pos, name in marks:
            if any(n in name for n in names):
                return pos
        return None

    n = len(text)
    method_at = find("method", "approach", "model", "framework") or int(0.25 * n)
    results_at = find("experiment", "result", "evaluation") or int(0.65 * n)
    concl_at = find("conclusion", "discussion") or int(0.9 * n)
    return {"intro": text[:method_at],
            "method": text[method_at:results_at],
            "contribution": text[:min(method_at, 4000)] + "\n...\n" + text[concl_at:]}


def inventory(text):
    """Deterministic structural inventory passed to the decision stage."""
    return {"characters": len(text),
            "figures": len(set(re.findall(r"\bFig(?:ure)?\.?\s*(\d+)", text))),
            "tables": len(set(re.findall(r"\bTable\s*(\d+)", text))),
            "equations": len(re.findall(r"\(\d+\)\s*$", text, re.M)),
            "mentions_ablation": bool(re.search(r"ablation", text, re.I)),
            "mentions_code_release": bool(re.search(r"github|code (is|will be) (available|released)", text, re.I))}


def run_committee(paper, cfg, committee_llm, decision_llm, preamble=""):
    sections = split_sections(paper["text"])
    notes = {s: committee_llm(read_prompt("focus_" + s), sections[s][:cfg.get("section_chars", 12000)])
             for s in FOCUS}
    notes_text = "\n\n".join("## Notes on %s\n%s" % (s, notes[s]) for s in FOCUS)

    reviews = {}
    for persona in cfg["personas"]:
        system = "\n\n".join([read_prompt("persona_system"), read_prompt("persona_" + persona), REVIEW_FORMAT])
        raw = committee_llm(system, notes_text)
        reviews[persona] = extract_json(raw) or {"unparsed": raw}

    weights = cfg.get("persona_weights", {})
    scores = {}
    for key in SCORES:
        vals = [(float(r[key]), float(weights.get(p, 1))) for p, r in reviews.items()
                if isinstance(r.get(key), (int, float))]
        scores[key] = sum(v * w for v, w in vals) / sum(w for _, w in vals) if vals else None

    text_parts = {p: {k: r.get(k) for k in ["summary", "strengths", "weaknesses", "questions"]}
                  for p, r in reviews.items()}
    synthesis = committee_llm(read_prompt("committee_synthesis"), json.dumps(text_parts, indent=1))

    ratings = [r["rating"] for r in reviews.values() if isinstance(r.get("rating"), (int, float))]
    packet = {
        "title": paper.get("title"), "abstract": paper.get("abstract"),
        "excerpt": paper["text"][:cfg.get("excerpt_chars", 6000)],
        "inventory": inventory(paper["text"]),
        "committee_review": synthesis,
        "persona_scores": {p: {k: r.get(k) for k in SCORES} for p, r in reviews.items()},
        "disagreement": {"rating_range": (max(ratings) - min(ratings)) if ratings else None},
    }
    decision_raw = decision_llm((preamble + "\n\n" if preamble else "") + read_prompt("decision_head"),
                                json.dumps(packet, indent=1))
    return {"focus_notes": notes, "persona_reviews": reviews, "committee_scores": scores,
            "committee_review": synthesis, "decision": extract_json(decision_raw) or {"unparsed": decision_raw}}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--paper", required=True, help="paper as .txt/.md, or .json with title/abstract/text")
    ap.add_argument("--config", default=os.path.join(ROOT, "configs", "pipeline.yaml"))
    ap.add_argument("--decision-head", default="deepseek", help="key under decision_heads in the config")
    ap.add_argument("--out", help="write the full committee output as JSON")
    ap.add_argument("--dry-run", action="store_true", help="use placeholder outputs instead of a model")
    a = ap.parse_args()

    with open(a.config) as fh:
        cfg = yaml.safe_load(fh)
    head = cfg["decision_heads"][a.decision_head]
    preamble = ""
    if head.get("preamble_file"):
        with open(os.path.join(ROOT, head["preamble_file"])) as fh:
            preamble = fh.read().strip()
    if a.dry_run:
        committee_llm = decision_llm = MockLLM()
    else:
        ep = cfg["endpoint"]
        committee_llm = LLM(cfg["committee"]["model"], ep["base_url"], ep["api_key_env"],
                            cfg["committee"].get("temperature", 0.0), cfg["committee"].get("max_tokens", 1500))
        decision_llm = LLM(head["model"], ep["base_url"], ep["api_key_env"],
                           head.get("temperature", 0.0), head.get("max_tokens", 800))

    result = run_committee(load_paper(a.paper), cfg, committee_llm, decision_llm, preamble)
    out = json.dumps(result, indent=2)
    if a.out:
        with open(a.out, "w") as fh:
            fh.write(out)
    print(json.dumps({"committee_scores": result["committee_scores"],
                      "decision": result["decision"]}, indent=2))


if __name__ == "__main__":
    main()
