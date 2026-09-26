"""Keyword screen for the fifteen M-25-21 Section 6 presumption categories.

The patterns below were written from the memo's own wording and frozen before the
screen was run (see docs/PREREGISTRATION.md section 5). A match makes a row a
candidate for that category; it is not a verdict. The blinded reading of sampled
rows measures how often a candidate is actually read as high-impact.

Run over every row's free text: use_case_name, problem_solved, benefits,
system_outputs, data_description.
"""
import re, json, os, collections

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CATEGORIES = {
    "a_safety_critical_infrastructure": r"critical infrastructure|life safety|fire (?:safety|detection|alarm)|food safety|traffic (?:control|signal)|air traffic|emergency (?:services|response|dispatch)|911|dam safety|grid (?:control|operation)",
    "b_physical_movement": r"\brobot|robotic|autonomous (?:vehicle|drone|aircraft|craft|system)|unmanned|drone|self-driving|industrial equipment|vehicle control",
    "c_kinetic_attack_defense": r"kinetic|weapon(?:s)? system|active defense|munition|targeting",
    "d_hazardous_materials": r"hazardous (?:chemical|material|waste|substance)|biological agent|toxic|radiological|nuclear material|pathogen",
    "e_engineering_safety": r"structural (?:integrity|safety|failure)|bridge (?:inspection|safety)|pipeline (?:integrity|safety)|aircraft (?:safety|inspection|certification)|(?:dam|levee) (?:inspection|safety)|building safety",
    "f_healthcare": r"\bpatient|diagnos|clinical (?:decision|risk|care|outcome)|treatment (?:plan|recommendation|decision)|medical device|triage|sepsis|suicide risk|prognos|radiolog|pathology|screening for|risk (?:score|stratification) for (?:patients|veterans)|medication|prescri",
    "g_facility_access_security": r"facility (?:access|security)|access control|physical security|badge|perimeter|screening of (?:visitors|persons)|entry (?:screening|control)",
    "h_sanctions_trade_export": r"sanction|export control|trade restriction|denied part|entity list|shipment screening|import (?:enforcement|screening)|cargo (?:screening|inspection|targeting)|customs",
    "i_protected_speech": r"content moderation|remov(?:e|al) of (?:posts|content)|protected speech|takedown|flag(?:ging)? (?:posts|comments|content)",
    "j_law_enforcement": r"law enforcement|criminal|suspect|forensic|recidivism|sentencing|parole|probation|bail|pretrial|detention|surveillance|license plate|facial recognition|face (?:matching|recognition)|biometric|fingerprint|iris|gait|social media monitoring|crime (?:forecast|prediction|analysis)|investigat|offender|inmate|prisoner|threat (?:assessment|detection)|weapon(?:s)? detection|gunshot|contraband",
    "k_immigration": r"immigra|asylum|visa|refugee|naturalization|border (?:crossing|screening|security)|travel(?:er)? (?:screening|vetting|approval)|passport|foreign national|citizenship",
    "l_biometric_one_to_many": r"one-to-many|facial recognition|face (?:matching|recognition)|biometric (?:identification|matching)",
    "m_benefits_services": r"benefit(?:s)? (?:eligib|determin|adjudic|claim|application|process|fraud)|eligibility|adjudicat|claims? (?:processing|decision|adjudication|determination)|entitlement|disability (?:claim|rating|determination)|loan (?:application|approval|underwriting|eligibility)|public housing|housing assistance|fraud|improper payment|identity (?:proofing|verification)|applicant|grant (?:application|review|award)|tax (?:return|refund|credit)|social security|medicaid|medicare|veterans? benefit|unemployment (?:insurance|benefit|claim)|SNAP|food stamp|penalt",
    "n_federal_employment": r"hiring|recruit|applicant (?:screening|ranking|scoring)|resume|résumé|candidate (?:screening|ranking|matching)|promotion|performance (?:management|review|rating|appraisal)|disciplinary|termination of (?:employment|employees)|reasonable accommodation|workforce (?:assignment|allocation)|personnel (?:decision|action)|employee (?:evaluation|assessment)|job (?:applicant|candidate|posting)",
    "o_translation": r"translat|interpret(?:ation|er) service|multilingual|language access",
}
TEXT_FIELDS = ["use_case_name", "problem_solved", "benefits", "system_outputs", "data_description"]
_C = {k: re.compile(v, re.I) for k, v in CATEGORIES.items()}


def screen_row(row):
    text = " \n ".join(row.get(f, "") or "" for f in TEXT_FIELDS)
    hits = {}
    for k, rx in _C.items():
        ms = rx.findall(text)
        if ms:
            hits[k] = sorted({m if isinstance(m, str) else m[0] for m in ms})[:5]
    return hits


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from frame import load
    rows = load()
    out = []
    for r in rows:
        h = screen_row(r)
        out.append({"row": r["_row"], "id": r["id"], "agency": r["agency"],
                    "stage": r["development_stage"], "hi": r["is_high_impact"],
                    "categories": h})
    json.dump(out, open(os.path.join(BASE, "results", "presumption_screen.json"), "w"), indent=0)
    n_any = sum(1 for o in out if o["categories"])
    print(f"{n_any} of {len(out)} rows match at least one presumption category")
    cc = collections.Counter(k for o in out for k in o["categories"])
    for k, v in sorted(cc.items()):
        print(f"  {k:36s} {v}")
    live = [o for o in out if o["stage"] in ("Deployed", "Pilot")]
    print(f"\nlive rows: {len(live)}; matching: {sum(1 for o in live if o['categories'])}")
    print("live matching rows by self-determination:",
          dict(collections.Counter(o["hi"] for o in live if o["categories"])))
