"""Scan the repository for material that could identify the authors.

Checks generic patterns (email addresses, home-directory paths, cloud-sync
folders, API keys) plus any project-specific terms listed one per line in a
patterns file kept OUTSIDE the repository:

  python tools/anonymity_scan.py --patterns ../path/to/patterns.txt
"""
import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {".git", "results", "pdfs", "__pycache__", ".pytest_cache"}
GENERIC = {
    "email address": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    "home directory path": r"(/Users/|/home/|C:\\Users\\)[A-Za-z0-9._-]+",
    "cloud-sync folder": r"(?i)\b(dropbox|google drive|onedrive|icloud)\b",
    "API key": r"\b(sk-[A-Za-z0-9]{20,}|hf_[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})\b",
    "private key": r"BEGIN [A-Z ]*PRIVATE KEY",
}
ALLOWED = [r"noreply@", r"example\.(com|org)"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--patterns", help="file with extra terms to flag (names, institutions, ...)")
    ap.add_argument("--max-mb", type=float, default=50.0, help="flag files larger than this")
    a = ap.parse_args()

    patterns = dict(GENERIC)
    if a.patterns:
        with open(a.patterns) as fh:
            for term in (t.strip() for t in fh):
                if term and not term.startswith("#"):
                    patterns["term '%s'" % term] = r"(?i)" + re.escape(term)

    findings = []
    if os.path.isdir(os.path.join(ROOT, ".git")):
        findings.append(("<repo>", 0, "git history present: commit metadata may identify authors"))
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, ROOT)
            if os.path.getsize(path) > a.max_mb * 1e6:
                findings.append((rel, 0, "file larger than %.0f MB" % a.max_mb))
            if rel == os.path.join("tools", "anonymity_scan.py"):
                continue
            try:
                with open(path, encoding="utf-8") as fh:
                    lines = fh.readlines()
            except (UnicodeDecodeError, OSError):
                continue
            for i, line in enumerate(lines, 1):
                for label, pat in patterns.items():
                    for m in re.finditer(pat, line):
                        if not any(re.search(ok, m.group(0)) for ok in ALLOWED):
                            findings.append((rel, i, "%s: %s" % (label, m.group(0))))
    for rel, line, msg in findings:
        print("%s:%s  %s" % (rel, line, msg))
    print("\n%d finding(s)." % len(findings))
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
