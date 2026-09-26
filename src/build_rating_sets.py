"""Draw the rated sample from the live set, redact agency identifiers, shuffle,
and assign every row to exactly two of six raters.

Sampling rule is the one fixed in docs/PREREGISTRATION.md section 4.
"""
import json, os, re, random, collections, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frame import load

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "data", "rating")
os.makedirs(OUT, exist_ok=True)
SEED = 20260926
CAP_NOT_HI = 30
N_RATERS = 6
SHOW = ["use_case_name", "topic_area", "classification", "problem_solved",
        "benefits", "system_outputs", "data_description"]

rows = load()
live = [r for r in rows if r["development_stage"] in ("Deployed", "Pilot")
        and (r["problem_solved"].strip() or r["system_outputs"].strip())]
rng = random.Random(SEED)

take = []
for r in live:
    if r["is_high_impact"] in ("High-impact", "Presumed High-Impact, but Not High-impact", ""):
        take.append(r)
by_ag = collections.defaultdict(list)
for r in live:
    if r["is_high_impact"] == "Not High-impact":
        by_ag[r["agency"]].append(r)
for a in sorted(by_ag):
    pool = sorted(by_ag[a], key=lambda r: r["_row"])
    take += pool if len(pool) <= CAP_NOT_HI else rng.sample(pool, CAP_NOT_HI)
take.sort(key=lambda r: r["_row"])

# ---- redaction: agency names, abbreviations, bureau names and their acronyms ----
tokens = set()
for r in rows:
    for f in ("agency", "agency_name", "agency_bureau"):
        v = r[f].strip()
        if not v:
            continue
        tokens.add(v)
        for part in re.split(r"[/,;()]| - | – ", v):
            part = part.strip()
            if len(part) >= 4:
                tokens.add(part)
            # parenthesised acronyms and all-caps words of 2+ letters
        for acr in re.findall(r"\(([A-Z][A-Za-z&]{1,9})\)", v):
            tokens.add(acr)
        for acr in re.findall(r"\b[A-Z]{2,6}\b", v):
            tokens.add(acr)
STOP = {"Office", "Department", "Bureau", "Agency", "Administration", "Division", "Service",
        "Services", "Center", "National", "Federal", "United States", "U.S.", "Program",
        "Commission", "Board", "Board of", "Information", "Technology", "Research", "Health",
        "Human", "Management", "Security", "Data", "Policy", "Operations", "Officer",
        "Chief", "Enterprise", "Digital", "Support", "Business", "Financial", "General",
        "Public", "Affairs", "Analytics", "Innovation", "Systems", "Science", "Energy",
        "Labor", "Education", "Transportation", "Interior", "Commerce", "Justice",
        "Treasury", "State", "Defense", "Agriculture", "Veterans", "Housing", "Urban",
        "Development", "Environmental", "Protection", "Social", "Personnel", "Trade",
        "Small", "Election", "Assistance", "Homeland", "Nuclear", "Regulatory", "Arts",
        "Humanities", "Archives", "Records", "Credit", "Union", "Deposit", "Insurance",
        "Reserve", "Communications", "Maritime", "Futures", "Trading", "Special",
        "Counsel", "Pension", "Benefit", "Guaranty", "Corporation", "Foundation", "Fund",
        "AI", "IT", "US", "USA", "OF", "AND", "THE", "OCIO", "CIO", "OIG", "HQ", "OA",
        # content words that also occur inside bureau names; redacting them would
        # damage the description more than it protects the blind
        "Generation", "Technical", "Network", "Supply", "Chain", "Supply Chain",
        "Operations", "OCR", "GIS", "CRM", "Security", "Cyber", "Cybersecurity",
        "Compliance", "Enforcement", "Investigations", "Inspections", "Grants",
        "Procurement", "Acquisition", "Budget", "Finance", "Communications",
        "Engineering", "Laboratory", "Laboratories", "Statistics", "Survey",
        "Quality", "Safety", "Standards", "Learning", "Training", "Legal", "Privacy",
        "Planning", "Strategy", "Performance", "Emergency", "Response", "Recovery",
        "Field", "Regional", "Region", "Headquarters", "Mission", "Programs"}
tokens = {t for t in tokens if t not in STOP and len(t) >= 2}
# longest first so that a full name is replaced before its parts
tokens = sorted(tokens, key=len, reverse=True)
tok_re = re.compile("|".join(r"(?<![A-Za-z])" + re.escape(t) + r"(?![A-Za-z])" for t in tokens))


def redact(s):
    return tok_re.sub("[agency]", s or "")



if __name__ == "__main__":
    items = []
    for r in take:
        it = {"row": r["_row"], "id": r["id"]}
        for f in SHOW:
            it[f] = redact(r[f].strip())
        items.append(it)
    rng2 = random.Random(SEED + 1)
    rng2.shuffle(items)
    for i, it in enumerate(items):
        it["rid"] = i + 1
    key = [{"rid": it["rid"], "row": it["row"], "id": it["id"]} for it in items]
    for it in items:
        del it["row"]; del it["id"]

    json.dump(items, open(os.path.join(OUT, "items.json"), "w"), indent=1)
    json.dump(key, open(os.path.join(OUT, "items_key.json"), "w"), indent=1)
    json.dump({"seed": SEED, "cap_not_high_impact_per_agency": CAP_NOT_HI,
               "n_live_with_text": len(live), "n_sampled": len(items),
               "redaction_tokens": len(tokens)}, open(os.path.join(OUT, "manifest.json"), "w"), indent=2)

    # assignment: each item to two raters
    for k in range(N_RATERS):
        mine = [{"rid": it["rid"], **{f: it[f] for f in SHOW}} for i, it in enumerate(items)
                if k in (i % N_RATERS, (i - 1) % N_RATERS)]
        json.dump(mine, open(os.path.join(OUT, f"rater_{k}_items.json"), "w"), indent=1)
        print(f"rater {k}: {len(mine)} items")

    by_hi = collections.Counter(rows[k["row"]]["is_high_impact"] for k in key)
    print(f"\nlive with text {len(live)}; sampled {len(items)}: {dict(by_hi)}")
    n_red = sum(1 for it in items if "[agency]" in " ".join(it[f] for f in SHOW))
    print(f"rows with a redaction: {n_red}; redaction tokens: {len(tokens)}")
    print("example redacted:", next(it["use_case_name"] for it in items if "[agency]" in it["use_case_name"]))
