"""
GA reelset-tuning report charts.

Reads the save_sim_results JSON layout:
    seed_<S> -> results -> mutation_<M> -> <Replacement>_<Selection> -> results = [[best, mean], ...]
    seed_<S> -> results -> mutation_<M> -> <Method>_Baseline         -> results = [[best, current], ...]
and, when the runs recorded it (see Compute.py), the computing cost:
    seed_<S> -> compute / machines,   ... -> <combo> -> timing

and writes these PNGs:
    1_convergence_by_strategy.png   best-so-far vs fitness evaluations, per strategy + baselines (one panel per mutation)
    2_final_error_by_mutation.png   final best error for every mutation rate (GA box + seed dots, baseline dots beside)
    3_heatmap_config_mutation.png   median final error, config x mutation (baselines are rows too)
    4_speed_to_target.png           evaluations needed to reach error <= 0.5 / 0.2 (one mutation rate)
    5_steadystate_by_mutation.png   Steady-state vs hill climbing convergence for each mutation rate
    6_selection_comparison.png      selection method within each strategy, baselines alongside (median + IQR)
    7_best_vs_mean.png              best vs population-mean error over the run (diversity; GA only)
    8_final_best_mean_gap.png       final best vs final mean per strategy x mutation (GA only)
    9_ga_vs_baselines.png           best GA configuration vs each baseline: convergence + per-seed finals
  computing cost (only for runs that recorded timing):
    10_compute_cost.png             time per evaluation and per run for every method; seconds and
                                    noise per evaluation against spins (the case for run.spins)
    11_budget_and_population.png    what the last evaluations still buy, in error and in hours (the case
                                    for run.generations); generations and start-up cost per population size
    12_machine_comparison.png       the same work timed on each machine (only when the file has several)
    compute_report.md               the numbers behind 10-12: machines, time per evaluation / run / study,
                                    and the cost-based case for spins, budget and population size

x-axis is "fitness evaluations": every run costs the same BUDGET evaluations (run.generations,
read from the file's meta), so children-per-step = BUDGET / steps (with 1000: SteadyState 1000
steps -> 1, Generational 100 -> 10, Elitist 125 -> 8, every baseline 1000 -> 1).
Mutation <M> is shown as M stops out of REEL_SIZE (stops per reelset, read from the file).
Random search ignores the mutation count, so the same random-search runs appear at every rate.
Charts 7 and 8 measure population diversity; the baselines keep a single reelset, so they are
left out there.

Usage (from the project root):
    python Optimizer/Compare.py                                   # Results/results.json, auto stage
    python Optimizer/Compare.py Results/results.json --stage free # free-game stage (seed_<n>_free)
    python Optimizer/Compare.py my.json --out plots --mutation 5  # other file / folder / chart-4 rate
--stage auto (default) uses the BaseGame runs if the file has any, otherwise the FreeGame runs.
Charts go to Results/ (base) or Results/FreeGame/ (free) unless --out is given.
"""
import argparse
import json
import math
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
from matplotlib.ticker import NullFormatter

# ----------------------------------------------------------------- settings
# Defaults only: load() replaces them with the values in the results file.
BUDGET = 1000        # fitness evaluations per run (run.generations)
REEL_SIZE = 250       # stops per reelset -> mutation % = M / REEL_SIZE
GRID = np.arange(10, BUDGET + 1, 10)   # common evaluation axis for curves
STAGES = {"base": r"^seed_\d+$", "free": r"^seed_\d+_free$"}   # BaseGame / FreeGame results keys


def _set_scale(budget, reel_size):
    """Use the file's budget and reelset size for every chart."""
    global BUDGET, REEL_SIZE, GRID
    BUDGET, REEL_SIZE = int(budget), int(reel_size)
    step = max(1, BUDGET // 100)
    GRID = np.arange(step, BUDGET + 1, step)

# ----------------------------------------------------------------- style
INK, INK2, MUTED, GRIDC, SURF = "#0b0b0b", "#52514e", "#8a8984", "#e6e5e0", "#ffffff"
STRATS = ["SteadyState", "ElistismGenerational", "Generational"]
SC = {"SteadyState": "#2a78d6", "ElistismGenerational": "#eb6834", "Generational": "#1baf7a"}
SL = {"SteadyState": "Steady-state", "ElistismGenerational": "Elitist generational", "Generational": "Generational"}
SELS = ["TournamentSelection", "RouletteSelection", "SUS"]
SELL = {"TournamentSelection": "Tournament", "RouletteSelection": "Roulette", "SUS": "SUS"}
SEQ = ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#0d366b", "#0a2a52"]   # light -> dark, low -> high mutation

# baselines: stored as <Method>_Baseline. Non-solid lines and their own marker shapes, so they
# never rely on colour alone. Random search is a gray dotted reference line (the floor to beat).
BASELINE_TAG = "Baseline"
BLS = ["HillClimbing", "SimulatedAnnealing", "RandomSearch"]
BC = {"HillClimbing": "#a3329e", "SimulatedAnnealing": "#7a5c00", "RandomSearch": "#5c5b57"}
BL = {"HillClimbing": "Hill climbing (1+1)-EA", "SimulatedAnnealing": "Simulated annealing",
      "RandomSearch": "Random search"}
BLS_LS = {"HillClimbing": "--", "SimulatedAnnealing": "-.", "RandomSearch": ":"}
BLS_MK = {"HillClimbing": "D", "SimulatedAnnealing": "^", "RandomSearch": "s"}
COLOR = {**SC, **BC}
LABEL = {**SL, **BL}

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


def _baseline_handles():
    return [Line2D([], [], color=BC[b], lw=1.8, ls=BLS_LS[b], marker=BLS_MK[b], ms=5, label=BL[b])
            for b in BLS]


def _config_label(strat, sel):
    """'Steady-state + Tournament', or 'Baseline: Hill climbing (1+1)-EA'."""
    if sel == BASELINE_TAG:
        return f"Baseline: {BL.get(strat, strat)}"
    return f"{SL.get(strat, strat)} + {SELL.get(sel, sel)}"


# ----------------------------------------------------------------- loading
def _stops(reelset):
    """Number of stops in a reelset, accepting the extra list level parent files use."""
    if reelset and isinstance(reelset[0], list) and reelset[0] and isinstance(reelset[0][0], list):
        reelset = reelset[0]
    return sum(len(reel) for reel in reelset)


def stages_in(raw):
    """Which stages ("base", "free") have runs in a loaded results file."""
    return [s for s, pat in STAGES.items() if any(re.match(pat, k) for k in raw)]


def _scale_from(raw, keys, stage):
    """Budget and reelset size of the runs being charted; all runs must agree on them."""
    budgets = {e.get("meta", {}).get("generations") for k, e in raw.items() if k in keys}
    budgets.discard(None)
    if len(budgets) > 1:
        raise ValueError(f"These runs used different budgets (run.generations): {sorted(budgets)}. "
                         "Chart runs with the same budget together.")
    sizes = set()
    reel_key = "BaseGameReel" if stage == "base" else "FreeGameReel"
    for k in keys:
        pop = raw[k].get("initial_population") or []
        if pop:
            sizes.add(_stops(pop[0][reel_key]))
    if len(sizes) > 1:
        raise ValueError(f"These runs have different reelset sizes: {sorted(sizes)}")
    return (budgets.pop() if budgets else BUDGET), (sizes.pop() if sizes else REEL_SIZE)


def load(json_file, stage="base"):
    """Returns (df, curves) for one stage: "base" (seed_<n>) or "free" (seed_<n>_free).
    Also sets BUDGET and REEL_SIZE from the file.
    df: one row per run with final metrics (GA combinations and baselines; baseline rows have
        selection == "Baseline" and is_baseline == True).
    curves[(seed, mut, strategy, selection)] = dict(best=..., mean=...) on GRID (best = best-so-far).
    For a baseline, strategy is the method name and "mean" is the reelset it is currently on."""
    with open(json_file) as f:
        raw = json.load(f)
    keys = [k for k in raw if re.match(STAGES[stage], k)]
    if not keys:
        found = ", ".join(stages_in(raw)) or "none"
        raise ValueError(f"No {stage}-game runs in {json_file} (stages found: {found})")
    _set_scale(*_scale_from(raw, keys, stage))

    rows, curves = [], {}
    for seed_key in keys:
        seed_entry = raw[seed_key]
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
                is_bl = sel == BASELINE_TAG
                r = dict(seed=seed_key, mutation=mut, strategy=strat, selection=sel,
                         config=_config_label(strat, sel), is_baseline=is_bl,
                         final_best=bsf[-1], final_mean=mean[-1])
                for t in (0.5, 0.2):
                    hit = np.where(bsf <= t)[0]
                    r[f"evals_to_{t}"] = float(ev[hit[0]]) if len(hit) else np.nan
                rows.append(r)
    if not rows:
        raise ValueError(f"No {stage}-game results found in {json_file}")
    return pd.DataFrame(rows), curves


def _stack(curves, key, mut, strat, seeds=None, sel=None):
    """All runs' curves (best or mean) for one mutation + strategy (or baseline method),
    optionally limited to some seeds or one selection method."""
    return np.array([v[key] for (sd, m, st, se), v in curves.items()
                     if m == mut and st == strat and (seeds is None or sd in seeds)
                     and (sel is None or se == sel)])


def _ga(df):
    return df[~df.is_baseline]


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
        for b in BLS:
            A = _stack(curves, "best", m, b)
            if not len(A):
                continue
            med = np.median(A, 0)
            ax.plot(GRID, med, color=BC[b], lw=1.8, ls=BLS_LS[b], label=BL[b])
            ax.plot(GRID[-1], med[-1], color=BC[b], marker=BLS_MK[b], ms=6, ls="none")
        ax.set_yscale("log"); ax.set_xlim(0, BUDGET); ax.set_xlabel("Fitness evaluations")
        ax.set_title(f"Mutation {pct(m)} ({m}/{REEL_SIZE} stops)", loc="left", fontsize=11)
        for t in (0.5, 0.1):
            ax.axhline(t, color=MUTED, lw=0.8, ls="--")
    axes[0][0].set_ylabel("Best error so far (log)")
    h, l = axes[0][0].get_legend_handles_labels()
    ncol = min(len(l), 6 if len(muts) > 1 else 2)
    fig.legend(h, l, loc="lower center", ncol=ncol, fontsize=9,
               bbox_to_anchor=(0.5, -0.08 if len(muts) > 1 else -0.16))
    sep = "  " if len(muts) > 1 else "\n"
    fig.suptitle(f"Convergence by replacement strategy vs baselines{sep}"
                 "(median over seeds × selections, band = GA IQR)",
                 x=0.01, ha="left", fontsize=12, color=INK, y=1.0 if len(muts) > 1 else 1.1)
    return _save(fig, out_dir, "1_convergence_by_strategy")


def chart2_final_by_mutation(df, out_dir, seeds, rates):
    sub_all = df[df.seed.isin(seeds)]
    ga = _ga(sub_all)
    fig, ax = plt.subplots(figsize=(max(6.0, 2.0 * len(rates) + 0.8), 4.8))
    data = [ga[ga.mutation == r].final_best.values for r in rates]
    bp = ax.boxplot(data, positions=range(len(rates)), widths=0.42, patch_artist=True, showfliers=False,
                    medianprops=dict(color=INK, lw=2), whiskerprops=dict(color=MUTED), capprops=dict(color=MUTED))
    for p, c in zip(bp["boxes"], SEQ):
        p.set_facecolor(c); p.set_alpha(0.35); p.set_edgecolor(c)
    rng = np.random.default_rng(0)
    top = sub_all.final_best.max() * 2.5
    bl_x = {"HillClimbing": 0.33, "SimulatedAnnealing": 0.43, "RandomSearch": 0.53}   # right of each box
    for i, r in enumerate(rates):
        sub = ga[ga.mutation == r]
        for s in STRATS:
            y = sub[sub.strategy == s].final_best.values
            ax.scatter(i + rng.uniform(-0.15, 0.15, len(y)), y, s=24, color=SC[s], edgecolor="white", lw=0.8,
                       zorder=3, label=SL[s] if i == 0 and len(y) else None)
        for b in BLS:
            y = sub_all[(sub_all.mutation == r) & (sub_all.strategy == b)].final_best.values
            if not len(y):
                continue
            ax.scatter(np.full(len(y), i + bl_x[b]), y, s=26, marker=BLS_MK[b], color=BC[b],
                       edgecolor="white", lw=0.8, zorder=3, label=BL[b] if i == 0 else None)
            ax.hlines(np.median(y), i + bl_x[b] - 0.04, i + bl_x[b] + 0.04, color=INK, lw=1.6, zorder=4)
        if len(sub):
            ax.text(i, top, f"GA median {np.median(sub.final_best):.2f}", ha="center", va="bottom",
                    fontsize=9, color=INK, fontweight="bold")
    ax.set_xticks(range(len(rates)), [pct_tick(r) for r in rates]); ax.set_yscale("log")
    ax.set_xlim(-0.5, len(rates) - 0.5 + 0.2)
    ax.set_ylim(sub_all.final_best.min() * 0.6, top * 1.6)
    ax.set_xlabel(f"Mutation rate (stops mutated out of {REEL_SIZE} in the reelset)")
    ax.set_ylabel(f"Final best error after {BUDGET} evals (log)")
    ax.set_title(f"Final error by mutation rate  ({len(seeds)} seeds)\n"
                 f"box = all GA configs; baselines to the right, tick = median",
                 loc="left", fontsize=11)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=3, fontsize=8)
    return _save(fig, out_dir, "2_final_error_by_mutation")


def chart3_heatmap(df, out_dir, sort_mut):
    piv = df.pivot_table(index="config", columns="mutation", values="final_best", aggfunc="median")
    piv = piv.loc[piv[sort_mut].sort_values().index]
    nseeds = df.groupby("mutation").seed.nunique()
    cmap = LinearSegmentedColormap.from_list("b", ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"])
    vmin, vmax = np.nanmin(piv.values), np.nanmax(piv.values)
    fig, ax = plt.subplots(figsize=(1.6 * piv.shape[1] + 4.6, 0.58 * piv.shape[0] + 1.2))
    im = ax.imshow(piv.values, cmap=cmap, norm=LogNorm(vmin=vmin, vmax=vmax), aspect="auto")
    thresh = np.exp((np.log(vmin) + np.log(vmax)) / 2)
    for i in range(piv.shape[0]):
        for j in range(piv.shape[1]):
            v = piv.values[i, j]
            if np.isfinite(v):
                ax.text(j, i, f"{v:.3f}", ha="center", va="center", fontsize=9, color="white" if v > thresh else INK)
    ax.set_xticks(range(piv.shape[1]), [f"{pct_tick(c)}\n{nseeds[c]} seeds" for c in piv.columns])
    ax.set_yticks(range(piv.shape[0]), piv.index)
    for lab in ax.get_yticklabels():                   # baselines in italics, so they stand out
        if lab.get_text().startswith("Baseline:"):
            lab.set_fontstyle("italic"); lab.set_color(INK)
    ax.grid(False); ax.set_xlabel(f"Mutation rate (stops mutated out of {REEL_SIZE} in the reelset)")
    for sp in ax.spines.values():
        sp.set_visible(False)
    cb = fig.colorbar(im, ax=ax, shrink=0.8)
    cb.set_label("Median final best error (log)", color=INK2); cb.outline.set_visible(False)
    ax.set_title("Median final error per configuration and baseline  (lower = better)", loc="left", fontsize=11)
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
    cols = [COLOR.get(s, MUTED) for s in sp.strategy]
    hatches = ["///" if s in BC else None for s in sp.strategy]     # baselines also hatched
    ax.barh(y + 0.19, sp.e05.fillna(0), height=0.36, color=cols, alpha=0.45, hatch=hatches, edgecolor="white")
    ax.barh(y - 0.19, sp.e02.fillna(0), height=0.36, color=cols, hatch=hatches, edgecolor="white")
    for yi, (_, r) in zip(y, sp.iterrows()):
        l05 = f"{r.e05:.0f}  ({r.s05:.0%} of seeds)" if r.e05 == r.e05 else "never reached (0% of seeds)"
        l02 = f"{r.e02:.0f}  ({r.s02:.0%} of seeds)" if r.e02 == r.e02 else "never reached (0% of seeds)"
        ax.text((r.e05 if r.e05 == r.e05 else 0) + 12, yi + 0.19, l05, va="center", fontsize=8, color=INK2)
        ax.text((r.e02 if r.e02 == r.e02 else 0) + 12, yi - 0.19, l02, va="center", fontsize=8, color=INK)
    ax.set_yticks(y, sp.index); ax.set_xlim(0, BUDGET * 1.05); ax.grid(axis="y", visible=False)
    for lab in ax.get_yticklabels():
        if lab.get_text().startswith("Baseline:"):
            lab.set_fontstyle("italic")
    ax.set_xlabel("Median fitness evaluations needed (of seeds that reached it)")
    ax.set_title(f"How fast each configuration hits the target  (mutation {pct(mut)} = {mut}/{REEL_SIZE} stops, "
                 f"{g.seed.nunique()} seeds)", loc="left", fontsize=11)
    ax.legend(handles=[Patch(color=MUTED, alpha=0.45, label="to reach error ≤ 0.5"),
                       Patch(color=MUTED, label="to reach error ≤ 0.2"),
                       Patch(facecolor=MUTED, hatch="///", edgecolor="white", label="baseline")],
              loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=3)
    return _save(fig, out_dir, "4_speed_to_target")


def chart5_steadystate_by_mutation(curves, out_dir, seeds, rates):
    """Steady-state GA (solid) against hill climbing (dashed) at every mutation rate. Hill climbing
    is a population-1 Steady-state GA without crossover, so the gap is what the population and
    crossover add."""
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ends = []
    for r, c in zip(rates, SEQ):
        A = _stack(curves, "best", r, "SteadyState", seeds)
        if len(A):
            med = np.median(A, 0)
            ax.plot(GRID, med, color=c, lw=2)
            ends.append([med[-1], pct(r)])
        H = _stack(curves, "best", r, "HillClimbing", seeds)
        if len(H):
            ax.plot(GRID, np.median(H, 0), color=c, lw=1.6, ls="--")
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
    ax.legend(handles=[Line2D([], [], color=INK2, lw=2, label="Steady-state GA (median of 3 selections)"),
                       Line2D([], [], color=INK2, lw=1.6, ls="--", label="Hill climbing (1+1)-EA"),
                       Line2D([], [], color=SEQ[0], lw=3, label="light = low mutation"),
                       Line2D([], [], color=SEQ[-2], lw=3, label="dark = high mutation")],
              loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=2, fontsize=9)
    ax.set_title(f"Steady-state GA vs hill climbing at each mutation rate  "
                 f"({len(seeds)} seeds)",
                 loc="left", fontsize=11)
    return _save(fig, out_dir, "5_steadystate_by_mutation")


def chart6_selection(df, out_dir, muts):
    main = df[df.mutation.isin(muts)]
    fig, ax = plt.subplots(figsize=(9.5, 4.2))
    for i, s in enumerate(STRATS):
        for j, sel in enumerate(SELS):
            g = main[(main.strategy == s) & (main.selection == sel)].final_best
            if g.empty:
                continue
            x = j + (i - 1) * 0.25
            ax.vlines(x, g.quantile(.25), g.quantile(.75), color=SC[s], lw=3, alpha=0.5)
            ax.scatter([x], [g.median()], s=60, color=SC[s], edgecolor="white", lw=1.5, zorder=3,
                       label=SL[s] if j == 0 else None)
    xb = len(SELS) + 0.3        # baselines have no selection: their own group on the right
    for k, b in enumerate(BLS):
        g = main[main.strategy == b].final_best
        if g.empty:
            continue
        x = xb + (k - 1) * 0.25
        ax.vlines(x, g.quantile(.25), g.quantile(.75), color=BC[b], lw=3, alpha=0.5)
        ax.scatter([x], [g.median()], s=60, marker=BLS_MK[b], color=BC[b], edgecolor="white", lw=1.5,
                   zorder=3, label=BL[b])
    ax.axvline(len(SELS) - 0.35, color=GRIDC, lw=1)
    ax.set_xticks(list(range(len(SELS))) + [xb], [SELL[s] for s in SELS] + ["Baselines\n(no selection)"])
    ax.set_yscale("log")
    ax.set_ylabel("Final best error (log)")
    ax.set_title(f"Selection method within each strategy, baselines alongside  (dot = median, bar = IQR; "
                 f"mutation {'/'.join(pct(m) for m in muts)})", loc="left", fontsize=11)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=3, fontsize=9); ax.grid(axis="x", visible=False)
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
    df = _ga(df)
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


def _best_ga_config(df, mut):
    """(config label, strategy, selection) of the GA configuration with the lowest median final error."""
    ga = _ga(df[df.mutation == mut])
    if ga.empty:
        return None
    best_cfg = ga.groupby("config").final_best.median().idxmin()
    bstrat, bsel = ga[ga.config == best_cfg][["strategy", "selection"]].iloc[0]
    return best_cfg, bstrat, bsel


def chart9_ga_vs_baselines(df, curves, out_dir, mut):
    """Best GA configuration at this mutation rate (lowest median final error) against each
    baseline: median convergence with IQR, then each seed's final error, with the best GA and
    hill climbing joined per seed so wins and losses are visible run by run."""
    g = df[df.mutation == mut]
    ga = _ga(g)
    bls = [b for b in BLS if (g.strategy == b).any()]
    if ga.empty or not bls:
        print("chart 9 skipped: needs GA and baseline results at mutation", mut)
        return None
    best_cfg, bstrat, bsel = _best_ga_config(df, mut)

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(13, 4.8),
                                  gridspec_kw=dict(width_ratios=[1.5, 1], wspace=0.28))
    series = [("GA", best_cfg, SC.get(bstrat, INK), "-", "o",
               _stack(curves, "best", mut, bstrat, sel=bsel))]
    series += [(b, BL[b], BC[b], BLS_LS[b], BLS_MK[b], _stack(curves, "best", mut, b)) for b in bls]
    for _, lab, c, ls, mk, A in series:
        ax.fill_between(GRID, np.percentile(A, 25, 0), np.percentile(A, 75, 0), color=c, alpha=0.10, lw=0)
        ax.plot(GRID, np.median(A, 0), color=c, lw=2, ls=ls, label=lab)
    ax.set_yscale("log"); ax.set_xlim(0, BUDGET)
    ax.set_xlabel("Fitness evaluations"); ax.set_ylabel("Best error so far (log)")
    for t in (0.5, 0.1):
        ax.axhline(t, color=MUTED, lw=0.8, ls="--")
    ax.set_title("Convergence  (median, band = IQR over seeds)", loc="left", fontsize=11)
    ax.legend(loc="upper right", fontsize=9)

    # per-seed finals; best GA and hill climbing joined by a line for each seed
    seeds = sorted(g.seed.unique(), key=lambda s: int(s.split("_")[1]))
    ga_final = ga[ga.config == best_cfg].set_index("seed").final_best
    cols = [("GA", ga_final, SC.get(bstrat, INK), "o")]
    cols += [(b, g[g.strategy == b].set_index("seed").final_best, BC[b], BLS_MK[b]) for b in bls]
    for k, (_, vals, c, mk) in enumerate(cols):
        v = vals.reindex(seeds).values
        ax2.scatter(np.full(len(v), k), v, s=34, marker=mk, color=c, edgecolor="white", lw=0.8, zorder=3)
        ax2.hlines(np.nanmedian(v), k - 0.22, k + 0.22, color=INK, lw=2, zorder=4)
    if "HillClimbing" in bls:
        hc = g[g.strategy == "HillClimbing"].set_index("seed").final_best
        k_hc = 1 + bls.index("HillClimbing")
        wins = 0
        for s in seeds:
            if s in ga_final.index and s in hc.index:
                ax2.plot([0, k_hc], [ga_final[s], hc[s]], color=MUTED, lw=0.7, alpha=0.6, zorder=1)
                wins += ga_final[s] < hc[s]
        n = len(set(ga_final.index) & set(hc.index))
        ax2.set_title(f"Final error per seed  (GA beats hill climbing on {wins}/{n} seeds)",
                      loc="left", fontsize=11)
    else:
        ax2.set_title("Final error per seed", loc="left", fontsize=11)
    short = {"HillClimbing": "Hill\nclimbing", "SimulatedAnnealing": "Simulated\nannealing",
             "RandomSearch": "Random\nsearch"}
    ax2.set_xticks(range(len(cols)), ["Best\nGA"] + [short[b] for b in bls])
    ax2.set_yscale("log"); ax2.grid(axis="x", visible=False)
    ax2.yaxis.set_minor_formatter(NullFormatter())
    ax2.set_ylabel(f"Final best error after {BUDGET} evals (log)")
    fig.suptitle(f"Best GA configuration ({best_cfg}) vs baselines  —  mutation {pct(mut)} "
                 f"({mut}/{REEL_SIZE} stops), {len(seeds)} seeds",
                 x=0.01, ha="left", fontsize=12, color=INK)
    return _save(fig, out_dir, "9_ga_vs_baselines")


# ================================================================= computing cost
# Fitness SD of ONE 10M-spin evaluation (simulator noise study, claude/noise-study-results.md;
# worst case over the reelsets measured), scaling as 1/sqrt(spins). Same numbers as Stats.py.
NOISE_SD_10M = {"base": 0.034, "free": 0.10}
Z_DIFF_95 = 2.77                 # two independent measurements must differ by 2.77 SD to tell apart (95%)
JOB_SPINS = 1_000_000            # SimRunner::JOB_SPINS: the simulator splits every call into 1M-spin jobs
WORKER_SHARE = 0.8               # SimRunner uses 80% of the logical CPUs (unless SIM_THREADS is set)
SPIN_LADDER = [1_000_000, 2_000_000, 5_000_000, 10_000_000, 20_000_000, 40_000_000, 100_000_000]
POP_LADDER = [4, 6, 10, 20, 30, 50]
ELITE_COUNT = 2                  # main.ELITE_COUNT
STAGE_NAME = {"base": "BaseGame", "free": "FreeGame"}


def _stage_of(key):
    return next((s for s, pat in STAGES.items() if re.match(pat, key)), None)


def _first(values, default=np.nan):
    return values[0] if values else default


def _sd(stage, spins):
    """Fitness SD of one evaluation with this many spins."""
    return NOISE_SD_10M[stage] * math.sqrt(10_000_000 / spins)


def _floor(stage, spins):
    """Smallest fitness gap two independent evaluations can resolve (95%)."""
    return Z_DIFF_95 * _sd(stage, spins)


def _fmt_spins(n):
    n = int(n)
    return f"{n // 1_000_000}M" if n % 1_000_000 == 0 else f"{n / 1e6:g}M" if n >= 100_000 else f"{n:,}"


def _fmt_t(seconds):
    """Seconds as s / min / h, whichever reads best."""
    if seconds != seconds:
        return "n/a"
    if seconds < 120:
        return f"{seconds:.2f} s" if seconds < 10 else f"{seconds:.0f} s"
    if seconds < 7200:
        return f"{seconds / 60:.1f} min"
    return f"{seconds / 3600:.1f} h"


def load_compute(json_file):
    """
    Timing recorded by the optimizer (all stages in the file). None if the runs predate it.
        exps     one row per experiment (GA combination or baseline) per seed
        stages   one row per stage of a run (seed_<n> / seed_<n>_free -> compute)
        machines {id: description}
    """
    with open(json_file) as f:
        raw = json.load(f)
    exps, stages, machines = [], [], {}
    for seed_key, entry in raw.items():
        stage = _stage_of(seed_key)
        if stage is None:
            continue
        machines.update(entry.get("machines") or {})
        meta = entry.get("meta", {})
        comp = entry.get("compute")
        if comp:
            init = comp.get("initialPopulation") or {}          # only in files from before totalSeconds
            stages.append(dict(stage=stage, seed=seed_key,
                               wall_s=comp.get("totalSeconds", comp.get("stageWallSeconds", np.nan)),
                               init_n=init.get("evaluations", 0), init_s=init.get("seconds", 0.0),
                               pop=meta.get("populationSize"), spins=meta.get("spins"),
                               budget=meta.get("generations")))
        for mut_key, combos in entry.get("results", {}).items():
            mm = re.match(r"^mutation_(\d+)$", mut_key)
            if not mm:
                continue
            for combo_key, e in combos.items():
                t = e.get("timing")
                if not t:
                    continue
                strat, sel = combo_key.split("_", 1)
                strat = strat.replace("ElitismGenerational", "ElistismGenerational")
                fc, st = t.get("finalCheck") or {}, t.get("startEvaluations") or {}
                row = dict(stage=stage, seed=seed_key, mutation=int(mm.group(1)), strategy=strat,
                           selection=sel, is_baseline=sel == BASELINE_TAG, config=_config_label(strat, sel),
                           machine=t.get("machineId"), reused="reusedFrom" in t,
                           evaluations=t.get("evaluations", 0),
                           spins=_first(t.get("spins"), meta.get("spins")), threads=_first(t.get("threads")),
                           search_s=t.get("searchSeconds", 0.0), sim_s=t.get("simSeconds") or np.nan,
                           wall_s=t.get("wallSeconds", np.nan), overhead_s=t.get("overheadSeconds", 0.0),
                           start_s=st.get("seconds", 0.0),
                           final_n=fc.get("evaluations", 0), final_s=fc.get("seconds", 0.0),
                           final_sim_s=fc.get("simSeconds") or np.nan,
                           final_spins=_first(fc.get("spins")), final_threads=_first(fc.get("threads")))
                row["per_eval"] = row["search_s"] / row["evaluations"] if row["evaluations"] else np.nan
                exps.append(row)
    if not exps:
        return None
    stage_cols = ["stage", "seed", "wall_s", "init_n", "init_s",
                  "pop", "spins", "budget"]
    return dict(exps=pd.DataFrame(exps),
                stages=pd.DataFrame(stages, columns=stage_cols), machines=machines)


def _per_eval(exps):
    """Seconds per evaluation over these runs: total search time / total evaluations."""
    n = exps.evaluations.sum()
    return float(exps.search_s.sum() / n) if n else float("nan")


def _main_machine(exps):
    """The machine that did most of the evaluations."""
    return exps.groupby("machine").evaluations.sum().idxmax()


def _machine_name(cc, mid, short=False):
    m = cc["machines"].get(mid, {})
    cpu = (m.get("cpu") or "unknown CPU")
    for junk in ("(R)", "(TM)", " CPU", " Processor", " with Radeon Graphics"):
        cpu = cpu.replace(junk, "")
    cpu = re.sub(r"\s+", " ", cpu).strip()
    if short:
        return f"{cpu[:28]} · {m.get('logicalCpus', '?')} thr"
    return f"{cpu}, {m.get('logicalCpus', '?')} logical CPUs"


def _rounds(spins, workers):
    """How many times in a row each worker runs a 1M-spin job: ceil(jobs / workers)."""
    jobs = math.ceil(spins / JOB_SPINS)
    return math.ceil(jobs / max(1, min(workers, jobs)))


def cost_model(cc, stage, machine):
    """
    Seconds per evaluation as a function of spins N on one machine, in the stage's game mode:
        t(N) = a + jobTime * ceil(jobs(N) / workers(N))
    a        per-call overhead outside the spinning (process start, reelset, JSON), measured
    jobTime  wall time of one round of 1M-spin jobs running in parallel, measured
    workers  min(80% of the logical CPUs, jobs) - what SimRunner uses
    The simulator splits every call into 1M-spin jobs, so time steps up whenever the jobs no
    longer fit in one round of threads. Measured at the run's spins; the steps elsewhere follow
    from the job split (per-job speed is assumed not to change with the number of busy threads).
    """
    g = cc["exps"]
    g = g[(g.stage == stage) & (g.machine == machine) & ~g.reused & (g.evaluations > 0) & g.sim_s.notna()]
    if g.empty:
        return None
    logical = cc["machines"].get(machine, {}).get("logicalCpus") or int(np.nanmax(g.threads))
    cap = max(1, math.floor(logical * WORKER_SHARE))
    if np.nanmax(g.threads) > cap:                      # SIM_THREADS raised the limit
        cap = int(np.nanmax(g.threads))
    a = float(np.median((g.search_s - g.sim_s) / g.evaluations))
    job = float(np.median([r.sim_s / r.evaluations / _rounds(r.spins, int(r.threads)) for r in g.itertuples()]))

    def t(n):
        return a + job * _rounds(n, cap)

    return dict(a=a, job=job, cap=cap, logical=logical, t=t,
                spins=int(g.spins.mode()[0]), threads=int(g.threads.mode()[0]))


def chart10_compute_cost(cc, stage, out_dir):
    """Time per evaluation and per run for each method, and seconds / noise against spins."""
    exps = cc["exps"]
    exps = exps[(exps.stage == stage) & ~exps.reused]
    if exps.empty or not (exps.evaluations > 0).any():
        print("chart 10 skipped: no timing for this stage")
        return None
    machine = _main_machine(exps)
    exps = exps[exps.machine == machine]
    order = [c for c in ([_config_label(s, x) for s in STRATS for x in SELS] +
                         [_config_label(b, BASELINE_TAG) for b in BLS]) if c in set(exps.config)]
    strat_of = exps.groupby("config").strategy.first()
    model = cost_model(cc, stage, machine)

    fig = plt.figure(figsize=(17, max(4.8, 0.42 * len(order) + 1.8)))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.15, 1.15, 1.25], wspace=0.42)
    ax1, ax2, ax3 = fig.add_subplot(gs[0]), fig.add_subplot(gs[1]), fig.add_subplot(gs[2])
    y = np.arange(len(order))[::-1]

    # (a) seconds per evaluation: each run's total search time / its evaluations
    data = [exps[exps.config == c].per_eval.dropna().values for c in order]
    horiz = ({"orientation": "horizontal"} if tuple(map(int, matplotlib.__version__.split(".")[:2])) >= (3, 10)
             else {"vert": False})
    bp = ax1.boxplot(data, positions=y, widths=0.6, **horiz, patch_artist=True, showfliers=False,
                     medianprops=dict(color=INK, lw=1.8), whiskerprops=dict(color=MUTED), capprops=dict(color=MUTED))
    for box, c in zip(bp["boxes"], order):
        col = COLOR.get(strat_of[c], MUTED)
        box.set_facecolor(col); box.set_alpha(0.35); box.set_edgecolor(col)
        if strat_of[c] in BC:
            box.set_hatch("///")
    for yi, c, d in zip(y, order, data):
        if len(d):
            ax1.text(np.percentile(d, 75) * 1.02, yi + 0.33, f"{_per_eval(exps[exps.config == c]):.2f} s",
                     fontsize=7.5, color=INK2)
    ax1.set_yticks(y, order, fontsize=8.5)
    for lab in ax1.get_yticklabels():
        if lab.get_text().startswith("Baseline:"):
            lab.set_fontstyle("italic")
    ax1.grid(axis="y", visible=False)
    spins = int(exps.spins.mode()[0])
    ax1.set_xlabel(f"Seconds per evaluation ({_fmt_spins(spins)} spins; one value per run, label = overall)")
    ax1.set_title("Time per evaluation", loc="left", fontsize=11)

    # (b) minutes per run: search + final check + start + optimizer overhead
    med = exps.groupby("config")[["search_s", "final_s", "start_s", "overhead_s"]].median().reindex(order) / 60
    left = np.zeros(len(order))
    parts = [("search_s", "search (simulator)", 1.0), ("final_s", "final check", 0.55),
             ("start_s", "start population", 0.35), ("overhead_s", "optimizer overhead", 0.15)]
    for col, lab, alpha in parts:
        vals = med[col].fillna(0).values
        if not vals.any():
            continue
        ax2.barh(y, vals, left=left, height=0.6, alpha=alpha, edgecolor="white", lw=0.6,
                 color=[COLOR.get(strat_of[c], MUTED) for c in order], label=lab)
        left += vals
    for yi, tot in zip(y, left):
        ax2.text(tot * 1.01, yi, _fmt_t(tot * 60), va="center", fontsize=7.5, color=INK2)
    ax2.set_yticks(y, [""] * len(order)); ax2.grid(axis="y", visible=False)
    ax2.set_xlim(0, left.max() * 1.22 if left.max() > 0 else 1)
    ax2.set_xlabel(f"Minutes per run (median over seeds, {BUDGET} evaluations)")
    ax2.set_title("Time per run", loc="left", fontsize=11)
    ax2.legend(handles=[Patch(color=MUTED, alpha=a, label=l) for c, l, a in parts if med[c].fillna(0).any()],
               loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2, fontsize=8)

    # (c) seconds per evaluation and noise against spins
    if model:
        ns = np.unique(np.r_[np.geomspace(1e6, 1e8, 60).round(-5), SPIN_LADDER, spins]).astype(int)
        ax3.step(ns, [model["t"](n) for n in ns], where="post", color=INK, lw=2,
                 label=f"time per evaluation (model, {model['cap']} threads)")
        ax3.scatter([spins], [_per_eval(exps)], s=60, color=INK, zorder=4, edgecolor="white",
                    label="measured (run spins)")
        if stage == "free":       # final checks run the full game, as the FreeGame search does
            fcs = exps[exps.final_n > 0]
            if not fcs.empty:
                ax3.scatter(fcs.final_spins, fcs.final_s / fcs.final_n, s=40, marker="D", facecolor="white",
                            edgecolor=INK, zorder=4, label="measured (final checks)")
        ax3.set_xscale("log"); ax3.set_yscale("log")
        ax3.set_xlabel("Spins per evaluation (log)"); ax3.set_ylabel("Seconds per evaluation (log)")
        ax3.axvline(spins, color=MUTED, lw=0.8, ls="--")
        tw = ax3.twinx()
        tw.spines["right"].set_visible(True)
        tw.plot(ns, [_floor(stage, n) for n in ns], color=SC["SteadyState"], lw=2, ls="--",
                label="noise floor: smallest real fitness gap (95%)")
        tw.set_yscale("log"); tw.set_ylabel("Fitness noise floor (log)", color=SC["SteadyState"])
        tw.tick_params(axis="y", colors=SC["SteadyState"]); tw.grid(False)
        h1, l1 = ax3.get_legend_handles_labels(); h2, l2 = tw.get_legend_handles_labels()
        ax3.legend(h1 + h2, l1 + l2, loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=1, fontsize=8)
        ax3.set_title(f"Cost vs precision per evaluation ({STAGE_NAME[stage]})", loc="left", fontsize=11)

    fig.suptitle(f"Computing cost  —  {STAGE_NAME[stage]} stage on {_machine_name(cc, machine)}",
                 x=0.01, ha="left", fontsize=12, color=INK, y=1.02)
    return _save(fig, out_dir, "10_compute_cost")


def _budget_rows(df, curves, mut):
    """Median best-so-far at 25/50/75/100% of the budget for the best GA config and each baseline."""
    rows = []
    best = _best_ga_config(df, mut)
    series = []
    if best:
        series.append((f"GA: {best[0]}", best[1], best[2]))
    series += [(BL[b], b, None) for b in BLS if (df[df.mutation == mut].strategy == b).any()]
    marks = [int(round(BUDGET * q)) for q in (0.25, 0.5, 0.75, 1.0)]
    idx = [int(np.argmin(np.abs(GRID - m))) for m in marks]
    for label, strat, sel in series:
        A = _stack(curves, "best", mut, strat, sel=sel)
        if not len(A):
            continue
        med = np.median(A, 0)
        rows.append(dict(label=label, strategy=strat, med=med, at=[med[i] for i in idx], marks=marks,
                         gain_last=med[idx[2]] - med[idx[3]], n=len(A)))
    return rows


def chart11_budget_population(df, curves, cc, stage, out_dir, mut):
    """What the evaluations buy (error vs evaluations, with hours per run on top) and what
    population size costs and changes at a fixed budget."""
    exps = cc["exps"]
    exps = exps[(exps.stage == stage) & ~exps.reused]
    if exps.empty:
        print("chart 11 skipped: no timing for this stage")
        return None
    machine = _main_machine(exps)
    t_eval = _per_eval(exps[exps.machine == machine])
    spins = int(exps.spins.mode()[0])
    floor = _floor(stage, spins)
    rows = _budget_rows(df, curves, mut)
    st = cc["stages"][cc["stages"].stage == stage]
    pop_now = int(st["pop"].mode()[0]) if st["pop"].notna().any() else 10

    fig, (ax, axp) = plt.subplots(1, 2, figsize=(15, 5), gridspec_kw=dict(width_ratios=[1.35, 1], wspace=0.35))
    for r in rows:
        col = COLOR.get(r["strategy"], INK)
        ls = BLS_LS.get(r["strategy"], "-")
        ax.plot(GRID, r["med"], color=col, lw=2, ls=ls, label=r["label"])
    if rows:
        end = rows[0]["med"][-1]
        ax.axhspan(end, end + floor, color=SC["SteadyState"], alpha=0.10, lw=0)
        ax.text(BUDGET * 0.02, end + floor, f"best GA end + noise floor ({floor:.3g})", fontsize=8,
                color=SC["SteadyState"], va="bottom")
        q3 = int(round(BUDGET * 0.75))
        ax.axvspan(q3, BUDGET, color=MUTED, alpha=0.08, lw=0)
        ax.text(q3 + BUDGET * 0.01, np.max(rows[0]["med"]),
                f"last 25%: −{rows[0]['gain_last']:.3g} error\n{_fmt_t(0.25 * BUDGET * t_eval)} per run",
                fontsize=8, color=INK2, va="top")
    ax.set_yscale("log"); ax.set_xlim(0, BUDGET)
    ax.set_xlabel("Fitness evaluations"); ax.set_ylabel("Best error so far (median over seeds, log)")
    run_s = BUDGET * t_eval
    unit, div = ("hours", 3600) if run_s >= 7200 else ("minutes", 60) if run_s >= 120 else ("seconds", 1)
    top = ax.secondary_xaxis("top", functions=(lambda e: e * t_eval / div, lambda u: u * div / max(t_eval, 1e-9)))
    top.set_xlabel(f"{unit.capitalize()} into one run (at {t_eval:.2f} s per evaluation)", color=INK2)
    ax.legend(loc="upper right", fontsize=8)
    ax.set_title(f"What the budget buys  (mutation {pct(mut)})", loc="left", fontsize=11, pad=34)

    # population: generations per strategy and start-up cost, at this budget
    pops = sorted(set(POP_LADDER + [pop_now]))
    gens = {"SteadyState": [BUDGET] * len(pops),
            "ElistismGenerational": [max(1, BUDGET // max(1, p - ELITE_COUNT)) for p in pops],
            "Generational": [max(1, BUDGET // p) for p in pops]}   # main.generations_for: at least 1
    share = [100 * p / (BUDGET + p) for p in pops]
    axp.bar(range(len(pops)), share, color=MUTED, alpha=0.25, width=0.6, label="start population: % of run cost")
    for i, s in enumerate(share):
        axp.text(i, s, f"{s:.1f}%\n{_fmt_t(pops[i] * t_eval)}", ha="center", va="bottom", fontsize=7.5, color=INK2)
    axp.set_ylabel("Start population, % of a run's evaluations")
    axp.set_ylim(0, max(share) * 1.45)
    tw = axp.twinx(); tw.spines["right"].set_visible(True); tw.grid(False)
    for s in STRATS:
        tw.plot(range(len(pops)), gens[s], color=SC[s], lw=2, marker="o", ms=4, label=f"{SL[s]}: generations")
    tw.set_yscale("log"); tw.set_ylabel(f"Generations in {BUDGET} evaluations (log)")
    axp.set_xticks(range(len(pops)), [f"{p}" + ("\n(used)" if p == pop_now else "") for p in pops])
    axp.set_xlabel("Population size"); axp.grid(axis="x", visible=False)
    h1, l1 = axp.get_legend_handles_labels(); h2, l2 = tw.get_legend_handles_labels()
    axp.legend(h1 + h2, l1 + l2, loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=2, fontsize=8)
    axp.set_title("Population size at a fixed budget", loc="left", fontsize=11, pad=34)
    fig.suptitle(f"Choosing the budget and the population  —  {STAGE_NAME[stage]} stage",
                 x=0.01, ha="left", fontsize=12, color=INK, y=1.04)
    return _save(fig, out_dir, "11_budget_and_population")


def chart12_machines(cc, out_dir):
    """The same work on every machine in the file: seconds per evaluation and throughput per thread."""
    exps = cc["exps"][~cc["exps"].reused & (cc["exps"].evaluations > 0)]
    if exps.machine.nunique() < 2:
        return None
    g = exps.groupby(["machine", "stage", "spins"]).agg(
        evals=("evaluations", "sum"), search_s=("search_s", "sum"), sim_s=("sim_s", "sum"),
        threads=("threads", "median")).reset_index()
    g["per_eval"] = g.search_s / g.evals
    g["spins_per_thread_s"] = g.spins * g.evals / (g.sim_s * g.threads) / 1e6     # million spins
    groups = [(s, n) for s, n in sorted({(r.stage, int(r.spins)) for r in g.itertuples()})]
    machines = list(g.machine.unique())
    palette = SEQ[1::2] + [SC["ElistismGenerational"], SC["Generational"], BC["HillClimbing"]]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 4.6), gridspec_kw=dict(wspace=0.3))
    w = 0.8 / len(machines)
    for k, mid in enumerate(machines):
        for ax, col in ((a1, "per_eval"), (a2, "spins_per_thread_s")):
            vals = [g[(g.machine == mid) & (g.stage == s) & (g.spins == n)][col] for s, n in groups]
            vals = [v.iloc[0] if len(v) else np.nan for v in vals]
            x = np.arange(len(groups)) + (k - (len(machines) - 1) / 2) * w
            ax.bar(x, vals, width=w * 0.95, color=palette[k % len(palette)], label=_machine_name(cc, mid, True))
            for xi, v in zip(x, vals):
                if v == v:
                    ax.text(xi, v, f"{v:.2f}" if col == "per_eval" else f"{v:.2f}M", ha="center",
                            va="bottom", fontsize=7.5, color=INK2)
    labels = [f"{STAGE_NAME[s]}\n{_fmt_spins(n)} spins" for s, n in groups]
    for ax in (a1, a2):
        ax.set_xticks(range(len(groups)), labels); ax.grid(axis="x", visible=False)
    a1.set_ylabel("Seconds per evaluation (lower = faster)")
    a2.set_ylabel("Million spins per second per thread (higher = faster)")
    a1.set_title("Time per evaluation", loc="left", fontsize=11)
    a2.set_title("Speed of one core", loc="left", fontsize=11)
    a1.legend(loc="upper center", bbox_to_anchor=(1.1, -0.16), ncol=min(3, len(machines)), fontsize=8)
    fig.suptitle("Machine comparison  —  the same simulator work on each machine", x=0.01, ha="left",
                 fontsize=12, color=INK, y=1.02)
    return _save(fig, out_dir, "12_machine_comparison")


def compute_report(df, curves, cc, stage, out_dir, mut):
    """compute_report.md: machines, time per evaluation / run / study, and the cost-based case for
    run.spins, run.generations and run.populationSize. Returns the path."""
    allx = cc["exps"]
    exps = allx[(allx.stage == stage) & ~allx.reused]
    machine = _main_machine(exps)
    sev = exps[(exps.machine == machine) & (exps.evaluations > 0)]
    spins = int(exps.spins.mode()[0])
    t_eval = _per_eval(sev)
    model = cost_model(cc, stage, machine)
    st_all = cc["stages"]
    st = st_all[st_all.stage == stage]
    pop_now = int(st["pop"].mode()[0]) if st["pop"].notna().any() else None
    L = [f"# Computing cost ({STAGE_NAME[stage]} stage)", "",
         "Every simulator call the optimizer made was timed (wall time as the optimizer pays it, including starting the simulator and reading its "
         "output). The optimizer stores the total time per method and run, so time per evaluation is total time / evaluations.", ""]

    # ---- machines
    L += ["## Machines", "",
          "| Id | CPU | Cores / logical CPUs | Threads used | Memory | OS | Compiler | Build | Python |",
          "|---|---|---|---|---|---|---|---|---|"]
    used = allx.groupby("machine").threads.agg(lambda s: "/".join(str(int(v)) for v in sorted(set(s.dropna()))))
    for mid, m in cc["machines"].items():
        opt = "" if m.get("optimized") is not False else " **(not optimised)**"
        mem = f"{m['memoryGB']:g} GB" if m.get("memoryGB") else "?"
        L.append(f"| {mid} | {m.get('cpu')} | {m.get('physicalCores') or '?'} / {m.get('logicalCpus')} | "
                 f"{used.get(mid, '?')} | {mem} | {m.get('os')} | {m.get('compiler')} | "
                 f"{m.get('buildType')}{opt} | {m.get('python')} |")
    if any(m.get("optimized") is False for m in cc["machines"].values()):
        L += ["", "> **Warning:** a simulator built without optimisation is several times slower; "
                  "its timings are not representative. Rebuild with `-DCMAKE_BUILD_TYPE=Release`."]
    if allx.machine.nunique() > 1:
        L += ["", f"The tables below use machine **{machine}** (most evaluations); "
                  "12_machine_comparison.png compares the machines."]

    # ---- time per evaluation
    L += ["", "## Time per evaluation", "",
          f"Every evaluation simulates {spins:,} spins "
          f"({'base game only' if stage == 'base' else 'full game'}). Differences between methods come "
          "from the reelsets they propose: reelsets that trigger more free games play more spins.", "",
          "| Method | Runs | Evaluations | Seconds per evaluation | Fastest run | Slowest run |",
          "|---|---|---|---|---|---|"]
    order = [c for c in ([_config_label(s, x) for s in STRATS for x in SELS] +
                         [_config_label(b, BASELINE_TAG) for b in BLS]) if c in set(sev.config)]
    for c in order:
        g = sev[sev.config == c]
        L.append(f"| {c} | {len(g)} | {int(g.evaluations.sum()):,} | {_per_eval(g):.3f} s | "
                 f"{g.per_eval.min():.3f} s | {g.per_eval.max():.3f} s |")
    L.append(f"| **All** | {len(sev)} | {int(sev.evaluations.sum()):,} | **{t_eval:.3f} s** | "
             f"{sev.per_eval.min():.3f} s | {sev.per_eval.max():.3f} s |")
    if model:
        thr = int(model["threads"])
        sps = spins / max(model["job"] * _rounds(spins, thr), 1e-9)
        L += ["", f"That is about {sps / 1e6:.1f}M spins per second on {thr} thread{'s' * (thr != 1)} "
                  f"({sps / thr / 1e6:.2f}M per thread); {model['a'] * 1000:.0f} ms of each call is "
                  "outside the spinning (starting the simulator, reading the reelset, writing the JSON)."]
        jobs = math.ceil(spins / JOB_SPINS)
        w = min(model["cap"], jobs)
        if jobs % w and jobs > w:
            L += ["", f"> **Thread use:** the simulator splits {spins:,} spins into {jobs} jobs of 1M and "
                      f"runs {w} at a time, so it needs {_rounds(spins, w)} rounds and the last one keeps "
                      f"only {jobs % w} thread(s) busy. {w * _rounds(spins, w) - jobs} thread-slots idle: "
                      f"a spin count of {w * (jobs // w) / 1e6:g}M or {w * _rounds(spins, w) / 1e6:g}M "
                      "would use the threads fully, or set SIM_THREADS."]
        elif jobs < model["cap"]:
            L += ["", f"> **Thread use:** {spins:,} spins are {jobs} jobs of 1M, so at most {jobs} of the "
                      f"{model['cap']} threads this machine would use are busy. More cores do not make an "
                      "evaluation at this spin count faster; more spins per evaluation would come almost free "
                      f"up to {model['cap']}M."]

    # ---- time per run
    L += ["", "## Time per run", "",
          f"One run = one method on one seed: {BUDGET} evaluations, plus the final check of its best "
          "reelset. Overhead is the optimizer's own work (selection, files, saving results).", "",
          "| Method | Runs | Wall time | Search | Final check | Overhead |", "|---|---|---|---|---|---|"]
    m_exps = exps[exps.machine == machine]
    for c in order:
        g = m_exps[m_exps.config == c]
        L.append(f"| {c} | {len(g)} | {_fmt_t(g.wall_s.median())} | {_fmt_t(g.search_s.median())} | "
                 f"{_fmt_t(g.final_s.median())} | {_fmt_t(g.overhead_s.median())} "
                 f"({100 * g.overhead_s.sum() / max(g.wall_s.sum(), 1e-9):.1f}%) |")
    if len(st):
        L += ["", f"A whole {STAGE_NAME[stage]} stage of one seed (all {exps.groupby('seed').size().median():.0f} "
                  f"methods, initial population included) took {_fmt_t(st.wall_s.median())} "
                  f"(median over {len(st)} seeds)."]

    # ---- whole study
    L += ["", "## Whole study (every stage in the file)", "",
          "Simulation = time spent in simulator calls; CPU time = simulator time × threads it used; "
          "wall time = the stages' own clocks (includes the optimizer's work).", "",
          "| Stage | Seeds | Runs | Simulator calls | Simulation | CPU time | Wall time |",
          "|---|---|---|---|---|---|---|"]
    tot = dict(seeds=0, runs=0, calls=0, sim=0.0, cpu=0.0, wall=0.0)
    for s in [x for x in STAGES if (allx.stage == x).any()]:
        e = allx[(allx.stage == s) & ~allx.reused]
        sg = st_all[st_all.stage == s]
        calls = int(e.evaluations.sum() + e.final_n.sum() + sg.init_n.sum())
        sim = float(e.search_s.sum() + e.final_s.sum() + e.start_s.sum() + sg.init_s.sum())
        cpu = float(np.nansum(e.sim_s * e.threads) + np.nansum(e.final_sim_s * e.final_threads))
        wall = float(sg.wall_s.sum()) if len(sg) else float(e.wall_s.sum())
        n_seeds = e.seed.nunique()
        L.append(f"| {STAGE_NAME[s]} | {n_seeds} | {len(e)} | {calls:,} | {_fmt_t(sim)} | {_fmt_t(cpu)} | "
                 f"{_fmt_t(wall)} |")
        for k, v in zip(tot, (n_seeds, len(e), calls, sim, cpu, wall)):
            tot[k] += v
    L.append(f"| **Total** | | **{tot['runs']}** | **{tot['calls']:,}** | **{_fmt_t(tot['sim'])}** | "
             f"**{_fmt_t(tot['cpu'])}** | **{_fmt_t(tot['wall'])}** |")
    if (allx.reused).any():
        L += ["", "Random search is run once per seed and saved under every mutation count; the copies "
                  "are not counted."]

    # ---- the case for the settings
    L += ["", "## Choosing the settings", ""]
    best = _best_ga_config(df, mut)
    best_err = float(df[(df.mutation == mut) & (df.config == best[0])].final_best.median()) if best else np.nan
    n_runs = len(exps)

    # spins
    L += [f"### Spins per evaluation (run.spins = {spins:,})", "",
          f"Noise: fitness SD of one evaluation is {NOISE_SD_10M[stage]} at 10M spins ({STAGE_NAME[stage]}, "
          "simulator noise study) and falls as 1/√spins. The noise floor is the smallest fitness "
          "difference two evaluations can resolve (2.77 SD, 95%). Cost: seconds per evaluation from "
          "the model in 10_compute_cost.png, measured at the run's spins.", "",
          f"| Spins | Seconds per evaluation | One run ({BUDGET} evaluations) | This stage's {n_runs} runs | "
          "Fitness SD | Noise floor |", "|---|---|---|---|---|---|"]
    ladder = sorted(set(SPIN_LADDER + [spins]))
    for n in ladder:
        t = model["t"](n) if model else t_eval * n / spins
        star = "**" if n == spins else ""
        L.append(f"| {star}{_fmt_spins(n)}{star} | {t:.2f} s | {_fmt_t(BUDGET * t)} | {_fmt_t(n_runs * BUDGET * t)} | "
                 f"{_sd(stage, n):.4f} | {star}{_floor(stage, n):.4f}{star} |")
    if model:
        low = max(100_000, spins // 10)
        t_now, t_4x, t_10th = model["t"](spins), model["t"](4 * spins), model["t"](low)
        L += ["", f"- **Fewer spins** ({_fmt_spins(low)}): {t_now / t_10th:.1f}× faster, but "
                  f"the noise floor rises to {_floor(stage, low):.3f}"
                  + (f", above the {best_err:.3f} median final error of the best GA configuration: the search "
                     "could no longer tell its late improvements from noise." if best_err == best_err
                     and _floor(stage, low) > best_err else "."),
              f"- **More spins** ({_fmt_spins(4 * spins)}): the floor halves to {_floor(stage, 4 * spins):.3f}, "
              f"but every run takes {t_4x / t_now:.1f}× as long ({_fmt_t(BUDGET * t_now)} → "
              f"{_fmt_t(BUDGET * t_4x)}), and these {n_runs} runs {_fmt_t(n_runs * BUDGET * t_now)} → "
              f"{_fmt_t(n_runs * BUDGET * t_4x)}. That time buys more seeds instead, which the "
              "statistical tests need more.",
              f"- At {_fmt_spins(spins)} the noise floor is {_floor(stage, spins):.3f}"
              + (f" against a best median final error of {best_err:.3f}" if best_err == best_err else "")
              + ". The final check (finalCheckSpins) then measures each best reelset precisely once."]

    # budget
    rows = _budget_rows(df, curves, mut)
    floor = _floor(stage, spins)
    L += ["", f"### Evaluation budget (run.generations = {BUDGET})", "",
          f"Median best-so-far error (mutation {mut}) at each quarter of the budget, and what the last "
          f"quarter bought. Noise floor at {_fmt_spins(spins)} spins: {floor:.3f}. One quarter of a run "
          f"costs {_fmt_t(0.25 * BUDGET * t_eval)} of simulation.", ""]
    if rows:
        L += ["| Method | Seeds | " + " | ".join(f"@{m}" for m in rows[0]["marks"]) +
              " | Last-quarter gain | Above noise floor |", "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['label']} | {r['n']} | " + " | ".join(f"{v:.3g}" for v in r["at"]) +
                 f" | {r['gain_last']:.3g} | {'yes' if r['gain_last'] > floor else 'no'} |")
    if rows:
        g0 = rows[0]
        if g0["gain_last"] > floor:
            L += ["", f"- The best GA configuration still improved by {g0['gain_last']:.3g} in the last "
                      f"{BUDGET // 4} evaluations, more than the noise floor: {BUDGET} is a compute limit, "
                      "not a converged search. Say so in the paper, and report the budget as the cost of one "
                      f"run ({_fmt_t(BUDGET * t_eval)} here)."]
        else:
            L += ["", f"- In the last {BUDGET // 4} evaluations the best GA configuration improved by only "
                      f"{g0['gain_last']:.3g}, below the noise floor of {floor:.3f}: extra evaluations would "
                      f"mostly re-measure noise. Doubling the budget would double every run "
                      f"({_fmt_t(BUDGET * t_eval)} → {_fmt_t(2 * BUDGET * t_eval)}) and this stage "
                      f"({_fmt_t(n_runs * BUDGET * t_eval)} → {_fmt_t(2 * n_runs * BUDGET * t_eval)})."]
        L += ["- In-run errors are the best of many noisy evaluations, so they are biased low (Stats.py "
              "re-evaluates them); the shape of the curve, not its last value, is what matters here."]

    # population
    if pop_now:
        L += ["", f"### Population size (run.populationSize = {pop_now})", "",
              "At a fixed evaluation budget, the population size barely changes the cost: it adds the "
              "start population's evaluations once per run. What it changes is how the budget is spent.", "",
              "| Population | Start population | Share of run | Generations: Steady-state | Elitist | Generational |",
              "|---|---|---|---|---|---|"]
        for p in sorted(set(POP_LADDER + [pop_now])):
            star = "**" if p == pop_now else ""
            L.append(f"| {star}{p}{star} | {_fmt_t(p * t_eval)} | {100 * p / (BUDGET + p):.1f}% | {BUDGET} | "
                     f"{max(1, BUDGET // max(1, p - ELITE_COUNT))} | {max(1, BUDGET // p)} |")
        L += ["", f"- With {pop_now}, the start population costs {100 * pop_now / (BUDGET + pop_now):.1f}% of a run "
                  f"({_fmt_t(pop_now * t_eval)}), and Generational replacement still gets {BUDGET // pop_now} "
                  f"generations ({BUDGET // max(1, pop_now - ELITE_COUNT)} for Elitist). At 50 it would get "
                  f"only {max(1, BUDGET // 50)}, too few to converge, and buying back 100 generations would take "
                  f"{_fmt_t(100 * 50 * t_eval)} per run instead of {_fmt_t(100 * pop_now * t_eval)}.",
              f"- Smaller populations (4-6) save {100 * max(0, pop_now - 4) / (BUDGET + pop_now):.1f}% of a run "
              "or less but leave little diversity for crossover. "
              "The cost does not decide between 6, 10 and 20; a small sensitivity sweep (checklist, priority 3) "
              "would."]
    path = os.path.join(out_dir, "compute_report.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("wrote", path)
    return path


def run_compute(df, curves, json_file, stage, out_dir, mut):
    """Computing-cost charts and report, if the runs recorded timing."""
    cc = load_compute(json_file)
    if cc is None or not (cc["exps"].stage == stage).any():
        print("[compare] no computing-cost data for this stage (runs predate timing capture) - "
              "charts 10-12 and compute_report.md skipped")
        return []
    ex = cc["exps"][(cc["exps"].stage == stage) & ~cc["exps"].reused]
    m = _main_machine(ex)
    g = ex[ex.machine == m]
    print(f"[compare] computing cost: {int(g.evaluations.sum()):,} evaluations in {len(g)} runs, "
          f"{_per_eval(g):.2f} s each on "
          f"{_machine_name(cc, m)}")
    return [chart10_compute_cost(cc, stage, out_dir),
            chart11_budget_population(df, curves, cc, stage, out_dir, mut),
            chart12_machines(cc, out_dir),
            compute_report(df, curves, cc, stage, out_dir, mut)]


# ----------------------------------------------------------------- main
def _report(df, json_file, stage, out_dir):
    """Print what was loaded, so a missing method or stage is obvious before reading charts."""
    seeds = sorted(df.seed.unique(), key=lambda s: int(s.split("_")[1]))
    ga = _ga(df)
    bls = [b for b in BLS if (df.strategy == b).any()]
    print(f"[compare] {json_file} | {stage} game | {len(seeds)} run(s): {', '.join(seeds)}")
    print(f"[compare] budget {BUDGET} evaluations | reelset {REEL_SIZE} stops | "
          f"mutation counts {sorted(int(m) for m in df.mutation.unique())}")
    print(f"[compare] GA configurations: {ga.config.nunique()} | "
          f"baselines: {', '.join(BL[b] for b in bls) or 'none'}")
    if not bls:
        print("[compare] NOTE: no baseline results in this file - the charts show the GA only. "
              "Run the optimizer with baselines.methods set to add them.")
    print(f"[compare] writing charts to {out_dir}/")


def run_all(json_file, out_dir="plots", speed_mutation=5, stage="base"):
    """Draw all report charts for one stage ("base" or "free").
    speed_mutation = mutation count used for charts 4, 9 and 11 (and heatmap sort)."""
    os.makedirs(out_dir, exist_ok=True)
    df, curves = load(json_file, stage)
    _report(df, json_file, stage, out_dir)
    ga = _ga(df)
    rates_src = ga if not ga.empty else df
    all_rates = sorted(rates_src.mutation.unique())
    seeds = sorted(df.seed.unique(), key=lambda s: int(s.split("_")[1]))
    # mutation rates every seed has (fair 5-seed comparisons)
    common = [m for m in all_rates if rates_src[rates_src.mutation == m].seed.nunique() == len(seeds)] or all_rates
    # seeds that have every mutation rate (fair all-rates comparisons)
    full_seeds = [s for s in seeds if set(rates_src[rates_src.seed == s].mutation) == set(all_rates)] or seeds
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
        chart9_ga_vs_baselines(df, curves, out_dir, speed_mutation),
    ]
    out += run_compute(df, curves, json_file, stage, out_dir, speed_mutation)
    return out

run_all("Results/results.json","Results/Graphs",stage="base")
# run_all("Results/results.json","Results/Graphs",stage="free")