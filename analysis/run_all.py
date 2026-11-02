"""Run every analysis script and collect the tables in results/SUMMARY.md."""
import argparse
import glob
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPTS = ["01_agreement.py", "02_review_similarity.py", "03_score_dispersion.py",
           "04_acceptance_effect.py", "05_band_comparison.py"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default=os.path.join(ROOT, "data"))
    parser.add_argument("--out", default=os.path.join(ROOT, "results"))
    args = parser.parse_args()
    failed = []
    for script in SCRIPTS:
        print("=" * 70 + "\n" + script)
        code = subprocess.call([sys.executable, os.path.join(HERE, script),
                                "--data", args.data, "--out", args.out], cwd=HERE)
        if code != 0:
            failed.append(script)
    with open(os.path.join(args.out, "SUMMARY.md"), "w") as out:
        out.write("# Results\n\n")
        for md in sorted(glob.glob(os.path.join(args.out, "0*.md"))):
            out.write(open(md).read() + "\n")
    if failed:
        sys.exit("Failed: " + ", ".join(failed))


if __name__ == "__main__":
    main()
