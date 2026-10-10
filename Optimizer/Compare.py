"""
GA reelset-tuning report charts.

Reads the save_sim_results JSON layout:
    seed_<S> -> results -> mutation_<M> -> <Replacement>_<Selection> -> results = [[best, mean], ...]

and writes 8 PNGs:
    1_convergence_by_strategy.png   best-so-far vs fitness evaluations, per strategy (one panel per mutation)
    2_final_error_by_mutation.png   final best error for every mutation rate (box + seed dots)
    3_heatmap_config_mutation.png   median final error, config x mutation
    4_speed_to_target.png           evaluations needed to reach error <= 0.5 / 0.2 (one mutation rate)
    5_steadystate_by_mutation.png   Steady-state convergence for each mutation rate
    6_selection_comparison.png      selection method within each strategy (median + IQR)
    7_best_vs_mean.png              best vs population-mean error over the run (diversity)
    8_final_best_mean_gap.png       final best vs final mean per strategy x mutation

x-axis is "fitness evaluations": each run is assumed to cost the same BUDGET evaluations, so
children-per-step = BUDGET / steps (SteadyState 1000 steps -> 1, Generational 100 -> 10,
Elitist 125 -> 8). Mutation <M> is shown as M stops out of REEL_SIZE (5 -> 10%).
"""
import json
import os
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, LogNorm
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

# ----------------------------------------------------------------- settings
BUDGET = 1000        # fitness evaluations per run
REEL_SIZE = 250       # stops per reel -> mutation % = M / REEL_SIZE
GRID = np.arange(10, BUDGET + 1, 10)   # common evaluation axis for curves

# ----------------------------------------------------------------- style
INK, INK2, MUTED, GRIDC, SURF = "#0b0b0b", "#52514e", "#8a8984", "#e6e5e0", "#ffffff"
STRATS = ["SteadyState", "ElistismGenerational", "Generational"]
SC = {"SteadyState": "#2a78d6", "ElistismGenerational": "#eb6834", "Generational": "#1baf7a"}
SL = {"SteadyState": "Steady-state", "ElistismGenerational": "Elitist generational", "Generational": "Generational"}
SELS = ["TournamentSelection", "RouletteSelection", "SUS"]
SELL = {"TournamentSelection": "Tournament", "RouletteSelection": "Roulette", "SUS": "SUS"}
SEQ = ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#0d366b", "#0a2a52"]   # light -> dark, low -> high mutation
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": MUTED,
    "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2, "axes.titlecolor": INK,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": GRIDC,
    "grid.linewidth": 0.8, "figure.facecolor": SURF, "axes.facecolor": SURF, "legend.frameon": False})


def pct(m):
    return f"{m * 100 / REEL_SIZE:g}%"


def pct_tick(m):
    return f"{pct(m)}\n({m}/{REEL_SIZE})"


def _save(fig, out_dir, name):
    path = os.path.join(out_dir, f"{name}.png")
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("wrote", path)
    return path


# ----------------------------------------------------------------- loading
def load(json_file):
    """Returns (df, curves).
    df: one row per run with final metrics.
    curves[(seed, mut, strategy, selection)] = dict(best=..., mean=...) on GRID (best = best-so-far)."""
    with open(json_file) as f:
        raw = json.load(f)
    rows, curves = [], {}
    for seed_key, seed_entry in raw.items():
        if not re.match(r"^seed_\d+$", seed_key):
            continue
        for mut_key, combos in seed_entry.get("results", {}).items():
            mm = re.match(r"^mutation_(\d+)$", mut_key)
            if not mm:
                continue
            mut = int(mm.group(1))
            for combo_key, entry in combos.items():
                strat, sel = combo_key.split("_", 1)
                strat = strat.replace("ElitismGenerational", "ElistismGenerational")   # accept both spellings
                arr = np.asarray(entry.get("results", []), dtype=float)
                if arr.ndim != 2 or len(arr) == 0:
                    continue
                best, mean = arr[:, 0], arr[:, 1]
                ev = np.arange(1, len(best) + 1) * (BUDGET / len(best))     # evaluations used after each step
                bsf = np.minimum.accumulate(best)                             # best-so-far
                curves[(seed_key, mut, strat, sel)] = dict(
                    best=np.interp(GRID, ev, bsf), mean=np.interp(GRID, ev, mean))
                r = dict(seed=seed_key, mutation=mut, strategy=strat, selection=sel,
                         config=f"{SL.get(strat, strat)} + {SELL.get(sel, sel)}",
                         final_best=bsf[-1], final_mean=mean[-1])
                for t in (0.5, 0.2):
                    hit = np.where(bsf <= t)[0]
                    r[f"evals_to_{t}"] = float(ev[hit[0]]) if len(hit) else np.nan
                rows.append(r)
    if not rows:
        raise ValueError(f"No runs found in {json_file}")
    return pd.DataFrame(rows), curves


def _stack(curves, key, mut, strat, seeds=None):
    """All runs' curves (best or mean) for one mutation + strategy, optionally limited to some seeds."""
    return np.array([v[key] for (sd, m, st, _), v in curves.items()
                     if m == mut and st == strat and (seeds is None or sd in seeds)])


# ----------------------------------------------------------------- charts
def chart1_convergence(df, curves, out_dir, muts):
    fig, axes = plt.subplots(1, len(muts), figsize=(4.4 * len(muts), 4.2), sharey=True, squeeze=False)
    for ax, m in zip(axes[0], muts):
        for s in STRATS:
            A = _stack(curves, "best", m, s)
            if not len(A):
                continue
            ax.fill_between(GRID, np.percentile(A, 25, 0), np.percentile(A, 75, 0), color=SC[s], alpha=0.12, lw=0)
            ax.plot(GRID, np.median(A, 0), color=SC[s], lw=2, label=SL[s])
        ax.set_yscale("log"); ax.set_xlim(0, BUDGET); ax.set_xlabel("Fitness evaluations")
        ax.set_title(f"Mutation {pct(m)} ({m}/{REEL_SIZE} stops)", loc="left", fontsize=11)
        for t in (0.5, 0.1):
            ax.axhline(t, color=MUTED, lw=0.8, ls="--")
    axes[0][0].set_ylabel("Best error so far (log)")
    axes[0][0].legend(loc="upper right")
    fig.suptitle("Convergence by replacement strategy  (median over seeds × selections, band = IQR)",
                 x=0.01, ha="left", fontsize=12, color=INK)
    return _save(fig, out_dir, "1_convergence_by_strategy")


def chart2_final_by_mutation(df, out_dir, seeds, rates):
    sub_all = df[df.seed.isin(seeds)]
    fig, ax = plt.subplots(figsize=(1.6 * len(rates) + 0.5, 4.5))
    data = [sub_all[sub_all.mutation == r].final_best.values for r in rates]
    bp = ax.boxplot(data, positions=range(len(rates)), widths=0.5, patch_artist=True, showfliers=False,
                    medianprops=dict(color=INK, lw=2), whiskerprops=dict(color=MUTED), capprops=dict(color=MUTED))
    for p, c in zip(bp["boxes"], SEQ):
        p.set_facecolor(c); p.set_alpha(0.35); p.set_edgecolor(c)
    rng = np.random.default_rng(0)
    top = sub_all.final_best.max() * 2.5
    for i, r in enumerate(rates):
        sub = sub_all[sub_all.mutation == r]
        for s in STRATS:
            y = sub[sub.strategy == s].final_best.values
            ax.scatter(i + rng.uniform(-0.18, 0.18, len(y)), y, s=26, color=SC[s], edgecolor="white", lw=0.8,
                       zorder=3, label=SL[s] if i == 0 else None)
        ax.text(i, top, f"median {np.median(sub.final_best):.2f}", ha="center", va="bottom",
                fontsize=9, color=INK, fontweight="bold")
    ax.set_xticks(range(len(rates)), [pct_tick(r) for r in rates]); ax.set_yscale("log")
    ax.set_ylim(sub_all.final_best.min() * 0.6, top * 1.6)
    ax.set_xlabel(f"Mutation rate (stops mutated per reel of {REEL_SIZE})")
    ax.set_ylabel(f"Final best error after {BUDGET} evals (log)")
    ax.set_title(f"Final error by mutation rate  ({', '.join(s.replace('seed_', 'seed ') for s in seeds)}; all configs)",
                 loc="left", fontsize=11)
    ax.legend(loc="lower right", ncol=3, fontsize=8)
    return _save(fig, out_dir, "2_final_error_by_mutation")


def chart3_heatmap(df, out_dir, sort_mut):
    piv = df.pivot_table(index="config", columns="mutation", values="final_best", aggfunc="median")
    piv = piv.loc[piv[sort_mut].sort_values().index]
    nseeds = df.groupby("mutation").seed.nunique()
    cmap = LinearSegmentedColormap.from_list("b", ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"])
    vmin, vmax = np.nanmin(piv.values), np.nanmax(piv.values)
    fig, ax = plt.subplots(figsize=(1.6 * piv.shape[1] + 4, 0.58 * piv.shape[0] + 1.2))
    im = ax.imshow(piv.values, cmap=cmap, norm=LogNorm(vmin=vmin, vmax=vmax), aspect="auto")
    thresh = np.exp((np.log(vmin) + np.log(vmax)) / 2)
    for i in range(piv.shape[0]):
        for j in range(piv.shape[1]):
            v = piv.values[i, j]
            if np.isfinite(v):
                ax.text(j, i, f"{v:.3f}", ha="center", va="center", fontsize=9, color="white" if v > thresh else INK)
    ax.set_xticks(range(piv.shape[1]), [f"{pct_tick(c)}\n{nseeds[c]} seeds" for c in piv.columns])
    ax.set_yticks(range(piv.shape[0]), piv.index)
    ax.grid(False); ax.set_xlabel(f"Mutation rate (stops mutated per reel of {REEL_SIZE})")
    for sp in ax.spines.values():
        sp.set_visible(False)
    cb = fig.colorbar(im, ax=ax, shrink=0.8)
    cb.set_label("Median final best error (log)", color=INK2); cb.outline.set_visible(False)
    ax.set_title("Median final error per configuration  (lower = better)", loc="left", fontsize=11)
    return _save(fig, out_dir, "3_heatmap_config_mutation")


def chart4_speed(df, out_dir, mut):
    g = df[df.mutation == mut]
    sp = g.groupby("config").agg(strategy=("strategy", "first"),
                                 e05=("evals_to_0.5", "median"), s05=("evals_to_0.5", lambda s: s.notna().mean()),
                                 e02=("evals_to_0.2", "median"), s02=("evals_to_0.2", lambda s: s.notna().mean()))
    sp["key"] = sp.e02.fillna(1e9)
    sp = sp.sort_values(["key", "e05"], ascending=False)
    fig, ax = plt.subplots(figsize=(9, 0.55 * len(sp) + 0.6))
    y = np.arange(len(sp))
    cols = [SC.get(s, MUTED) for s in sp.strategy]
    ax.barh(y + 0.19, sp.e05.fillna(0), height=0.36, color=cols, alpha=0.45)
    ax.barh(y - 0.19, sp.e02.fillna(0), height=0.36, color=cols)
    for yi, (_, r) in zip(y, sp.iterrows()):
        l05 = f"{r.e05:.0f}  ({r.s05:.0%} of seeds)" if r.e05 == r.e05 else "never reached (0% of seeds)"
        l02 = f"{r.e02:.0f}  ({r.s02:.0%} of seeds)" if r.e02 == r.e02 else "never reached (0% of seeds)"
        ax.text((r.e05 if r.e05 == r.e05 else 0) + 12, yi + 0.19, l05, va="center", fontsize=8, color=INK2)
        ax.text((r.e02 if r.e02 == r.e02 else 0) + 12, yi - 0.19, l02, va="center", fontsize=8, color=INK)
    ax.set_yticks(y, sp.index); ax.set_xlim(0, BUDGET * 1.05); ax.grid(axis="y", visible=False)
    ax.set_xlabel("Median fitness evaluations needed (of seeds that reached it)")
    ax.set_title(f"How fast each configuration hits the target  (mutation {pct(mut)} = {mut}/{REEL_SIZE} stops, "
                 f"{g.seed.nunique()} seeds)", loc="left", fontsize=11)
    ax.legend(handles=[Patch(color=MUTED, alpha=0.45, label="to reach error ≤ 0.5"),
                       Patch(color=MUTED, label="to reach error ≤ 0.2")],
              loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2)
    return _save(fig, out_dir, "4_speed_to_target")


def chart5_steadystate_by_mutation(curves, out_dir, seeds, rates):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ends = []
    for r, c in zip(rates, SEQ):
        A = _stack(curves, "best", r, "SteadyState", seeds)
        if not len(A):
            continue
        med = np.median(A, 0)
        ax.plot(GRID, med, color=c, lw=2)
        ends.append([med[-1], pct(r)])
    # spread end labels so they don't overlap (log space)
    ends.sort(key=lambda e: e[0])
    for i in range(1, len(ends)):
        if np.log10(ends[i][0]) - np.log10(ends[i - 1][0]) < 0.13:
            ends[i][0] = ends[i - 1][0] * 10 ** 0.13
    for yv, lab in ends:
        ax.text(BUDGET * 1.008, yv, lab, color=INK, va="center", fontsize=9)
    ax.set_yscale("log"); ax.set_xlim(0, BUDGET * 1.06)
    ax.set_xlabel("Fitness evaluations"); ax.set_ylabel("Best error so far (log)")
    for t in (0.5, 0.1):
        ax.axhline(t, color=MUTED, lw=0.8, ls="--")
    ax.set_title(f"Steady-state GA: effect of mutation rate over the run  "
                 f"({', '.join(s.replace('seed_', 'seed ') for s in seeds)}; median of 3 selections)",
                 loc="left", fontsize=11)
    return _save(fig, out_dir, "5_steadystate_by_mutation")


def chart6_selection(df, out_dir, muts):
    main = df[df.mutation.isin(muts)]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    for i, s in enumerate(STRATS):
        for j, sel in enumerate(SELS):
            g = main[(main.strategy == s) & (main.selection == sel)].final_best
            if g.empty:
                continue
            x = j + (i - 1) * 0.25
            ax.vlines(x, g.quantile(.25), g.quantile(.75), color=SC[s], lw=3, alpha=0.5)
            ax.scatter([x], [g.median()], s=60, color=SC[s], edgecolor="white", lw=1.5, zorder=3,
                       label=SL[s] if j == 0 else None)
    ax.set_xticks(range(len(SELS)), [SELL[s] for s in SELS]); ax.set_yscale("log")
    ax.set_ylabel("Final best error (log)")
    ax.set_title(f"Selection method within each strategy  (dot = median, bar = IQR; mutation "
                 f"{'/'.join(pct(m) for m in muts)})", loc="left", fontsize=11)
    ax.legend(loc="upper left"); ax.grid(axis="x", visible=False)
    return _save(fig, out_dir, "6_selection_comparison")


def chart7_best_vs_mean(curves, out_dir, muts):
    fig, axes = plt.subplots(1, len(muts), figsize=(4.4 * len(muts), 4.4), sharey=True, squeeze=False)
    for ax, m in zip(axes[0], muts):
        for s in STRATS:
            B = _stack(curves, "best", m, s)
            M = _stack(curves, "mean", m, s)
            if not len(B):
                continue
            B, M = np.median(B, 0), np.median(M, 0)
            ax.fill_between(GRID, B, M, color=SC[s], alpha=0.08, lw=0)
            ax.plot(GRID, B, color=SC[s], lw=2)
            ax.plot(GRID, M, color=SC[s], lw=1.6, ls="--")
        ax.set_yscale("log"); ax.set_xlim(0, BUDGET); ax.set_xlabel("Fitness evaluations")
        ax.set_title(f"Mutation {pct(m)} ({m}/{REEL_SIZE} stops)", loc="left", fontsize=11)
    axes[0][0].set_ylabel("Error (log)")
    h = [Line2D([], [], color=SC[s], lw=2, label=SL[s]) for s in STRATS] + \
        [Line2D([], [], color=INK2, lw=2, label="best"),
         Line2D([], [], color=INK2, lw=1.6, ls="--", label="population mean")]
    fig.legend(handles=h, loc="lower center", ncol=5, fontsize=9, bbox_to_anchor=(0.5, -0.06))
    fig.suptitle("Best vs population-mean error  (median over seeds × selections; shaded = gap = remaining diversity)",
                 x=0.01, ha="left", fontsize=12, color=INK)
    return _save(fig, out_dir, "7_best_vs_mean")


def chart8_best_mean_gap(df, out_dir, rates):
    fig, ax = plt.subplots(figsize=(9, 0.33 * len(STRATS) * len(rates) + 1.2))
    y, ticks = 0, []
    for s in STRATS:
        for m in rates:
            g = df[(df.strategy == s) & (df.mutation == m)]
            if g.empty:
                continue
            b, mu = g.final_best.median(), g.final_mean.median()
            ax.plot([b, mu], [y, y], color=SC[s], lw=2, alpha=0.5)
            ax.scatter([b], [y], s=55, color=SC[s], edgecolor="white", lw=1.2, zorder=3)
            ax.scatter([mu], [y], s=55, facecolor="white", edgecolor=SC[s], lw=1.8, zorder=3)
            ax.text(max(b, mu) * 1.15, y, f"×{mu / b:.1f}", va="center", fontsize=8, color=INK2)
            ticks.append((y, f"{SL[s]}  {pct(m)}"))
            y += 1
        y += 0.8
    ax.set_yticks([t[0] for t in ticks], [t[1] for t in ticks], fontsize=8.5); ax.invert_yaxis()
    ax.set_xscale("log"); ax.grid(axis="y", visible=False)
    ax.set_xlabel("Final error (log)  —  ● best   ○ population mean   (×n = mean / best)")
    ax.set_title("How far the population sits from its best at the end of the run  (median over seeds)",
                 loc="left", fontsize=11)
    return _save(fig, out_dir, "8_final_best_mean_gap")


# ----------------------------------------------------------------- main
def run_all(json_file, out_dir="plots", speed_mutation=5):
    """Draw all 8 report charts. speed_mutation = mutation count used for chart 4 (and heatmap sort)."""
    os.makedirs(out_dir, exist_ok=True)
    df, curves = load(json_file)
    all_rates = sorted(df.mutation.unique())
    seeds = sorted(df.seed.unique(), key=lambda s: int(s.split("_")[1]))
    # mutation rates every seed has (fair 5-seed comparisons)
    common = [m for m in all_rates if df[df.mutation == m].seed.nunique() == len(seeds)] or all_rates
    # seeds that have every mutation rate (fair all-rates comparisons)
    full_seeds = [s for s in seeds if set(df[df.seed == s].mutation) == set(all_rates)] or seeds
    if speed_mutation not in all_rates:
        speed_mutation = common[0]
    panels7 = sorted({all_rates[0], speed_mutation, all_rates[-1]})

    out = [
        chart1_convergence(df, curves, out_dir, common),
        chart2_final_by_mutation(df, out_dir, full_seeds, all_rates),
        chart3_heatmap(df, out_dir, speed_mutation),
        chart4_speed(df, out_dir, speed_mutation),
        chart5_steadystate_by_mutation(curves, out_dir, full_seeds, all_rates),
        chart6_selection(df, out_dir, common),
        chart7_best_vs_mean(curves, out_dir, panels7),
        chart8_best_mean_gap(df, out_dir, all_rates),
    ]
    return out


if __name__ == "__main__":
    run_all("Results/results-1000-5-runs.json", "Results")