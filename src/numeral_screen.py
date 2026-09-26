"""Exhaustive numeral screen over the live set. A numeric performance figure is
necessary for `quantified`, so the candidate set bounds RQ3 from above. Dates,
years, section numbers and identifiers will match too; that is the point, the
reviewer removes them by reading.

Version 1 (frozen before running) matched percentages, multiples, currency,
magnitude words attached to a digit, and integers of two or more digits. After
unblinding, four rows the automated passes had marked quantified were found
outside the candidate set: "from about one week to one day", "by a third",
"by 2/3", and "within 3-meters". Version 2 adds spelled-out numbers and
fractions, slash fractions, and a single digit attached to a unit. Both versions
are kept; results/numeral_screen.json is v2 and results/numeral_screen_v1.json
is the original. Recorded as Amendment 2 in docs/PREREGISTRATION.md."""
SCREEN_VERSION = 2
import re, json, os, sys
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NUM = re.compile(
    r"(\d+(?:\.\d+)?\s*%|\d+(?:\.\d+)?\s*(?:percent|percentage points?|bps|basis points?)"
    r"|\b\d+(?:\.\d+)?\s*(?:x|times|fold)\b"
    r"|[$€£]\s?\d|\b\d+(?:\.\d+)?\s*(?:million|billion|thousand|hours?|minutes?|seconds?|days?|weeks?|months?)\b"
    r"|\b\d{2,}(?:,\d{3})*(?:\.\d+)?\b)", re.I)
NUM_V2_EXTRA = re.compile(
    r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|twenty|thirty|forty|fifty|hundred|thousand|million|billion)\b"
    r"(?:\s+(?:percent|times|fold|x|hours?|minutes?|seconds?|days?|weeks?|months?|years?|meters?|metres?|miles?|feet|foot))?"
    r"|\b(?:half|a third|two.thirds|one.third|a quarter|three.quarters|double|doubled|twice|triple|tripled|tenfold|fourfold|fivefold|threefold|twofold)\b"
    r"|\b\d\s*/\s*\d\b"
    r"|\b\d(?:\.\d+)?\s*-?\s*(?:x|times|fold|%|percent|hours?|minutes?|seconds?|days?|weeks?|months?|years?|meters?|metres?|miles?|feet|foot|mm|cm|km|fte)\b", re.I)
FIELDS = ["problem_solved", "benefits", "system_outputs", "data_description"]

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from frame import load
    rows = [r for r in load() if r["development_stage"] in ("Deployed", "Pilot")]
    out = []
    for r in rows:
        text = " \n ".join(r[f] or "" for f in FIELDS)
        m1 = NUM.findall(text)
        m2 = NUM_V2_EXTRA.findall(text)
        if m1 or m2:
            out.append({"row": r["_row"], "id": r["id"],
                        "numerals": sorted(set(x.strip() for x in m1 + m2))[:10],
                        "v1": bool(m1), "v2_only": bool(m2) and not m1})
    v1 = [o for o in out if o["v1"]]
    json.dump(v1, open(os.path.join(BASE, "results", "numeral_screen_v1.json"), "w"), indent=0)
    json.dump(out, open(os.path.join(BASE, "results", "numeral_screen.json"), "w"), indent=0)
    print(f"v1: {len(v1)} of {len(rows)} live rows; v2: {len(out)} "
          f"({sum(1 for o in out if o['v2_only'])} added by the extension)")
