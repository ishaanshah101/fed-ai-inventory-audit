"""RQ6: who is selling AI to the federal government, according to the inventory.

vendor_name is free text. Each string is split on separators and each part is
mapped to a parent vendor through the fixed table below; anything not in the
table is kept as its own cleaned string. A row that names several vendors
counts once for each. Every mapping is inspectable in results/vendors.json.
"""
import json, os, re, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frame import load
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PARENT = {  # lower-case substring -> parent
    "microsoft": "Microsoft", "azure": "Microsoft", "copilot": "Microsoft", "github": "Microsoft",
    "openai": "OpenAI", "open ai": "OpenAI", "chatgpt": "OpenAI",
    "google": "Google", "gemini": "Google", "vertex": "Google",
    "amazon": "Amazon", "aws": "Amazon", "bedrock": "Amazon",
    "anthropic": "Anthropic", "claude": "Anthropic",
    "palantir": "Palantir", "deloitte": "Deloitte", "thomson reuters": "Thomson Reuters", "westlaw": "Thomson Reuters",
    "clear": "Thomson Reuters", "lexisnexis": "LexisNexis", "lexis nexis": "LexisNexis", "relx": "LexisNexis",
    "servicenow": "ServiceNow", "leidos": "Leidos", "ibm": "IBM", "accenture": "Accenture", "guidehouse": "Guidehouse",
    "booz allen": "Booz Allen Hamilton", "saic": "SAIC", "gdit": "GDIT", "general dynamics": "GDIT",
    "nec": "NEC", "adobe": "Adobe", "axon": "Axon", "veritone": "Veritone", "sas": "SAS", "esri": "Esri",
    "salesforce": "Salesforce", "databricks": "Databricks", "chainalysis": "Chainalysis", "clearview": "Clearview AI",
    "dataminr": "Dataminr", "medallia": "Medallia", "motorola": "Motorola Solutions", "opentext": "OpenText",
    "boston dynamics": "Boston Dynamics", "informatica": "Informatica", "techsmith": "TechSmith", "camtasia": "TechSmith",
    "meltwater": "Meltwater", "exiger": "Exiger", "altana": "Altana", "trm labs": "TRM Labs", "aretec": "Aretec",
    "lexical intelligence": "Lexical Intelligence", "nvidia": "NVIDIA", "oracle": "Oracle", "splunk": "Splunk",
    "cisco": "Cisco", "crowdstrike": "CrowdStrike", "elastic": "Elastic", "snowflake": "Snowflake",
    "ge healthcare": "GE HealthCare", "siemens": "Siemens Healthineers", "philips": "Philips", "hologic": "Hologic",
    "aidoc": "Aidoc", "icad": "iCAD", "terarecon": "TeraRecon", "brainlab": "Brainlab", "uipath": "UiPath",
    "xai": "xAI", "perplexity": "Perplexity", "meta": "Meta", "hugging face": "Hugging Face", "wellsaid": "WellSaid Labs",
    "eleven labs": "ElevenLabs", "elevenlabs": "ElevenLabs", "zoom": "Zoom", "otter": "Otter.ai",
}
NOT_A_VENDOR = re.compile(r"^(not available|n/?a|none|unknown|tbd|in-?house.*|internal.*|open.?source.*|contractor.*|various.*|multiple.*|ai (service|model) provider|law enforcement sensitive.*|les|federal shared service.*|government.*|cots.*|inc\.?|llc\.?|corp\.?|corporation|ltd\.?|co\.?|small business)$", re.I)

def parents(s):
    s = re.sub(r"PIID:?\s*\S+", " ", s)
    parts = re.split(r"[;,/&+\n]|\band\b|\bwith\b", s)
    out = set()
    for p in parts:
        p = p.strip(" .()")
        if not p or NOT_A_VENDOR.match(p):
            continue
        low = p.lower(); hit = None
        for k, v in PARENT.items():
            if re.search(r"(?<![a-z])" + re.escape(k) + r"(?![a-z])", low):
                hit = v; break
        out.add(hit or p)
    return out

rows = load()
live = [r for r in rows if r["development_stage"] in ("Deployed", "Pilot")]
vend = [r for r in live if r["contracting_usage"] in ("Vendor Purchased", "Contracting and In House")]
named = [r for r in vend if r["vendor_name"].strip()]
counts = collections.Counter(); mapping = {}
rows_with_parent = 0
for r in named:
    ps = parents(r["vendor_name"])
    mapping[r["vendor_name"].strip()] = sorted(ps)
    if ps: rows_with_parent += 1
    for p in ps: counts[p] += 1
top = counts.most_common(25)
n_named = rows_with_parent
res = {"n_live": len(live), "n_vendor_involved": len(vend),
       "n_vendor_purchased": sum(1 for r in live if r["contracting_usage"] == "Vendor Purchased"),
       "n_contract_and_inhouse": sum(1 for r in live if r["contracting_usage"] == "Contracting and In House"),
       "n_inhouse": sum(1 for r in live if r["contracting_usage"] == "In-house Development"),
       "n_contracting_blank": sum(1 for r in live if not r["contracting_usage"].strip()),
       "n_named_vendor_rows": rows_with_parent, "n_distinct_strings": len(mapping),
       "n_distinct_parents": len(counts),
       "top": top, "share_top5": sum(v for _, v in top[:5]) / n_named,
       "share_top10": sum(v for _, v in top[:10]) / n_named,
       "microsoft_share": counts["Microsoft"] / n_named,
       "mapping": mapping}
# by agency: top vendor per big agency
res["microsoft_by_agency"] = {}
for a in sorted({r["agency"] for r in named}):
    sub = [r for r in named if r["agency"] == a]
    if len(sub) >= 15:
        res["microsoft_by_agency"][a] = {"n": len(sub), "microsoft": sum(1 for r in sub if "Microsoft" in parents(r["vendor_name"]))}
json.dump(res, open(os.path.join(BASE, "results", "vendors.json"), "w"), indent=2)
print(f"live {len(live)}: vendor-purchased {res['n_vendor_purchased']}, contract+inhouse {res['n_contract_and_inhouse']}, in-house {res['n_inhouse']}, blank {res['n_contracting_blank']}")
print(f"rows naming a vendor: {rows_with_parent} ({len(mapping)} distinct strings -> {len(counts)} parents)")
for k, v in top[:20]: print(f"  {v:4d} {k}")
print(f"top5 share {res['share_top5']:.3f}  top10 share {res['share_top10']:.3f}  Microsoft {res['microsoft_share']:.3f}")
print("microsoft by agency:", res["microsoft_by_agency"])
