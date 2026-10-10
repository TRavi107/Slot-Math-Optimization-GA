"""
GA reelset-tuning report charts.

Reads the save_sim_results JSON layout:
    seed_<S> -> results -> mutation_<M> -> <Replacement>_<Selection> -> results = [[best, mean], ...]
    seed_<S> -> results -> mutation_<M> -> <Method>_Baseline         -> results = [[best, current], ...]

and writes 9 PNGs:
    1_convergence_by_strategy.png   best-so-far vs fitness evaluations, per strategy + baselines (one panel per mutation)
    2_final_error_by_mutation.png   final best error for every mutation rate (GA box + seed dots, baseline dots beside)
    3_heatmap_config_mutation.png   median final error, config x mutation (baselines are rows too)
    4_speed_to_target.png           evaluations needed to reach error <= 0.5 / 0.2 (one mutation rate)
    5_steadystate_by_mutation.png   Steady-state vs hill climbing convergence for each mutation rate
    6_selection_comparison.png      selection method within each strategy, baselines alongside (median + IQR)
    7_best_vs_mean.png              best vs population-mean error over the run (diversity; GA only)
    8_final_best_mean_gap.png       final best vs final mean per strategy x mutation (GA only)
    9_ga_vs_baselines.png           best GA configuration vs each baseline: convergence + per-seed finals

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
                config = (f"Baseline: {BL.get(strat, strat)}" if is_bl
                          else f"{SL.get(strat, strat)} + {SELL.get(sel, sel)}")
                r = dict(seed=seed_key, mutation=mut, strategy=strat, selection=sel,
                         config=config, is_baseline=is_bl,
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
    best_cfg = ga.groupby("config").final_best.median().idxmin()
    bstrat, bsel = ga[ga.config == best_cfg][["strategy", "selection"]].iloc[0]

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
    speed_mutation = mutation count used for charts 4 and 9 (and heatmap sort)."""
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
    return out


def main():
    ap = argparse.ArgumentParser(description="Draw the GA and baseline comparison charts.")
    ap.add_argument("results", nargs="?", default="Results/results.json",
                    help="results file (default: Results/results.json)")
    ap.add_argument("--stage", choices=["auto", "base", "free"], default="auto",
                    help="base = seed_<n> runs, free = seed_<n>_free runs, "
                         "auto = base if the file has any, else free (default)")
    ap.add_argument("--out", default=None,
                    help="output folder (default: Results, or Results/FreeGame for the free stage)")
    ap.add_argument("--mutation", type=int, default=5,
                    help="mutation count used for charts 3, 4 and 9 (default 5)")
    args = ap.parse_args()

    with open(args.results) as f:
        found = stages_in(json.load(f))
    if not found:
        raise SystemExit(f"No runs (seed_<n> or seed_<n>_free) in {args.results}")
    stage = args.stage if args.stage != "auto" else found[0]
    if args.stage == "auto" and len(found) > 1:
        print(f"[compare] file has both stages; charting base. Use --stage free for the free game.")
    out = args.out or ("Results" if stage == "base" else os.path.join("Results", "FreeGame"))
    try:
        run_all(args.results, out, args.mutation, stage)
    except ValueError as e:
        raise SystemExit(f"[compare] {e}")


if __name__ == "__main__":
    main()