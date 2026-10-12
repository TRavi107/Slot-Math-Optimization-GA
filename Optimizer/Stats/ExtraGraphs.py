"""
Extra README charts (15-17), drawn from files the other analysis scripts write:

    15_noise_vs_error.png                  simulator noise next to the final errors
    16_paired_wins_vs_hill_climbing.png    same seed, same parents: GA vs hill climbing
    17_overview_best_mutation.png          all three experiments, each method at its best count

Reads (run Stats.py, MutationsStats.py and NoiseStudy.py first):
    Results/stats/stats_runs.csv, stats_pairwise.csv                 base game
    Results/stats/FreeGame/stats_runs.csv, stats_pairwise.csv        free game, Both mode
    Results/stats/FreeGame_fixedbase/stats_runs.csv                  free game, fixed base
    Results/stats/mutation_base|mutation_free|mutation_free_fixedbase/best_mutation.csv
    NoiseStudy/noise_runs.csv

Usage (from the project root):
    python Optimizer/Stats/ExtraGraphs.py [--out Results/Graphs]
"""
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm, LinearSegmentedColormap

import argparse
import os

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--stats", default="Results/stats", help="folder Stats.py wrote to")
ap.add_argument("--noise", default="NoiseStudy/noise_runs.csv")
ap.add_argument("--out", default="Results/Graphs")
args = ap.parse_args()
S, OUT = args.stats, args.out
os.makedirs(OUT, exist_ok=True)
RUNS = {"base": f"{S}/stats_runs.csv", "free": f"{S}/FreeGame/stats_runs.csv",
        "fixed": f"{S}/FreeGame_fixedbase/stats_runs.csv"}
BEST = {"best_mut_base": f"{S}/mutation_base/best_mutation.csv",
        "best_mut_free": f"{S}/mutation_free/best_mutation.csv",
        "best_mut_fixed": f"{S}/mutation_free_fixedbase/best_mutation.csv"}

INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#8a8984", "#e6e5e1"
STRAT = {"Steady-state": "#2a78d6", "Elitist generational": "#eb6834",
         "Generational": "#1baf7a", "Hill climbing": "#6250d6",
         "Simulated annealing": "#7a5c00"}

plt.rcParams.update({
    "font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2, "axes.titlecolor": INK,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "figure.facecolor": "white", "axes.facecolor": "white",
})


def family(method):
    return method.split(" + ")[0]


def load_runs(name):
    d = pd.read_csv(RUNS[name])
    return d[d.method != "Random search"].copy()


base, free, fixed = load_runs("base"), load_runs("free"), load_runs("fixed")
noise = pd.read_csv(args.noise)
noise = noise[noise.combination != "RandomSearch_Baseline"]

# simulator SD of one fitness evaluation at 10M spins, per stage (median over reelsets)
sd10 = noise.groupby(["mode", "mutation", "combination"]).fitness.std().groupby("mode").median()
# noise floor of the 100M re-check used in the stats: 2.77 x SD / sqrt(10)
floor100 = {"BaseGame": pd.read_csv(f"{S}/stats_pairwise.csv").noise_floor.iloc[0],
            "FreeGame": pd.read_csv(f"{S}/FreeGame/stats_pairwise.csv").noise_floor.iloc[0]}
floor10 = {m: 2.77 * sd10[m] for m in sd10.index}

ORDER = ["Steady-state + Tournament", "Steady-state + SUS", "Steady-state + Roulette",
         "Elitist generational + Tournament", "Elitist generational + SUS",
         "Elitist generational + Roulette", "Generational + Tournament",
         "Generational + SUS", "Generational + Roulette",
         "Hill climbing", "Simulated annealing"]


# ---------------------------------------------------------------------------
# 15: how big is simulator noise next to the errors and the seed-to-seed spread
# ---------------------------------------------------------------------------
def chart_noise():
    fig, axes = plt.subplots(1, 2, figsize=(13, 6.2), sharey=True)
    for ax, (df, mode, title) in zip(axes, [(base, "BaseGame", "Base game"),
                                            (free, "FreeGame", "Free game (Both mode)")]):
        ys = np.arange(len(ORDER))[::-1]
        for y, m in zip(ys, ORDER):
            v = df.loc[df.method == m, "reeval_error"].values
            q1, med, q3 = np.percentile(v, [25, 50, 75])
            lo, hi = np.percentile(v, [5, 95])
            c = STRAT[family(m)]
            ax.plot([lo, hi], [y, y], color=c, lw=1.2, alpha=0.5, solid_capstyle="round")
            ax.plot([q1, q3], [y, y], color=c, lw=6, alpha=0.85, solid_capstyle="butt")
            ax.plot(med, y, "o", ms=8, mfc="white", mec=c, mew=2, zorder=3)
        ax.axvspan(1e-3, floor100[mode], color="#d55181", alpha=0.10, lw=0)
        ax.axvline(floor100[mode], color="#b33b6b", lw=1.5, ls="-")
        ax.axvline(floor10[mode], color="#b33b6b", lw=1.5, ls="--")
        ax.set_xscale("log")
        lo = 0.01 if mode == "BaseGame" else 0.05
        ax.set_xlim(lo, 4 if mode == "BaseGame" else 4)
        ax.set_yticks(ys)
        ax.set_yticklabels(ORDER)
        ax.set_title(title, loc="left", fontsize=11.5, fontweight="bold")
        ax.set_xlabel("Final error (re-checked, 100M spins, log scale)   lower = better")
        ax.grid(axis="y", visible=False)
        ax.text(floor100[mode], -1.15, f"tests' floor {floor100[mode]:.3f} ",
                color="#b33b6b", fontsize=8.5, va="bottom", ha="right")
        ax.text(floor10[mode], -1.15, f" one 10M eval {floor10[mode]:.3f}",
                color="#b33b6b", fontsize=8.5, va="bottom", ha="left")
        iqr = df.groupby(["mutation", "method"]).reeval_error.apply(
            lambda x: x.quantile(.75) - x.quantile(.25)).median()
        ax.text(0.99, 0.985,
                f"Typical seed-to-seed spread (IQR): {iqr:.3f}\n"
                f"= {iqr / floor100[mode]:.0f}x the re-check noise floor",
                transform=ax.transAxes, ha="right", va="top", fontsize=9, color=INK2,
                bbox=dict(boxstyle="round,pad=0.4", fc="white", ec=GRID))
        ax.set_ylim(-1.2, len(ORDER) + 0.9)
    fig.suptitle("How big is simulator noise compared with the results?   "
                 "(all 30 seeds x every mutation count per method)",
                 x=0.01, ha="left", fontsize=12.5, fontweight="bold", color=INK)
    fig.text(0.01, 0.945, va="top", s=
             "Dot = median, thick bar = middle 50% of runs, thin line = 5th-95th percentile.\n"
             "Solid line: smallest gap the statistical tests treat as real (conservative).  "
             "Dashed: smallest gap one 10M-spin evaluation inside a run can resolve (95%).",
             fontsize=9, color=INK2)
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    fig.savefig(f"{OUT}/15_noise_vs_error.png", dpi=170)
    plt.close(fig)


# ---------------------------------------------------------------------------
# 16: same seed, same parents, same mutation: how often does each GA beat hill climbing
# ---------------------------------------------------------------------------
def chart_paired():
    ga = ORDER[:9]
    stages = [(base, "Base game"), (free, "Free game (Both mode)"),
              (fixed, "Free game (one fixed base reelset)")]
    cmap = LinearSegmentedColormap.from_list("div", ["#d95926", "#efeeea", "#2a78d6"])
    norm = TwoSlopeNorm(vmin=0, vcenter=50, vmax=100)
    fig, axes = plt.subplots(1, 3, figsize=(15, 5.6),
                             gridspec_kw={"width_ratios": [4, 4, 3]})
    for k, (ax, (df, title)) in enumerate(zip(axes, stages)):
        muts = sorted(df.mutation.unique())
        p = df.pivot_table(index=["seed", "mutation"], columns="method",
                           values="reeval_error").reset_index()
        M = np.zeros((len(ga), len(muts)))
        for j, m in enumerate(muts):
            s = p[p.mutation == m]
            for i, g in enumerate(ga):
                M[i, j] = (s[g] < s["Hill climbing"]).mean() * 100
        ax.imshow(M, cmap=cmap, norm=norm, aspect="auto")
        for i in range(len(ga)):
            for j in range(len(muts)):
                wins = round(M[i, j] * 30 / 100)
                ax.text(j, i, f"{wins}/30", ha="center", va="center", fontsize=9,
                        color=INK if 25 < M[i, j] < 75 else "white")
        ax.set_xticks(range(len(muts)))
        ax.set_xticklabels([f"m={m}" for m in muts])
        ax.set_yticks(range(len(ga)))
        ax.set_yticklabels(ga if k == 0 else [])
        ax.grid(False)
        for s in ax.spines.values():
            s.set_visible(False)
        ax.set_title(title, loc="left", fontsize=11, fontweight="bold")
        ax.set_xlabel("Mutation count (stops changed per child, of 250)")
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    cax = fig.add_axes([0.925, 0.12, 0.012, 0.72])
    cb = fig.colorbar(sm, cax=cax)
    cb.set_label("Seeds where the GA ended lower than hill climbing (%)")
    cb.outline.set_visible(False)
    fig.suptitle("Head to head: on how many of the 30 seeds did each GA beat hill climbing?",
                 x=0.01, ha="left", fontsize=12.5, fontweight="bold", color=INK)
    fig.text(0.01, 0.905,
             "Each seed is a fair match: same 10 starting reelsets, same simulator seed, "
             "same mutation operator and count, same 1000-evaluation budget.  "
             "Blue = GA usually wins, orange = hill climbing usually wins, 15/30 = coin flip.",
             fontsize=9, color=INK2)
    fig.subplots_adjust(left=0.17, right=0.9, top=0.82, bottom=0.12, wspace=0.08)
    fig.savefig(f"{OUT}/16_paired_wins_vs_hill_climbing.png", dpi=170)
    plt.close(fig)


# ---------------------------------------------------------------------------
# 17: one picture of all three experiments, each method at its best mutation count
# ---------------------------------------------------------------------------
def chart_overview():
    files = [("best_mut_base", "Base game", floor100["BaseGame"]),
             ("best_mut_free", "Free game (Both mode)", floor100["FreeGame"]),
             ("best_mut_fixed", "Free game (fixed base)", floor100["FreeGame"])]
    fig, axes = plt.subplots(1, 3, figsize=(15, 5.4))
    for k, (ax, (f, title, fl)) in enumerate(zip(axes, files)):
        b = pd.read_csv(BEST[f]).sort_values("best_median", ascending=False)
        ys = np.arange(len(b))
        best = b.best_median.min()
        ax.axvspan(best, best + fl, color="#d55181", alpha=0.12, lw=0)
        for y, (_, r) in zip(ys, b.iterrows()):
            c = STRAT[family(r.method)]
            mk = "D" if r.is_baseline else "o"
            ax.plot([b.best_median.min() * 0.9, r.best_median], [y, y], color=GRID, lw=1, zorder=1)
            ax.plot(r.best_median, y, mk, ms=8, color=c, mec="white", mew=1.5, zorder=3)
            ax.text(r.best_median, y + 0.32, f"  {r.best_median:.3f}  (m={r.best_mutation})",
                    fontsize=8, color=INK2, va="center")
        ax.set_yticks(ys)
        ax.set_yticklabels(b.method, fontsize=9)
        ax.set_title(title, loc="left", fontsize=11, fontweight="bold")
        ax.set_xlabel("Median final error (lower = better)")
        ax.grid(axis="y", visible=False)
        span = b.best_median.max() - b.best_median.min()
        ax.set_xlim(b.best_median.min() - 0.08 * span, b.best_median.max() + 0.45 * span)
        ax.set_ylim(-1.0, len(b) - 0.2)
        ax.text(best, -0.55, " within noise of the best", fontsize=8,
                color="#b33b6b", va="bottom")
    handles = [plt.Line2D([], [], marker="o", ls="", color=STRAT[s], ms=8, label=s)
               for s in ["Steady-state", "Elitist generational", "Generational"]]
    handles += [plt.Line2D([], [], marker="D", ls="", color=STRAT[s], ms=8, label=s + " (baseline)")
                for s in ["Hill climbing", "Simulated annealing"]]
    fig.legend(handles=handles, loc="lower center", ncol=5, frameon=False, fontsize=9)
    fig.suptitle("All three experiments at a glance: every method tuned to its own best "
                 "mutation count (30 seeds; random search left out, error 37.5 / 62.8)",
                 x=0.01, ha="left", fontsize=12.5, fontweight="bold", color=INK)
    fig.tight_layout(rect=(0, 0.06, 1, 0.94))
    fig.savefig(f"{OUT}/17_overview_best_mutation.png", dpi=170)
    plt.close(fig)


chart_noise()
chart_paired()
chart_overview()
print(f"Charts 15-17 written to {OUT}/")
print("simulator SD of fitness at 10M spins:", sd10.round(4).to_dict(),
      "in-run floors:", {k: round(v, 4) for k, v in floor10.items()})