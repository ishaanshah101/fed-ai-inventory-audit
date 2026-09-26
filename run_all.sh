#!/usr/bin/env bash
# Reproduce every result in the paper from the committed data.
# The six rating passes are model calls and are not scripted; their published
# output is in data/rating/rater_*.jsonl. Everything after that is deterministic.
set -euo pipefail
cd "$(dirname "$0")/src"
python3 stats.py                  # self-checks first
python3 frame.py                  # 1. load inventory, provenance, structured tabulations
python3 build_rating_sets.py      # 2. sample, redact, assign (seeded; regenerates identical files)
python3 validate_ratings.py       # 3. schema-check the 1,688 judgements
python3 agreement.py              # 4. agreement, agreed/disputed split
python3 numeral_screen.py         # 5. numeral screen, v1 and v2
python3 build_calibration.py      # 6. blinded calibration materials
python3 presumption_screen.py     # 7. presumption keyword screen
python3 calibrate.py              # 8. unblind, survival rates
python3 completeness.py           # 9. RQ1
python3 churn.py                  # 10. RQ5 matching (review verdicts are in results/churn_review.json)
python3 vendors.py                # 11. RQ6
python3 analyze.py                # 12. every number in the paper
python3 figures.py                # 13. figures
python3 verify_paper.py           # 14. recompute every quoted number, fail loudly
cd ../paper && pandoc paper.md -o fed-ai-inventory-audit.pdf --pdf-engine=xelatex \
  -V mainfont="DejaVu Serif" -V monofont="DejaVu Sans Mono"
echo "paper/fed-ai-inventory-audit.pdf"
