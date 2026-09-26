"""Figures. Palette #2a78d6, #eb6834, #8a6fbf carried over from the companion audits."""
from __future__ import annotations
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS, FIGS = os.path.join(BASE, "results"), os.path.join(BASE, "figures")
os.makedirs(FIGS, exist_ok=True)
C1, C2, C3 = "#2a78d6", "#eb6834", "#8a6fbf"
INK, MUTED, GRID, SURF = "#1c1c1c", "#5a5a5a", "#dcdcd8", "#fcfcfb"
plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF, "font.size": 9,
    "axes.edgecolor": GRID, "axes.labelcolor": INK, "text.color": INK, "xtick.color": MUTED,
    "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.6, "figure.dpi": 200, "savefig.bbox": "tight"})
HI = "High-impact"; NOT = "Not High-impact"; PRES = "Presumed High-Impact, but Not High-impact"


def fig1(res):
    """Blinded reading against the agency's own determination."""
    b = res["rq2"]["by_self_determination"]
    order = [(HI, "agency says\nhigh-impact"), (PRES, "agency says presumed,\nbut not high-impact"), (NOT, "agency says\nnot high-impact")]
    fig, ax = plt.subplots(figsize=(7.2, 2.9))
    ys = np.arange(len(order))[::-1]
    for y, (k, lab) in zip(ys, order):
        v = b[k]; n = v["n"]
        parts = [(v["read_high"] / n, C1, "read as high-impact"), (v["disputed"] / n, MUTED, "raters disagreed"),
                 (v["read_not"] / n, C2, "read as not high-impact")]
        left = 0
        for w, col, _ in parts:
            ax.barh([y], [w], left=left, color=col, height=0.6, edgecolor=SURF, linewidth=1.5)
            if w > 0.07:
                ax.text(left + w / 2, y, f"{w:.0%}", ha="center", va="center", color="white", fontweight="bold", fontsize=9)
            left += w
        ax.text(1.01, y, f"n = {n}", va="center", fontsize=8.5, color=MUTED)
    ax.set_yticks(ys); ax.set_yticklabels([l for _, l in order], fontsize=8.5)
    ax.set_xlim(0, 1); ax.xaxis.set_major_formatter(PercentFormatter(1.0)); ax.grid(axis="y", visible=False)
    ax.set_xlabel("share of sampled live use cases")
    h = [plt.Rectangle((0, 0), 1, 1, color=c) for c in (C1, MUTED, C2)]
    ax.legend(h, ["read as high-impact", "raters disagreed", "read as not high-impact"], loc="upper center",
              bbox_to_anchor=(0.5, -0.32), ncol=3, frameon=False, fontsize=8.5)
    ax.set_title("What a blinded reader says, against what the agency said", loc="left", fontweight="bold", pad=10)
    fig.savefig(os.path.join(FIGS, "fig1_reading_vs_determination.png")); plt.close(fig)


def fig2(res):
    """Per agency: how often not-high-impact rows read as high-impact, against how much the agency self-reports."""
    pa = res["rq2"]["population_estimate_not_hi_read_high"]["per_agency"]
    live_hi = {a: v["self_high_live"] for a, v in pa.items()}
    pts = [(a, v) for a, v in pa.items() if v["sampled"] >= 20]
    fig, ax = plt.subplots(figsize=(6.6, 4.0))
    for a, v in pts:
        tot_live = v["live_not_hi"] + v["self_high_live"]
        x = v["self_high_live"] / tot_live if tot_live else 0
        y = v["rate"]
        lo, hi = wilson_ci(v["read_high"], v["sampled"])
        ax.plot([x, x], [lo, hi], color=GRID, lw=1.2, zorder=1)
        ax.scatter([x], [y], s=40 + 1.2 * tot_live, color=C1, alpha=0.75, edgecolor=SURF, zorder=3)
        offs = {"HHS": (0.012, -0.03), "DOI": (-0.03, 0.03), "DOE": (0.02, 0.012), "DOL": (0.02, -0.028),
                "TREAS": (0.012, 0.012), "NASA": (0.015, -0.012), "SEC": (-0.045, -0.005), "FRB": (0.012, -0.022),
                "USDA": (0.02, 0.0)}
        if a in offs or tot_live >= 60 or y > 0.15:
            dx, dy = offs.get(a, (0.012, 0.012))
            ax.text(x + dx, y + dy, a, fontsize=8, color=INK)
    ax.set_xlabel("share of the agency's live use cases it marked high-impact")
    ax.set_ylabel("share of its not-high-impact rows\nthat read as high-impact, blind")
    ax.xaxis.set_major_formatter(PercentFormatter(1.0, decimals=0)); ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    ax.set_xlim(-0.03, 0.72); ax.set_ylim(-0.02, 0.52)
    ax.set_title("Agencies that flag more also leave more unflagged", loc="left", fontweight="bold", pad=10)
    ax.text(0.99, 0.02, "bubble area = live use cases; bars = 95% Wilson", transform=ax.transAxes, ha="right", fontsize=7.5, color=MUTED)
    fig.savefig(os.path.join(FIGS, "fig2_by_agency.png")); plt.close(fig)


def wilson_ci(k, n, z=1.959963984540054):
    if n == 0: return (0, 0)
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d
    h = z / d * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)); return (max(0, c - h), min(1, c + h))


def fig3(res):
    """Minimum practices on deployed high-impact use cases."""
    pp = res["rq4"]["per_practice"]; n = res["rq4"]["n_deployed_high_impact"]
    names = {"hi_testing_conducted": "pre-deployment testing", "hi_assessment_completed": "AI impact assessment",
             "hi_independent_review": "independent review", "hi_ongoing_monitoring": "ongoing monitoring",
             "hi_training_established": "operator training", "hi_failsafe_presence": "fail-safe"}
    order = list(names)
    fig, ax = plt.subplots(figsize=(7.2, 3.0))
    ys = np.arange(len(order))[::-1]
    for y, f in zip(ys, order):
        v = pp[f]; other = n - v["complete"] - v["in_progress"] - v["blank"]
        parts = [(v["complete"], C1), (v["in_progress"], C3), (other, MUTED), (v["blank"], C2)]
        left = 0
        for w, col in parts:
            ax.barh([y], [w], left=left, color=col, height=0.62, edgecolor=SURF, linewidth=1.5)
            if w / n > 0.08:
                ax.text(left + w / 2, y, f"{w}", ha="center", va="center", color="white", fontweight="bold", fontsize=9)
            left += w
    ax.set_yticks(ys); ax.set_yticklabels([names[f] for f in order], fontsize=8.5)
    ax.set_xlim(0, n); ax.set_xlabel(f"the {n} deployed use cases agencies marked high-impact"); ax.grid(axis="y", visible=False)
    h = [plt.Rectangle((0, 0), 1, 1, color=c) for c in (C1, C3, MUTED, C2)]
    ax.legend(h, ["reported complete", "reported in progress", "waived or other", "not published"], loc="upper center",
              bbox_to_anchor=(0.5, -0.3), ncol=4, frameon=False, fontsize=8.5)
    ax.set_title("M-25-21 minimum practices, as reported for deployed high-impact AI", loc="left", fontweight="bold", pad=10)
    fig.savefig(os.path.join(FIGS, "fig3_min_practices.png")); plt.close(fig)


def fig4(res):
    """Evidence funnel over live use cases."""
    r = res["rq3"]
    stages = [("live use cases", r["n_live"]), ("carry a number of any kind", r["candidates"]),
              ("give a performance figure", r["quantified"]), ("name the metric", r["metric_named"]),
              ("say what it was measured over", r["evaluation_described"]),
              ("state a baseline", r["baseline_given"]), ("state an uncertainty", r["uncertainty_given"])]
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    ys = np.arange(len(stages))[::-1]
    cols = [MUTED, MUTED, C1, C3, C3, C3, C2]
    for y, (lab, c), col in zip(ys, stages, cols):
        if c > 0:
            ax.barh([y], [c], color=col, height=0.62)
            ax.text(c * 1.3, y, f"{c}", va="center", fontsize=9, fontweight="bold", color=INK)
        else:
            ax.text(0.28, y, "0", va="center", fontsize=9, fontweight="bold", color=C2)
    ax.set_yticks(ys); ax.set_yticklabels([s[0] for s in stages], fontsize=8.5)
    ax.set_xscale("symlog", linthresh=1); ax.set_xlim(0, r["n_live"] * 2.6)
    ax.set_xticks([1, 10, 100, r["n_live"]]); ax.set_xticklabels(["1", "10", "100", str(r["n_live"])])
    ax.set_xlabel("number of use cases (log scale)"); ax.grid(axis="y", visible=False)
    ax.set_title("Every filter a use case has to pass to carry checkable evidence", loc="left", fontweight="bold", pad=10)
    fig.savefig(os.path.join(FIGS, "fig4_evidence_funnel.png")); plt.close(fig)


def fig5(res):
    """Vendor concentration."""
    top = res["rq6"]["top"][:12]; n = res["rq6"]["n_named_vendor_rows"]
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    ys = np.arange(len(top))[::-1]
    ax.barh(ys, [v / n for _, v in top], color=[C1] + [C3] * (len(top) - 1), height=0.66)
    for y, (k, v) in zip(ys, top):
        ax.text(v / n + 0.004, y, f"{v}", va="center", fontsize=8.5, color=INK)
    ax.set_yticks(ys); ax.set_yticklabels([k for k, _ in top], fontsize=8.5)
    ax.xaxis.set_major_formatter(PercentFormatter(1.0, decimals=0)); ax.grid(axis="y", visible=False)
    ax.set_xlabel(f"share of the {n} live use cases that name a vendor")
    ax.set_title("Who the inventory says is selling AI to the government", loc="left", fontweight="bold", pad=10)
    fig.savefig(os.path.join(FIGS, "fig5_vendors.png")); plt.close(fig)


if __name__ == "__main__":
    res = json.load(open(os.path.join(RESULTS, "analysis.json")))
    fig1(res); fig2(res); fig3(res); fig4(res); fig5(res)
    for f in sorted(os.listdir(FIGS)): print(f, os.path.getsize(os.path.join(FIGS, f)), "bytes")
