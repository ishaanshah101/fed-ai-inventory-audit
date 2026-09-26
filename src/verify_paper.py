"""Recompute every number quoted in the paper and the README from the results on
disk, and check the text says what the data says. Exits non-zero on any mismatch."""
import json, os, re, sys, collections
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "src"))
from frame import load

def norm(s): return re.sub(r"\s+", " ", s)
PAPER_RAW = open(os.path.join(BASE, "paper", "paper.md")).read(); PAPER = norm(PAPER_RAW)
README = norm(open(os.path.join(BASE, "README.md")).read()) if os.path.exists(os.path.join(BASE, "README.md")) else ""
A = json.load(open(os.path.join(BASE, "results", "analysis.json")))
S = json.load(open(os.path.join(BASE, "results", "structured.json")))
C = json.load(open(os.path.join(BASE, "results", "calibration.json")))
CP = json.load(open(os.path.join(BASE, "results", "completeness.json")))
V = json.load(open(os.path.join(BASE, "results", "vendors.json")))
CH = json.load(open(os.path.join(BASE, "results", "churn.json")))
rows = load()
fails, checks = [], 0

def ck(label, cond):
    global checks; checks += 1
    if not cond: fails.append(label)
def instr(label, t, where=None):
    ck(f"{label}: {t!r} in " + ("README" if where is README else "paper"), norm(t) in (where if where is not None else PAPER))
def near(label, value, quoted, tol):
    ck(f"{label}: {quoted} vs {value:.4f}", abs(float(quoted) - value) <= tol)
pct = lambda x: 100 * x

# ---------------- inventory basics
ck("3611 rows", len(rows) == 3611 == A["n_rows"]); instr("3611", "3,611 use cases from 41 agencies")
ck("41 agencies", S["n_agencies"] == 41)
ck("1480 live", A["n_live"] == 1480); instr("1480", "1,480 rows the live set")
ck("1040 deployed", S["development_stage"]["Deployed"] == 1040); instr("1040/440", "1,040 are marked Deployed and 440 Pilot")
ck("338 blank stage", S["development_stage"][""] == 338); instr("338", "338 rows, 9.4 percent of the inventory")
near("9.4pct", pct(338 / 3611), "9.4", 0.05)
ck("DOC 223", sum(1 for r in rows if r["agency"] == "DOC") == 223); instr("DOC 223", "published 223 rows containing a name")
ck("DOC 25 problem", sum(1 for r in rows if r["agency"] == "DOC" and r["problem_solved"].strip()) == 25); instr("25 of them", "for 25 of them a one-line problem statement")
ck("TVA 59", sum(1 for r in rows if r["agency"] == "TVA") == 59); ck("ED 56", sum(1 for r in rows if r["agency"] == "ED") == 56)
instr("TVA/ED", "TVA published 59 rows"); instr("ED", "Education published 56")
near("deployed rate", pct(A["rq5"]["deployed_rate"]), "28.8", 0.05); instr("28.8", "28.8 percent of the inventory is deployed")
near("live rate", pct(A["rq5"]["live_rate"]), "41.0", 0.05); instr("41.0", "41.0 percent is live")
ck("commit", "06c7ebe" in PAPER and "4a29d13" in PAPER)
ck("2133", CH["n_2024"] == 2133); instr("2133", "2,133 rows at commit")

# ---------------- RQ1
near("completeness", pct(CP["overall_completeness"]), "91.3", 0.05); instr("91.3", "91.3 percent complete")
ck("cells", CP["filled_cells"] == 38031 and CP["required_cells"] == 41642); instr("cells", "38,031 of 41,642 required cells")
ck("missing 3611", CP["missing_cells"] == 3611); instr("missing", "the other 3,611 cells")
ck("omitted 3033", CP["missing_because_column_omitted"] == 3033); instr("3033", "3,033 of the missing cells, 84 percent")
near("84pct", pct(3033 / 3611), "84", 0.5)
ck("blank 578", CP["missing_because_cell_blank"] == 578); instr("578", "Only 578 are cells left blank")
ck("30 agencies omit", len(CP["agencies_omitting_a_required_column"]) == 30); instr("30 agencies", "Thirty of the 41 agencies omitted at least one required column")

# ---------------- agreement
ag = A["agreement"]
ck("844", A["n_sampled"] == 844); instr("844", "That is 844 rows")
ck("1688", ag["n_judgements"] == 1688); instr("1688", "1,688 judgements")
near("cat agree", pct(ag["fields"]["category"]["observed_agreement"]), "91.7", 0.05); near("cat alpha", ag["fields"]["category"]["alpha"], "0.850", 0.0005)
near("role agree", pct(ag["fields"]["decision_role"]["observed_agreement"]), "88.2", 0.05); near("role alpha", ag["fields"]["decision_role"]["alpha"], "0.777", 0.0005)
near("reading agree", pct(ag["reading_high_impact"]["observed_agreement"]), "93.8", 0.05); near("reading alpha", ag["reading_high_impact"]["alpha"], "0.864", 0.0005)
near("strict agree", pct(ag["reading_principal_only"]["observed_agreement"]), "99.2", 0.05)
rt = json.load(open(os.path.join(BASE, "data/rating/all_ratings.json")))
ck("57 principal", sum(1 for d in rt if d["decision_role"] == "principal") == 57); instr("57", "57 of 1,688 judgements")
ck("52 disputed", ag["reading_high_impact"]["n_disputed"] == 52); instr("52", "The 52 disputed readings")
ck("23 j|none", ag["category_pairs_top"].get("j|none") == 23); instr("23 j-none", "Twenty-three of them are one pass calling a law-enforcement category")
near("quant agree", pct(ag["fields"]["quantified"]["observed_agreement"]), "99.9", 0.05); near("quant alpha", ag["fields"]["quantified"]["alpha"], "0.975", 0.0005)
near("stage agree", pct(ag["fields"]["stage"]["observed_agreement"]), "68.1", 0.05); near("stage alpha", ag["fields"]["stage"]["alpha"], "0.372", 0.0005)
instr("stage alpha quoted", "alpha 0.372"); instr("stage alpha 0.37", "alpha 0.37")

# ---------------- RQ2
b = A["rq2"]["by_self_determination"]; HI = "High-impact"; NOT = "Not High-impact"; PRES = "Presumed High-Impact, but Not High-impact"
ck("HI 250/193/44/13", (b[HI]["n"], b[HI]["read_high"], b[HI]["read_not"], b[HI]["disputed"]) == (250, 193, 44, 13))
instr("HI counts", "both passes read 193 as high-impact and 44 as not, with 13 disputed")
near("HI rate", pct(b[HI]["rate_read_high_agreed"]), "81.4", 0.05); instr("HI wilson", "Wilson 76.0 to 85.9")
ck("HI wilson", abs(pct(b[HI]["wilson"][0]) - 76.0) < 0.06 and abs(pct(b[HI]["wilson"][1]) - 85.9) < 0.06)
ck("NOT 493/47/418/28", (b[NOT]["n"], b[NOT]["read_high"], b[NOT]["read_not"], b[NOT]["disputed"]) == (493, 47, 418, 28))
instr("NOT counts", "both passes read 47 as high-impact, 418 as not, 28 disputed")
near("NOT rate", pct(b[NOT]["rate_read_high_agreed"]), "10.1", 0.05); instr("NOT wilson", "Wilson 7.7 to 13.2, agency bootstrap 6.6 to 14.0")
ck("NOT wilson", abs(pct(b[NOT]["wilson"][0]) - 7.7) < 0.06 and abs(pct(b[NOT]["wilson"][1]) - 13.2) < 0.06)
ab = A["rq2"]["not_hi_read_high_agency_bootstrap"]; ck("NOT agency boot", abs(pct(ab[1]) - 6.6) < 0.06 and abs(pct(ab[2]) - 14.0) < 0.06)
ck("PRES 71/25/35/11", (b[PRES]["n"], b[PRES]["read_high"], b[PRES]["read_not"], b[PRES]["disputed"]) == (71, 25, 35, 11))
instr("PRES counts", "both passes read 25 as high-impact and 35 as not, 11 disputed"); near("PRES rate", pct(b[PRES]["rate_read_high_agreed"]), "41.7", 0.05)
instr("PRES wilson", "Wilson 30.1 to 54.3"); ck("PRES wilson", abs(pct(b[PRES]["wilson"][0]) - 30.1) < 0.06 and abs(pct(b[PRES]["wilson"][1]) - 54.3) < 0.06)
sv = A["rq2"]["survival"]; ck("surv not 34/40", (sv["not"]["n"], sv["not"]["survived"]) == (40, 34)); instr("6 of 40", "I read 6 as high-impact, a survival rate of 85 percent")
ck("surv high 39/40", (sv["high"]["n"], sv["high"]["survived"]) == (40, 39)); instr("39 of 40", "survival on the high side was 39 of 40")
ck("disp 23/30", A["rq2"]["disputed_resolution"]["high"] == 23 and C["c1_disputed_n"] == 30); instr("23 of 30", "23 of 30 disputed rows as high-impact")
near("cal NOT", pct(b[NOT]["calibrated_rate"]), "26.4", 0.05); cb = A["rq2"]["not_hi_calibrated_boot"]
ck("cal boot", abs(pct(cb[1]) - 17.7) < 0.06 and abs(pct(cb[2]) - 36.4) < 0.06); instr("cal boot quoted", "from 17.7 to 36.4")
near("cal HI", pct(b[HI]["calibrated_rate"]), "81.9", 0.05); near("cal PRES", pct(b[PRES]["calibrated_rate"]), "53.6", 0.05)
instr("cal quoted", "stays at 81.9 percent"); instr("cal pres quoted", "rises to 53.6 percent")
pe = A["rq2"]["population_estimate_not_hi_read_high"]; ck("pop est 106/1129", round(pe["estimate"]) == 106 and pe["of"] == 1129 and pe["self_reported_high_live"] == 250)
instr("pop est", "estimated 106 use cases, against the 250 live use cases")
ck("self consistency 8/8", all(v == 8 for v in C["self_consistency"].values()))
p2 = A["rq2"]["prediction2"]; ck("P2 zero 6/88", tuple(p2["zero_n"]) == (6, 88)); ck("P2 top 16/80", tuple(p2["top_n"]) == (16, 80))
instr("P2 counts", "had 6 of 88 sampled not-high-impact rows read as high-impact, 6.8 percent"); instr("P2 top", "had 16 of 80, or 20.0 percent")
ck("P2 agencies", set(p2["zero_self_report_agencies"]) == {"HHS", "DOI", "TREAS"} and set(p2["top_self_report_agencies"]) == {"VA", "DOJ", "DHS"})
ck("P2 diff", abs(pct(p2["diff_boot"][0]) + 13.2) < 0.1 and abs(pct(p2["diff_boot"][1]) + 22.8) < 0.1 and abs(pct(p2["diff_boot"][2]) + 4.2) < 0.1)
instr("P2 diff quoted", "13 points the wrong way, with an interval from 4 to 23")
pa = pe["per_agency"]; ck("VA 8/27", (pa["VA"]["read_high"], pa["VA"]["sampled"]) == (8, 27)); instr("VA 8/27", "8 of 27")
ck("SSA 6/20", (pa["SSA"]["read_high"], pa["SSA"]["sampled"]) == (6, 20)); instr("SSA", "6 of 20"); ck("HHS 1/28", (pa["HHS"]["read_high"], pa["HHS"]["sampled"]) == (1, 28)); instr("HHS", "1 of 28")
va_live = sum(1 for r in rows if r["agency"] == "VA" and r["development_stage"] in ("Deployed", "Pilot"))
near("VA 64pct", pct(pa["VA"]["self_high_live"] / va_live), "64", 0.6); instr("VA 64", "marks 64 percent of its live use cases high-impact")
ssa_live = sum(1 for r in rows if r["agency"] == "SSA" and r["development_stage"] in ("Deployed", "Pilot"))
near("SSA 29pct", pct(pa["SSA"]["self_high_live"] / ssa_live), "29", 0.6)
hhs_live = sum(1 for r in rows if r["agency"] == "HHS" and r["development_stage"] in ("Deployed", "Pilot")); ck("HHS 255 live", hhs_live == 255); instr("HHS 255", "with 255 live use cases and no high-impact ones")
cats = A["rq2"]["categories_among_read_high"]; ck("cats", (cats["f"], cats["j"], cats["m"], cats["a"]) == (97, 89, 38, 17)); instr("cats", "healthcare (f) 97 times, law enforcement (j) 89, benefits and services (m) 38, safety-critical infrastructure (a) 17")
# PATTERN and DOJ examples
pat = [r for r in rows if "PATTERN" in r["use_case_name"] and r["agency"] == "DOJ"]
ck("PATTERN two rows", len(pat) == 2 and {r["is_high_impact"] for r in pat} == {HI, NOT})
ck("PATTERN quotes", all(norm(q) in norm(" ".join(r["problem_solved"] for r in pat)) for q in ["uses pre-defined rules to score an inmate's recidivism risk level", "to predict the risk of recidivism for incarcerated adults"]))
for nm in ["Cloudflare Turnstile", "Building Automation Systems", "Chatbot to Answer Internal Employee Policy Queries"]:
    ck(f"DOJ HI {nm}", any(r["agency"] == "DOJ" and r["use_case_name"].strip() == nm and r["is_high_impact"] == HI for r in rows))
pres = [r for r in rows if r["is_high_impact"] == PRES]; ck("110 overrides", len(pres) == 110)
just = collections.Counter(norm(r["HI_justification"].strip())[:120] for r in pres)
ck("47 template", sum(v for v in just.values() if v >= 3) == 47); instr("47 template", "47 share a justification text used three or more times")
ck("DOJ 32 same", just.most_common(1)[0][1] == 32 and sum(1 for r in pres if r["agency"] == "DOJ") == 32); instr("DOJ 32", "Thirty-two of Justice's 314 rows invoke the override, and all 32 carry the same justification sentence")
ck("DOJ 314", sum(1 for r in rows if r["agency"] == "DOJ") == 314)

# ---------------- RQ3
r3 = A["rq3"]; ck("305 cands", r3["candidates"] == 305); instr("305", "flagged 305 of the 1,480 live rows")
ck("37 q", r3["quantified"] == 37); near("2.5", pct(r3["rate"]), "2.5", 0.05); instr("q wilson", "Wilson 1.8 to 3.4")
ck("q wilson", abs(pct(r3["wilson"][0]) - 1.8) < 0.06 and abs(pct(r3["wilson"][1]) - 3.4) < 0.06)
ck("37/15/9/0", (r3["metric_named"], r3["baseline_given"], r3["evaluation_described"], r3["uncertainty_given"]) == (37, 15, 9, 0))
instr("37 15 9", "All 37 name the metric, 15 give a baseline, 9 say what data")
ck("9 checkable", r3["checkable"] == 9); near("0.61", pct(r3["checkable_rate"]), "0.61", 0.005); instr("chk wilson", "Wilson 0.32 to 1.15")
ck("chk wilson", abs(pct(r3["checkable_wilson"][0]) - 0.32) < 0.006 and abs(pct(r3["checkable_wilson"][1]) - 1.15) < 0.006)
pv = r3["passes_vs_reviewer"]; ck("185 in sample", C["c2_in_sample"] == 185); instr("185", "on the 185 candidates that fell inside the rated sample")
ck("20 vs 19", pv["passes_both_q"] == 20 and pv["reviewer_q_in_sample"] == 19 and pv["agree_both"] == 19 and pv["missed_by_both"] == [])
ck("overcall NASA QUAnT", rows[pv["overcalled_by_both"][0]]["agency"] == "NASA" and "QUAnT" in rows[pv["overcalled_by_both"][0]]["use_case_name"])
ck("v1 208", len(json.load(open(os.path.join(BASE, "results/numeral_screen_v1.json")))) == 208)
# quoted checkable examples exist verbatim in the inventory text
def in_inv(frag): return any(norm(frag) in norm(" ".join(r[f] for f in ("problem_solved","benefits","system_outputs","data_description"))) for r in rows)
for frag in ["a statistically significant 21% increase in the odds of adenoma detection", "from over a month to less than 4 days",
             "Reduces time spent searching course materials by over 80%", "Detects cooling towers approximately 600 times faster than manual searches",
             "2 million actions in the 2024 calendar year", "processed over 25,000 cases", "processes >15,000 emails annually"]:
    ck(f"verbatim in inventory {frag[:30]}", in_inv(frag))
    if "%" in frag or "less than 4 days" in frag or "600 times" in frag: ck(f"verbatim in paper {frag[:30]}", norm(frag) in PAPER)
ck("PFAS 78 vs 65", in_inv("validation accuracy of 78%") and in_inv("accuracies of 65%"))

# ---------------- RQ4
r4 = A["rq4"]; ck("227", r4["n_deployed_high_impact"] == 227); instr("227", "the 227 deployed use cases")
comp = [v["complete"] for v in r4["per_practice"].values()]; ck("complete 36-45", min(comp) == 36 and max(comp) == 45); instr("36 45", "between 36 and 45 rows each")
ip = [v["in_progress"] for v in r4["per_practice"].values()]; ck("inprog 81-90", min(ip) == 81 and max(ip) == 90); instr("81 90", "In-progress is reported on 81 to 90")
bl = [v["blank"] for v in r4["per_practice"].values()]; ck("blank 101-102", min(bl) == 101 and max(bl) == 102)
ck("33 all six", r4["all_six_complete"] == 33); ck("78 none", r4["none_complete_reported"] == 78); ck("101 all blank", r4["all_blank"] == 101)
instr("33/78/101", "33 report all six minimum practices complete, 78 report none complete, and 101 report nothing at all")
ba = r4["by_agency"]; ck("VA 94 blank", ba["VA"]["n"] == 94 and ba["VA"]["all_blank"] == 94 and ba["VA"]["columns_omitted"])
ck("DHS 26/38", ba["DHS"]["n"] == 38 and ba["DHS"]["all_six"] == 26); ck("SSA 7", ba["SSA"]["all_six"] == 7); ck("DOJ 73/0", ba["DOJ"]["n"] == 73 and ba["DOJ"]["all_six"] == 0)
instr("DHS SSA", "26 of them at Homeland Security and 7 at SSA"); instr("DOJ 73", "73 of those are Justice's entire deployed high-impact inventory")
ck("other 7", ba["NCUA"]["all_blank"] + ba["FDIC"]["all_blank"] + ba["NASA"]["all_blank"] == 7); instr("other 7", "account for the other 7")
ck("DOJ 78 check", sum(1 for r in rows if r["agency"] == "DOJ" and r["development_stage"] == "Deployed" and r["is_high_impact"] == HI) == 73)

# ---------------- RQ5
ck("171 absent", CH["agency_absent_in_2025"] == 171); instr("171", "171 belong to nine agencies absent")
ck("nine agencies", len(CH["agencies_2024_not_in_2025"]) == 9 and {"OPM", "USAID", "CFPB"} <= set(CH["agencies_2024_not_in_2025"]))
ck("1195/767", CH["matched"] == 1195 and CH["unmatched"] == 767); instr("1195 767", "1,195 have an exact name match in 2025 in any stage, and 767, 39.1 percent, do not")
ck("1962", CH["matched"] + CH["unmatched"] == 1962); instr("1962", "Of the 1,962 that could be matched")
near("39.1", pct(CH["unmatched_rate_of_matchable"]), "39.1", 0.05)
rv = A["rq5"]["review"]; ck("review 27/5/9/19", (rv["rename"], rv["retired_in_2024"], rv["no_successor_cots_likely"], rv["no_successor"]) == (27, 5, 9, 19))
instr("review", "Twenty-seven are renames"); instr("nineteen", "Nineteen have no plausible successor")
near("12", pct(A["rq5"]["silent_disappearance_upper_excl_cots"]), "12", 0.5); near("18", pct(A["rq5"]["silent_disappearance_upper_incl_cots"]), "18", 0.5)
instr("12/18", "at most 12 percent excluding the commercial products and 18 percent including them")
pc = A["partC"]; ck("stage surv 33/150", pc["pass_in_use_survival"]["in_use->in_use"] == 33 and pc["pass_in_use_survival"]["in_use->unclear"] == 114 and sum(v for k, v in pc["pass_in_use_survival"].items() if k.startswith("in_use->")) == 150)
instr("33 of 150", "agreed on 33 of 150 judgements, reading 114 as `unclear`")

# ---------------- RQ6
ck("552/387/505/36", (V["n_vendor_purchased"], V["n_contract_and_inhouse"], V["n_inhouse"], V["n_contracting_blank"]) == (552, 387, 505, 36))
instr("contracting", "552 are marked as purchased from a vendor, 387 as built with both contracting and in-house resources, 505 as built in-house, and 36 leave the field blank")
ck("939/625", V["n_vendor_involved"] == 939 and V["n_named_vendor_rows"] == 625); instr("939 625", "Of the 939 with vendor involvement, 625 name one")
ck("378/375", V["n_distinct_strings"] == 378 and V["n_distinct_parents"] == 375); instr("378 375", "The 378 distinct strings normalise to 375 parents")
top = dict(V["top"]); ck("MS 110", top["Microsoft"] == 110); near("17.6", pct(V["microsoft_share"]), "17.6", 0.05); instr("MS", "Microsoft is named on 110 of the 625, 17.6 percent")
ck("top others", top["Google"] == 29 and top["Deloitte"] == 27 and top["OpenAI"] == 27 and top["Palantir"] == 23 and top["Amazon"] == 17 and top["Thomson Reuters"] == 17)
near("34.6", pct(V["share_top5"]), "34.6", 0.05); near("44.8", pct(V["share_top10"]), "44.8", 0.05); instr("top5/10", "top five vendors hold 34.6 percent of the named rows and the top ten 44.8 percent")
mb = V["microsoft_by_agency"]; ck("DOE 50/127", (mb["DOE"]["microsoft"], mb["DOE"]["n"]) == (50, 127)); ck("HHS 8/137", (mb["HHS"]["microsoft"], mb["HHS"]["n"]) == (8, 137))
instr("DOE HHS MS", "50 of Energy's 127 vendor-named rows and 8 of HHS's 137")

# ---------------- predictions and figures
P = A["predictions"]; ck("P1 false", P["1_not_hi_read_high_ge_15pct"]["held"] is False); ck("P2 false", P["2_zero_reporters_higher"]["held"] is False)
ck("P3 true", P["3_quantified_lt_10_checkable_lt_2"]["held"] is True); ck("P4 true", P["4_unmatched_ge_20pct"]["held_as_stated"] is True)
ck("P5 false", P["5_top5_gt_half"]["held"] is False); ck("P6 untestable", P["6_deployed_read_not_in_use_ge_10pct"]["testable"] is False)
instr("2 held 3 failed", "Two preregistered predictions held, three failed and one proved untestable")
for f in ["fig1_reading_vs_determination.png", "fig2_by_agency.png", "fig3_min_practices.png", "fig4_evidence_funnel.png", "fig5_vendors.png"]:
    ck(f"fig {f}", os.path.exists(os.path.join(BASE, "figures", f)) and f in PAPER_RAW)
# external facts quoted
instr("M-25-21 date", "3 April 2025"); instr("GAO 1200", "about 1,200 use cases"); instr("Bean", "445 language-model benchmarks with 29 expert reviewers")
instr("inventory due", "22 December 2025"); instr("annual-report comparison", "2.7 percent of capability claims"); instr("0.17", "0.17 percent of AI sentences")

# ---------------- README
if README:
    for t in ["3,611", "1,480", "227", "33 report all six", "37 state", "9 say what", "10 percent", "26 percent", "42 percent", "47 of those 110", "PATTERN"]:
        instr(f"README {t}", t, README)
    m = re.search(r"\*\*(\d+) checks", README)
    ck("README advertises the right check count", bool(m) and int(m.group(1)) == checks + 1)

print(f"{checks} checks run, {len(fails)} failed")
for f in fails: print("  FAIL:", f)
sys.exit(1 if fails else 0)
