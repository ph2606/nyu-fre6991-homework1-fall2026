"""Regenerate calculations and compile the LaTeX PDF, with no shell expansion."""

import argparse
from pathlib import Path
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--skip-analysis", action="store_true", help="Compile existing tables and figures")
args = parser.parse_args()
if not args.skip_analysis:
    subprocess.run([sys.executable, str(root / "scripts" / "analyze.py")], cwd=root, check=True)
compiler = shutil.which("pdflatex")
if compiler is None:
    raise SystemExit("Install a TeX distribution (MiKTeX or TeX Live) with pdflatex.")
for run in range(2):
    process = subprocess.run(
        [compiler, "-interaction=nonstopmode", "-halt-on-error", "-file-line-error", "homework1_report.tex"],
        cwd=root / "report", capture_output=True, text=True, errors="replace",
    )
    if process.returncode:
        print(process.stdout[-14000:])
        print(process.stderr[-3000:])
        raise SystemExit(process.returncode)
print(f"Built {root / 'report' / 'homework1_report.pdf'}")
