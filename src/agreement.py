"""Inter-pass agreement on every rubric field, and the agreed/disputed split
on the derived high-impact reading."""
import json, collections, os
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(BASE, "data", "rating"); OUT = os.path.join(BASE, "results")
rows = json.load(open(os.path.join(R, "all_ratings.json")))
by = collections.defaultdict(list)
for d in rows: by[d["rid"]].append(d)
rids = sorted(by)


def alpha_nominal(field):
    """Krippendorff's alpha, nominal, exactly two coders per unit, no missing."""
    Do = sum(0.0 if by[r][0][field] == by[r][1][field] else 1.0 for r in rids) / len(rids)
    marg = collections.Counter(d[field] for d in rows); N = sum(marg.values())
    De = 1 - sum(c * (c - 1) for c in marg.values()) / (N * (N - 1))
    return 1 - Do / De if De > 0 else float("nan"), 1 - Do


def reading(d):
    return d["category"] != "none" and d["decision_role"] != "none"


def reading_strict(d):
    return d["category"] != "none" and d["decision_role"] == "principal"


rep = {"n_items": len(rids), "n_judgements": len(rows), "fields": {}}
for f in ["category", "decision_role", "stage", "quantified", "metric_named",
          "evaluation_described", "baseline_given", "uncertainty_given"]:
    a, po = alpha_nominal(f)
    rep["fields"][f] = {"alpha": a, "observed_agreement": po}
# derived
for name, fn in [("reading_high_impact", reading), ("reading_principal_only", reading_strict)]:
    agree = [r for r in rids if fn(by[r][0]) == fn(by[r][1])]
    both_t = sum(1 for r in agree if fn(by[r][0]))
    Do = 1 - len(agree) / len(rids)
    vals = [fn(d) for d in rows]; nt = sum(vals); N = len(vals)
    De = 1 - (nt * (nt - 1) + (N - nt) * (N - nt - 1)) / (N * (N - 1))
    rep[name] = {"observed_agreement": len(agree) / len(rids), "alpha": 1 - Do / De,
                 "n_agreed": len(agree), "n_disputed": len(rids) - len(agree),
                 "n_agreed_true": both_t, "n_agreed_false": len(agree) - both_t,
                 "psa_true": 2 * both_t / nt if nt else float("nan")}
# category confusion on items where both gave a non-none category
conf = collections.Counter(tuple(sorted((by[r][0]["category"], by[r][1]["category"]))) for r in rids)
rep["category_pairs_top"] = {f"{a}|{b}": c for (a, b), c in conf.most_common(15)}
split = {"agreed": {str(r): reading(by[r][0]) for r in rids if reading(by[r][0]) == reading(by[r][1])},
         "disputed": [r for r in rids if reading(by[r][0]) != reading(by[r][1])]}
json.dump(rep, open(os.path.join(OUT, "agreement.json"), "w"), indent=2)
json.dump(split, open(os.path.join(OUT, "reading_split.json"), "w"), indent=1)
print(f"items {len(rids)}  judgements {len(rows)}")
for f, v in rep["fields"].items():
    print(f"  {f:22s} agree {v['observed_agreement']:.3f}  alpha {v['alpha']:.3f}")
for k in ("reading_high_impact", "reading_principal_only"):
    v = rep[k]
    print(f"{k}: agree {v['observed_agreement']:.3f} alpha {v['alpha']:.3f}  agreed-true {v['n_agreed_true']} "
          f"agreed-false {v['n_agreed_false']} disputed {v['n_disputed']}  PSA(true) {v['psa_true']:.3f}")
print("top category pairs:", rep["category_pairs_top"])
