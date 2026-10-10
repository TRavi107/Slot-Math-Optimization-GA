
import argparse
import json
import os
import re
from collections import defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LogNorm
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
from matplotlib.ticker import FixedFormatter, FixedLocator, NullLocator

# ----------------------------------------------------------------- labels / colours
ALGO_LABEL = {
    "SteadyState": "Steady-state",
    "Generational": "Generational",
    "ElistismGenerational": "Elitist generational",
    "ElitismGenerational": "Elitist generational",
}
SEL_LABEL = {
    "TournamentSelection": "Tournament",
    "SUS": "SUS",
    "RouletteSelection": "Roulette",
}
PALETTE = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]
TICKS = [0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5,
         1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 5000, 10000]
GRID = np.linspace(0, 100, 201)  # common "run progress %" axis


ALGO_ORDER = ["SteadyState", "Generational", "ElistismGenerational", "ElitismGenerational"]
SEL_ORDER = ["TournamentSelection", "SUS", "RouletteSelection"]


def _ordered(items, order):
    """Sort known names by the preferred order, unknown ones alphabetically after them."""
    return sorted(items, key=lambda x: (order.index(x) if x in order else len(order), x))


def algo_name(a):
    return ALGO_LABEL.get(a, a)


def sel_name(s):
    return SEL_LABEL.get(s, s)


# ----------------------------------------------------------------- loading
SEED_RE = re.compile(r"^seed_(\d+)$")
MUT_RE = re.compile(r"^mutation_(\d+)$")
COMBO_RE = re.compile(r"^(?P<algo>.+)_(?P<sel>[^_]+)$")      # selection = text after the last underscore


DATA_NOTE = ""   # set by load(); stamped on every figure when only part of each run is used


def _select_rows(arr, fraction, part):
    """Keep the first or last `fraction` of a run's rows (at least 1 row)."""
    if fraction >= 1.0:
        return arr
    k = max(1, int(round(len(arr) * fraction)))
    return arr[:k] if part == "first" else arr[-k:]


def _save(fig, path, **kw):
    """savefig that stamps a note when only part of the raw data is used."""
    if DATA_NOTE:
        fig.text(0.995, 0.003, DATA_NOTE, ha="right", va="bottom", fontsize=8, color="#a00")
    fig.savefig(path, **kw)


def load(path, fraction=1.0, part="first"):
    global DATA_NOTE
    if not (0 < fraction <= 1):
        raise ValueError("fraction must be in (0, 1]")
    if part not in ("first", "last"):
        raise ValueError("part must be 'first' or 'last'")
    DATA_NOTE = "" if fraction >= 1 else f"data: {part} {fraction:.0%} of each run's iterations only"
    with open(path) as f:
        raw = json.load(f)
    data = defaultdict(lambda: defaultdict(dict))
    n_runs = 0
    skipped = []
    for seed_key, seed_entry in raw.items():
        ms = SEED_RE.match(seed_key)
        if not ms or not isinstance(seed_entry, dict):
            skipped.append(seed_key)
            continue
        seed = int(ms.group(1))
        for mut_key, combos in seed_entry.get("results", {}).items():
            mm = MUT_RE.match(mut_key)
            if not mm:
                skipped.append(f"{seed_key}/{mut_key}")
                continue
            mut = int(mm.group(1))
            for combo_key, entry in combos.items():
                mc = COMBO_RE.match(combo_key)
                arr = np.asarray(entry.get("results", []), dtype=float)
                if not mc or arr.ndim != 2 or arr.shape[0] == 0 or arr.shape[1] < 2:
                    skipped.append(f"{seed_key}/{mut_key}/{combo_key}")
                    continue
                data[mut][(mc.group("algo"), mc.group("sel"))][seed] = _select_rows(arr[:, :2], fraction, part)
                n_runs += 1
    if skipped:
        shown = ", ".join(skipped[:3]) + (" ..." if len(skipped) > 3 else "")
        print(f"load: skipped {len(skipped)} unrecognised/unusable entries ({shown})")
    if n_runs == 0:
        raise ValueError(f"No runs found in {path}. Expected seed_<S> -> results -> mutation_<M> -> "
                         "<Replacement>_<Selection> -> results (the save_sim_results layout).")
    return data


def _all_seeds(data):
    return sorted({sd for cfgs in data.values() for runs in cfgs.values() for sd in runs})


def _scopes(data, out_dir, per_seed, aggregate):
    """[(folder, seed_or_None)]: seed None = all seeds combined."""
    seeds = _all_seeds(data)
    scopes = []
    if aggregate and len(seeds) > 1:
        scopes.append((os.path.join(out_dir, "overall"), None))
    if per_seed:
        scopes += [(os.path.join(out_dir, f"seed_{sd}"), sd) for sd in seeds]
    return scopes


def _runs_for(cfg_runs, seed):
    """cfg_runs = {seed: array}. Return list of arrays for the scope (all seeds, or one)."""
    if seed is None:
        return [cfg_runs[k] for k in sorted(cfg_runs)]
    return [cfg_runs[seed]] if seed in cfg_runs else []


def _describe(n_seeds, seed, stat, band):
    """Resolve stat/band/subtitle for a scope."""
    if seed is not None:                      # single run: nothing to summarise
        return "geomean", "none", f"seed {seed}"
    few = n_seeds < 5
    s = stat or ("geomean" if few else "median")
    b = band or ("minmax" if few else "iqr")
    band_txt = {"minmax": "min-max", "iqr": "IQR", "std": "±1 std (log)", "none": ""}[b]
    stat_txt = {"geomean": "geometric mean", "mean": "mean", "median": "median"}[s]
    return s, b, f"{stat_txt} of {n_seeds} seeds" + (f", band = {band_txt}" if b != "none" else "")


# ----------------------------------------------------------------- statistics
def resample(arr, col):
    """Interpolate one run onto the common 0-100% progress grid."""
    y = arr[:, col]
    return np.interp(GRID, np.linspace(0, 100, len(y)), y)


def summarise(values, stat, band, axis=0):
    """values: (n_seeds, ...) -> (centre, lo, hi). Log-safe for geomean."""
    v = np.asarray(values, dtype=float)
    v = np.clip(v, 1e-12, None)
    if stat == "geomean":
        centre = np.exp(np.log(v).mean(axis))
    elif stat == "mean":
        centre = v.mean(axis)
    else:
        centre = np.median(v, axis)
    if band == "minmax":
        lo, hi = v.min(axis), v.max(axis)
    elif band == "iqr":
        lo, hi = np.percentile(v, [25, 75], axis=axis)
    elif band == "std":  # std in log space, shown multiplicatively (suits log axes)
        lg = np.log(v)
        s = lg.std(axis)
        c = lg.mean(axis)
        lo, hi = np.exp(c - s), np.exp(c + s)
    else:
        lo = hi = centre
    # keep the centre inside its own band (avoids negative error bars from float
    # rounding with 1 seed, or from e.g. geomean falling outside an IQR)
    lo = np.minimum(lo, centre)
    hi = np.maximum(hi, centre)
    return centre, lo, hi


def curve(runs, col, stat, band):
    stack = np.array([resample(r, col) for r in runs])
    return summarise(stack, stat, band, axis=0)


def finals(runs, col):
    return np.array([r[-1, col] for r in runs])


# ----------------------------------------------------------------- axis formatting
def plain_log_axis(ax, axis="y"):
    """Log scale with plain numbers (0.5, 2, 50) instead of 10^x."""
    ax_ = ax.yaxis if axis == "y" else ax.xaxis
    lo, hi = ax.get_ylim() if axis == "y" else ax.get_xlim()
    t = [v for v in TICKS if lo <= v <= hi]
    ax_.set_major_locator(FixedLocator(t))
    ax_.set_major_formatter(FixedFormatter([f"{v:g}" for v in t]))
    ax_.set_minor_locator(NullLocator())


def ylimits(data_by_cfg, col):
    vals = np.concatenate([r[:, col] for runs in data_by_cfg.values() for r in runs])
    vals = vals[vals > 0]
    return vals.min() * 0.6, vals.max() * 1.6


# ----------------------------------------------------------------- plots
def plot_by_algorithm(cfgs, col, stat, band, ylim, title_metric, prefix, subtitle):
    """ONE PNG per mutation count: one panel per algorithm (replacement type), side by side
    on the same axes, each with all its selection methods as lines.
    Returns [path]."""
    algos = _ordered({a for a, _ in cfgs}, ALGO_ORDER)
    sels = _ordered({s for _, s in cfgs}, SEL_ORDER)
    sel_col = {s: PALETTE[i % len(PALETTE)] for i, s in enumerate(sels)}
    fig, axs = plt.subplots(1, len(algos), figsize=(6 * len(algos), 5.6), sharey=True, squeeze=False)
    for ax, a in zip(axs[0], algos):
        for s in sels:
            if (a, s) not in cfgs:
                continue
            c, lo, hi = curve(cfgs[(a, s)], col, stat, band)
            ax.plot(GRID, c, color=sel_col[s], lw=2, label=sel_name(s))
            if band != "none":
                ax.fill_between(GRID, lo, hi, color=sel_col[s], alpha=0.18)
        ax.set_yscale("log")
        ax.set_ylim(*ylim)
        plain_log_axis(ax)
        ax.grid(alpha=0.3, which="both")
        ax.set_title(algo_name(a), fontsize=12)
        ax.set_xlabel("Run progress (%)")
        ax.legend(title="selection")
    axs[0][0].set_ylabel(f"{title_metric} fitness (log scale)")
    fig.suptitle(f"{title_metric} fitness by replacement type ({subtitle})", fontsize=13)
    fig.tight_layout()
    path = f"{prefix}_by_algorithm.png"
    _save(fig, path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return [path]


def plot_final_bar(cfgs, col, stat, band, title_metric, path, subtitle):
    algos = sorted({a for a, _ in cfgs})
    acol = {a: PALETTE[i % len(PALETTE)] for i, a in enumerate(algos)}
    fin = {k: finals(v, col) for k, v in cfgs.items()}
    summ = {k: summarise(v, stat, band) for k, v in fin.items()}
    order = sorted(fin, key=lambda k: summ[k][0])

    fig, ax = plt.subplots(figsize=(max(9, 1.1 * len(order)), 6.5))
    for i, k in enumerate(order):
        c, lo, hi = summ[k]
        ax.bar(i, c, color=acol[k[0]], alpha=0.5)
        if band != "none" and len(fin[k]) > 1:
            ax.errorbar(i, c, yerr=[[c - lo], [hi - c]], color="k", capsize=4, lw=1)
        ax.scatter(np.full(len(fin[k]), i), fin[k], color="k", s=22, zorder=3)
    allv = np.concatenate(list(fin.values()))
    ax.set_yscale("log")
    ax.set_ylim(allv.min() * 0.6, allv.max() * 1.8)
    plain_log_axis(ax)
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels([f"{algo_name(a)}\n{sel_name(s)}" for a, s in order],
                       rotation=60, ha="right", fontsize=9)
    ax.set_ylabel(f"Final {title_metric.lower()} fitness (log scale)")
    ax.grid(alpha=0.3, axis="y", which="both")
    ax.set_title(f"Final {title_metric.lower()} fitness per config ({subtitle}; dots = individual seeds)")
    ax.legend([Patch(color=acol[a], alpha=0.5) for a in algos], [algo_name(a) for a in algos])
    fig.tight_layout()
    _save(fig, path, dpi=130, bbox_inches="tight")
    plt.close(fig)


# ----------------------------------------------------------------- main function
def _check(stat, band, metric):
    if stat not in (None, "geomean", "mean", "median"):
        raise ValueError("stat must be 'geomean', 'mean', 'median' or None")
    if band not in (None, "minmax", "iqr", "std", "none"):
        raise ValueError("band must be 'minmax', 'iqr', 'std', 'none' or None")
    if metric not in ("best", "mean"):
        raise ValueError("metric must be 'best' or 'mean'")


def plot_ga_results(json_file, out_dir="plots", stat=None, band=None, metric="best",
                    mutation=None, per_seed=True, aggregate=True, fraction=1.0, part="first"):
    _check(stat, band, metric)
    data = load(json_file, fraction, part)
    col = 0 if metric == "best" else 1
    mtitle = "Best" if metric == "best" else "Mean"
    written = []

    for folder, seed in _scopes(data, out_dir, per_seed, aggregate):
        os.makedirs(folder, exist_ok=True)
        for mut, cfgs_raw in sorted(data.items()):
            if mutation is not None and mut != mutation:
                continue
            cfgs = {k: _runs_for(v, seed) for k, v in cfgs_raw.items()}
            cfgs = {k: v for k, v in cfgs.items() if v}
            if not cfgs:
                continue
            n_seeds = min(len(v) for v in cfgs.values())
            s, b, subtitle = _describe(n_seeds, seed, stat, band)
            ylim = ylimits(cfgs, col)
            prefix = os.path.join(folder, f"mut{mut}_{metric}")
            written += plot_by_algorithm(cfgs, col, s, b, ylim, mtitle, prefix, subtitle)
            p3 = f"{prefix}_final_best_bar.png"
            plot_final_bar(cfgs, col, s, b, mtitle, p3, subtitle)
            written.append(p3)
        print(f"{folder}: done")
    return written


# ----------------------------------------------------------------- compare mutation counts
def _pivot_by_config(cfgs_by_mut, seed):
    """{mut: {cfg: {seed: arr}}} -> {cfg: {mut: [arrays]}} for the scope."""
    out = defaultdict(dict)
    for mut, cfgs in cfgs_by_mut.items():
        for cfg, runs in cfgs.items():
            r = _runs_for(runs, seed)
            if r:
                out[cfg][mut] = r
    return out


def _resolve_configs(config, available):
    """Accept None, 'Algo_Selection', ('Algo','Selection') or a list of those."""
    if config is None:
        return list(available)
    items = [config] if isinstance(config, (str, tuple)) and not (
        isinstance(config, list)) else list(config)
    out = []
    for c in items:
        if isinstance(c, str):
            a, s_ = c.split("_", 1)
            c = (a, s_)
        if c not in available:
            raise ValueError(f"config {c} not found. Available: {sorted(available)}")
        out.append(tuple(c))
    return out


def compare_mutations(json_file, out_dir="plots", config=None, stat=None, band=None,
                      metric="best", per_seed=True, aggregate=True, min_mutations=1, fraction=1.0, part="first"):
    
    _check(stat, band, metric)
    data = load(json_file, fraction, part)
    col = 0 if metric == "best" else 1
    mtitle = "Best" if metric == "best" else "Mean"
    written = []

    for folder, seed in _scopes(data, out_dir, per_seed, aggregate):
        pivot = _pivot_by_config(data, seed)
        multi = {c: m for c, m in pivot.items() if len(m) >= min_mutations}
        if not multi:
            print(f"{folder}: no config has {min_mutations}+ mutation counts - skipped")
            continue
        selected = _resolve_configs(config, multi.keys())
        os.makedirs(folder, exist_ok=True)

        # one PNG per algorithm; one panel per selection method; one line per mutation count
        for algo in sorted({c[0] for c in selected}):
            cfgs_a = sorted([c for c in selected if c[0] == algo],
                             key=lambda c: (SEL_ORDER.index(c[1]) if c[1] in SEL_ORDER else len(SEL_ORDER), c[1]))
            all_muts = sorted({m for c in cfgs_a for m in multi[c]})
            mcol = {m: PALETTE[i % len(PALETTE)] for i, m in enumerate(all_muts)}
            allvals = np.concatenate([r[:, col] for c in cfgs_a for m in multi[c] for r in multi[c][m]])
            allvals = allvals[allvals > 0]

            fig, axs = plt.subplots(1, len(cfgs_a), figsize=(6 * len(cfgs_a), 5.5), sharey=True, squeeze=False)
            n_all = []
            for ax, cfg in zip(axs[0], cfgs_a):
                by_mut = multi[cfg]
                n_seeds = min(len(by_mut[m]) for m in by_mut)
                n_all.append(n_seeds)
                s_, b_, _ = _describe(n_seeds, seed, stat, band)
                for m in sorted(by_mut):
                    c, lo, hi = curve(by_mut[m], col, s_, b_)
                    ax.plot(GRID, c, color=mcol[m], lw=2, label=f"mutation = {m}")
                    if b_ != "none":
                        ax.fill_between(GRID, lo, hi, color=mcol[m], alpha=0.18)
                ax.set_yscale("log"); ax.set_ylim(allvals.min() * 0.6, allvals.max() * 1.6); plain_log_axis(ax)
                ax.grid(alpha=0.3, which="both")
                ax.set_xlabel("Run progress (%)")
                ax.set_title(sel_name(cfg[1]))
                ax.legend(title="mutation count", fontsize=8)
            axs[0][0].set_ylabel(f"{mtitle} fitness (log scale)")
            _, _, subtitle = _describe(min(n_all), seed, stat, band)
            if len(all_muts) == 1:   # this scope only has one mutation count: nothing to compare against
                head = f"{algo_name(algo)}: mutation {all_muts[0]} only"
            else:
                head = f"{algo_name(algo)}: effect of mutation count"
            fig.suptitle(f"{head} ({subtitle})", fontsize=13)
            fig.tight_layout()
            path = os.path.join(folder, f"{algo}_{metric}_mutation_compare.png")
            _save(fig, path, dpi=130, bbox_inches="tight")
            plt.close(fig)
            written.append(path)
        print(f"{folder}: {len(selected)} configs")
    return written


# ----------------------------------------------------------------- best config + best mutation (one diagram)
def best_config_and_mutation(json_file, out_dir="plots", stat=None, band=None, metric="best",
                             per_seed=True, aggregate=True, fraction=1.0, part="first"):
    
    from matplotlib.colors import LogNorm
    
    _check(stat, band, metric)
    data = load(json_file, fraction, part)
    col = 0 if metric == "best" else 1
    mtitle = "best" if metric == "best" else "mean"
    written = []

    for folder, seed in _scopes(data, out_dir, per_seed, aggregate):
        muts = sorted(data)
        cfg_all = sorted({c for m in muts for c in data[m]})
        n_seeds = min(len(_runs_for(r, seed)) for m in muts for r in data[m].values() if _runs_for(r, seed)) \
            if any(_runs_for(r, seed) for m in muts for r in data[m].values()) else 0
        if n_seeds == 0:
            continue
        s_, b_, subtitle = _describe(n_seeds, seed, stat, band)

        val = np.full((len(cfg_all), len(muts)), np.nan)
        lo = val.copy(); hi = val.copy()
        for i, cfg in enumerate(cfg_all):
            for j, m in enumerate(muts):
                runs = _runs_for(data[m].get(cfg, {}), seed)
                if runs:
                    c, l, h = summarise(finals(runs, col), s_, b_ if b_ != "none" else "minmax")
                    val[i, j], lo[i, j], hi[i, j] = float(c), float(l), float(h)

        keep = ~np.all(np.isnan(val), axis=0)          # drop mutation counts this scope has no runs for
        val, lo, hi = val[:, keep], lo[:, keep], hi[:, keep]
        muts_s = [m for m, k in zip(muts, keep) if k]
        best_per_cfg = np.nanmin(val, axis=1)
        order = np.argsort(best_per_cfg)
        val, lo, hi = val[order], lo[order], hi[order]
        cfg_sorted = [cfg_all[k] for k in order]
        col_overall = np.array([np.exp(np.nanmean(np.log(val[:, j]))) for j in range(len(muts_s))])

        nR, nC = len(cfg_sorted), len(muts_s)
        fig, ax = plt.subplots(figsize=(1.6 * (nC + 2) + 3, 0.65 * (nR + 1) + 2.2))
        cmap = plt.get_cmap("RdYlGn_r")
        allv = val.ravel()
        norm = LogNorm(vmin=np.nanmin(allv), vmax=np.nanmax(allv))

        def cell(r, c, text, sub, v, bold=False):
            rgb = cmap(norm(v))
            ax.add_patch(Rectangle((c, r), 1, 1, facecolor=rgb, edgecolor="white", lw=2))
            lum = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
            tc = "white" if lum < 0.5 else "black"          # readable on dark and light cells
            ax.text(c + .5, r + .45 if sub else r + .5, text, ha="center", va="center",
                    fontsize=10.5, fontweight="bold" if bold else "normal", color=tc)
            if sub:
                ax.text(c + .5, r + .75, sub, ha="center", va="center", fontsize=7.5, color=tc)

        show_range = b_ != "none" and n_seeds > 1
        for i in range(nR):
            for j in range(nC):
                v = val[i, j]
                if np.isnan(v):
                    ax.add_patch(Rectangle((j, i), 1, 1, facecolor="#eee", edgecolor="white", lw=2))
                    continue
                cell(i, j, f"{v:.3g}", f"{lo[i, j]:.2g}–{hi[i, j]:.2g}" if show_range else "", v)
            jb = int(np.nanargmin(val[i]))                       # best mutation of this config
            ax.add_patch(Rectangle((jb + .04, i + .04), .92, .92, fill=False, edgecolor="white", lw=2.5, zorder=3))
            ax.add_patch(Rectangle((jb, i), 1, 1, fill=False, edgecolor="#222", lw=1, zorder=3))
            # last column: best value + which mutation
            cell(i, nC, f"{val[i, jb]:.3g}", f"mutation {muts_s[jb]}", val[i, jb], bold=True)
        jbo = int(np.argmin(col_overall))      # best mutation overall (named in the title only)
        # best cell overall
        ib, jb = np.unravel_index(np.nanargmin(val), val.shape)
        ax.add_patch(Rectangle((jb, ib), 1, 1, fill=False, edgecolor="black", lw=3.5, zorder=4))

        ax.set_xlim(0, nC + 1); ax.set_ylim(nR, 0)
        ax.set_xticks([j + .5 for j in range(nC + 1)])
        ax.set_xticklabels([f"mutation {m}" for m in muts_s] + ["best"], fontsize=10)
        ax.xaxis.tick_top()
        ax.set_yticks([i + .5 for i in range(nR)])
        ax.set_yticklabels([f"{algo_name(a)} + {sel_name(sl)}" for a, sl in cfg_sorted], fontsize=10)
        ax.tick_params(length=0)
        for sp in ax.spines.values():
            sp.set_visible(False)
        sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
        cb = fig.colorbar(sm, ax=ax, fraction=0.03, pad=0.02)
        cb.set_label(f"final {mtitle} fitness (log scale, lower = better)")
        cb.set_ticks([t for t in TICKS if norm.vmin <= t <= norm.vmax])
        cb.set_ticklabels([f"{t:g}" for t in TICKS if norm.vmin <= t <= norm.vmax])
        best_cfg = cfg_sorted[0]
        fig.suptitle(
            f"Best config: {algo_name(best_cfg[0])} + {sel_name(best_cfg[1])} | "
            f"best mutation overall: {muts_s[jbo]}\n({subtitle}; black box = best cell, white box = best mutation per config)",
            fontsize=12, y=1.0)
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, f"{metric}_best_config_mutation.png")
        _save(fig, path, dpi=130, bbox_inches="tight")
        plt.close(fig)
        written.append(path)
        print(f"{folder}: done")
    return written


# ----------------------------------------------------------------- overall result diagrams
def overall_diagrams(json_file, out_dir="plots", stat="geomean", metric="best", fraction=1.0, part="first"):
    
    from matplotlib.colors import LogNorm
    
    if stat not in ("geomean", "mean", "median"):
        raise ValueError("stat must be 'geomean', 'mean' or 'median'")
    _check(None, None, metric)
    data = load(json_file, fraction, part)
    col = 0 if metric == "best" else 1
    mtitle = "best" if metric == "best" else "mean"
    stat_txt = {"geomean": "geometric mean", "mean": "mean", "median": "median"}[stat]
    muts = sorted(data)
    cfgs = sorted({c for m in muts for c in data[m]})
    algos = sorted({a for a, _ in cfgs})
    sels = sorted({sl for _, sl in cfgs})
    acol = {a: PALETTE[i % len(PALETTE)] for i, a in enumerate(algos)}
    scol = {sl: PALETTE[i % len(PALETTE)] for i, sl in enumerate(sels)}
    folder = os.path.join(out_dir, "overall")
    os.makedirs(folder, exist_ok=True)
    lab = lambda c: f"{algo_name(c[0])} + {sel_name(c[1])}"

    def fin(cfg, m):
        runs = data[m].get(cfg, {})
        return finals([runs[k] for k in sorted(runs)], col) if runs else np.array([])

    def avg(v):
        return float(summarise(v, stat, "none")[0])

    n_seeds = {m: max(len(fin(c, m)) for c in cfgs) for m in muts}
    seed_txt = lambda m: f"{n_seeds[m]} seed" + ("s" if n_seeds[m] != 1 else "")
    allv = np.concatenate([fin(c, m) for c in cfgs for m in muts if len(fin(c, m))])
    allv = allv[allv > 0]
    lo_, hi_ = allv.min() * 0.6, allv.max() * 1.8
    V = np.array([[avg(fin(c, m)) if len(fin(c, m)) else np.nan for m in muts] for c in cfgs])
    written = []

    # ---- 1) overview heatmap
    order = np.argsort(np.nanmin(V, axis=1))
    Vs, cs = V[order], [cfgs[i] for i in order]
    fig, ax = plt.subplots(figsize=(max(7.5, 2.6 * len(muts) + 3.5), 0.65 * len(cs) + 2))
    cmap = plt.get_cmap("RdYlGn_r")
    norm = LogNorm(vmin=np.nanmin(Vs), vmax=np.nanmax(Vs))
    for i in range(len(cs)):
        for j in range(len(muts)):
            v = Vs[i, j]
            if np.isnan(v):
                ax.add_patch(Rectangle((j, i), 1, 1, facecolor="#eee", edgecolor="white", lw=2))
                continue
            rgb = cmap(norm(v))
            tc = "white" if (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) < 0.5 else "black"
            ax.add_patch(Rectangle((j, i), 1, 1, facecolor=rgb, edgecolor="white", lw=2))
            ax.text(j + .5, i + .5, f"{v:.3g}", ha="center", va="center", color=tc, fontsize=11)
    for j in range(len(muts)):
        if np.all(np.isnan(Vs[:, j])):
            continue
        ib = int(np.nanargmin(Vs[:, j]))
        ax.add_patch(Rectangle((j + .03, ib + .03), .94, .94, fill=False, edgecolor="black", lw=3, zorder=3))
    ax.set_xlim(0, len(muts)); ax.set_ylim(len(cs), 0); ax.xaxis.tick_top()
    ax.set_xticks([j + .5 for j in range(len(muts))])
    ax.set_xticklabels([f"mutation {m}\n({seed_txt(m)})" for m in muts])
    ax.set_yticks([i + .5 for i in range(len(cs))]); ax.set_yticklabels([lab(c) for c in cs])
    ax.tick_params(length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax, fraction=0.04, pad=0.03)
    cb.set_label(f"final {mtitle} fitness ({stat_txt} over seeds, lower = better)")
    t = [x for x in TICKS if norm.vmin <= x <= norm.vmax]
    cb.set_ticks(t); cb.set_ticklabels([f"{x:g}" for x in t])
    fig.suptitle("Overview: config x mutation count (black box = best config for that mutation)", fontsize=11.5, y=0.99)
    path = os.path.join(folder, f"{metric}_overview_heatmap.png")
    _save(fig, path, dpi=130, bbox_inches="tight"); plt.close(fig); written.append(path)

    # ---- 2) ranking within each mutation count
    fig, axs = plt.subplots(1, len(muts), figsize=(7.2 * len(muts), 0.5 * len(cfgs) + 2.8), sharex=True, squeeze=False)
    for ax, m in zip(axs[0], muts):
        rows = [(c, fin(c, m)) for c in cfgs if len(fin(c, m))]
        rows.sort(key=lambda r: avg(r[1]), reverse=True)
        for i, (c, v) in enumerate(rows):
            top = i == len(rows) - 1
            ax.barh(i, avg(v), color=acol[c[0]], alpha=0.55)
            ax.scatter(v, np.full(len(v), i), color="k", s=20, zorder=3)
            ax.text(avg(v) * 1.08, i - .28, ("★ " if top else "") + f"{avg(v):.3g}", fontsize=9 if top else 8.5,
                    va="center", fontweight="bold" if top else "normal")
        ax.set_yticks(range(len(rows))); ax.set_yticklabels([lab(c) for c, _ in rows], fontsize=9)
        ax.set_xscale("log"); ax.set_xlim(lo_, hi_); plain_log_axis(ax, "x")
        ax.grid(alpha=0.3, axis="x", which="both")
        ax.set_title(f"mutation = {m}  ({seed_txt(m)})   ★ = best")
        ax.set_xlabel(f"final {mtitle} fitness (log)")
    fig.legend([Patch(color=acol[a], alpha=0.55) for a in algos], [algo_name(a) for a in algos],
               loc="lower center", ncol=len(algos), frameon=False, bbox_to_anchor=(.5, -.02))
    fig.suptitle(f"Ranking of configs within each mutation count (bar = {stat_txt} over seeds, dots = seeds)", fontsize=11.5)
    fig.tight_layout(rect=[0, .04, 1, 1])
    path = os.path.join(folder, f"{metric}_ranking_per_mutation.png")
    _save(fig, path, dpi=130, bbox_inches="tight"); plt.close(fig); written.append(path)

    # ---- 3) effect of mutation count per replacement type
    if len(muts) >= 2:
        fig, axs = plt.subplots(1, len(algos), figsize=(5.4 * len(algos), 5), sharey=True, squeeze=False)
        for ax, a in zip(axs[0], algos):
            for k, sl in enumerate(sels):
                c = (a, sl)
                xs = [j for j, m in enumerate(muts) if len(fin(c, m))]
                if not xs:
                    continue
                ax.plot(xs, [avg(fin(c, muts[j])) for j in xs], "-o", color=scol[sl], lw=2, ms=8, label=sel_name(sl))
                for j in xs:
                    v = fin(c, muts[j])
                    ax.scatter(np.full(len(v), j + .04 * (k - 1)), v, color=scol[sl], s=14, alpha=.5, edgecolor="k", lw=.3)
            ax.set_yscale("log"); ax.set_ylim(lo_, hi_); plain_log_axis(ax)
            ax.grid(alpha=0.3, which="both")
            ax.set_xticks(range(len(muts))); ax.set_xticklabels([str(m) for m in muts])
            ax.set_xlim(-.4, len(muts) - .6)
            ax.set_xlabel("mutation count"); ax.set_title(algo_name(a)); ax.legend(title="selection", fontsize=8)
        axs[0][0].set_ylabel(f"{stat_txt} final {mtitle} fitness (log)")
        fig.suptitle(f"Effect of mutation count on each algorithm (line = {stat_txt} over seeds, small dots = seeds)", fontsize=11.5)
        fig.tight_layout()
        path = os.path.join(folder, f"{metric}_mutation_effect.png")
        _save(fig, path, dpi=130, bbox_inches="tight"); plt.close(fig); written.append(path)
    print(f"{folder}: overall diagrams done ({len(written)} files)")
    return written


def best_mean_gap(json_file, out_dir="plots", stat="geomean", band=None, mutation=None, fraction=1.0, part="first"):
    
    _check(stat, band, "best")
    data = load(json_file, fraction, part)
    folder = os.path.join(out_dir, "overall")
    os.makedirs(folder, exist_ok=True)
    written = []
    for mut, cfgs_raw in sorted(data.items()):
        if mutation is not None and mut != mutation:
            continue
        cfgs = {}
        for cfg, runs in cfgs_raw.items():
            arrs = []
            for k in sorted(runs):
                r = runs[k]
                gap = np.clip(r[:, 1] - r[:, 0], 1e-9, None)       # mean - best, kept positive for log axis
                arrs.append(np.column_stack([gap, gap]))
            cfgs[cfg] = arrs
        n_seeds = min(len(v) for v in cfgs.values())
        if n_seeds == 1:
            s_, b_, subtitle = stat, "none", "single seed"
        else:
            s_, b_, subtitle = _describe(n_seeds, None, stat, band)
        algos = _ordered({a for a, _ in cfgs}, ALGO_ORDER)
        sels = _ordered({sl for _, sl in cfgs}, SEL_ORDER)
        scol = {sl: PALETTE[i % len(PALETTE)] for i, sl in enumerate(sels)}
        curves = {cfg: curve(v, 0, s_, b_) for cfg, v in cfgs.items()}
        # y-range from the average lines, so a single outlier generation in one seed cannot
        # squash the plot (its band is clipped instead, and flagged below)
        ylim = (min(np.min(c[1]) for c in curves.values()) * 0.6,
                max(np.max(c[0]) for c in curves.values()) * 2.0)
        clipped = any(np.max(c[2]) > ylim[1] for c in curves.values())
        fig, axs = plt.subplots(1, len(algos), figsize=(6 * len(algos), 5.6), sharey=True, squeeze=False)
        for ax, a in zip(axs[0], algos):
            for sl in sels:
                if (a, sl) not in cfgs:
                    continue
                c, lo, hi = curves[(a, sl)]
                ax.plot(GRID, c, color=scol[sl], lw=2, label=sel_name(sl))
                if b_ != "none":
                    ax.fill_between(GRID, lo, hi, color=scol[sl], alpha=0.18)
            ax.set_yscale("log"); ax.set_ylim(*ylim); plain_log_axis(ax)
            ax.grid(alpha=0.3, which="both")
            ax.set_title(algo_name(a), fontsize=12)
            ax.set_xlabel("Run progress (%)")
            ax.legend(title="selection")
        axs[0][0].set_ylabel("Mean − best fitness (log scale)")
        fig.suptitle(f"Mutation {mut}: population gap (mean − best) over the run ({subtitle})", fontsize=13)
        fig.tight_layout()
        if clipped:
            fig.text(0.995, 0.005, "note: seed-spread band clipped at top (outlier generation in one seed)",
                     ha="right", va="bottom", fontsize=8, color="#555")
        path = os.path.join(folder, f"mut{mut}_gap_by_algorithm.png")
        _save(fig, path, dpi=130, bbox_inches="tight"); plt.close(fig); written.append(path)
    print(f"{folder}: gap diagrams done ({len(written)} files)")
    return written


ALGO_COLOUR = {"SteadyState": "#1f77b4", "Generational": "#d62728",
               "ElistismGenerational": "#2ca02c", "ElitismGenerational": "#2ca02c"}


def best_vs_mean_diagram(json_file, out_dir="plots", stat="geomean", fraction=1.0, part="first"):
    
    from matplotlib.lines import Line2D

    if stat not in ("geomean", "mean", "median"):
        raise ValueError("stat must be 'geomean', 'mean' or 'median'")
    data = load(json_file, fraction, part)
    muts = sorted(data)
    cfgs = sorted({c for m in muts for c in data[m]},
                  key=lambda c: (ALGO_ORDER.index(c[0]) if c[0] in ALGO_ORDER else len(ALGO_ORDER), c[0],
                                 SEL_ORDER.index(c[1]) if c[1] in SEL_ORDER else len(SEL_ORDER), c[1]))
    algos = _ordered({a for a, _ in cfgs}, ALGO_ORDER)
    fallback = {a: PALETTE[i % len(PALETTE)] for i, a in enumerate(algos)}
    colour = lambda a: ALGO_COLOUR.get(a, fallback[a])
    stat_txt = {"geomean": "geometric mean", "mean": "mean", "median": "median"}[stat]

    def fin(cfg, m, col):
        runs = data[m].get(cfg, {})
        return finals([runs[k] for k in sorted(runs)], col) if runs else np.array([])

    avg = lambda v: float(summarise(v, stat, "none")[0])
    allv = np.concatenate([fin(c, m, k) for c in cfgs for m in muts for k in (0, 1) if len(fin(c, m, k))])
    allv = allv[allv > 0]
    lo, hi = allv.min() * 0.5, allv.max() * 2.2

    fig, axs = plt.subplots(1, len(muts), figsize=(8 * len(muts), 0.5 * len(cfgs) + 2.6),
                            sharex=True, squeeze=False)
    for ax, m in zip(axs[0], muts):
        rows = [(c, avg(fin(c, m, 0)), avg(fin(c, m, 1))) for c in cfgs if len(fin(c, m, 0))]
        rows.sort(key=lambda r: r[1], reverse=True)          # best config at the top
        for i, (c, b, mn) in enumerate(rows):
            col_ = colour(c[0])
            ax.plot([b, mn], [i, i], color=col_, lw=2.5, alpha=0.5, zorder=1)
            ax.scatter(b, i, s=70, color=col_, edgecolor="k", zorder=3)
            ax.scatter(mn, i, s=70, facecolor="white", edgecolor=col_, lw=2, zorder=3)
            ax.text(max(b, mn) * 1.12, i, f"mean = {mn / b:.1f}× best", fontsize=8.5, va="center", color="#444")
        ax.set_yticks(range(len(rows)))
        ax.set_yticklabels([f"{algo_name(c[0])} + {sel_name(c[1])}" for c, _, _ in rows], fontsize=9)
        ax.set_xscale("log"); ax.set_xlim(lo, hi); plain_log_axis(ax, "x")
        ax.grid(alpha=0.3, axis="x", which="both")
        n = max(len(fin(c, m, 0)) for c in cfgs)
        ax.set_title(f"mutation = {m}  ({n} seed{'s' if n != 1 else ''})")
        ax.set_xlabel(f"final fitness (log scale, {stat_txt} over seeds)")
    handles = [Line2D([0], [0], marker="o", color="w", markerfacecolor="gray", markeredgecolor="k", markersize=9),
               Line2D([0], [0], marker="o", color="w", markerfacecolor="white", markeredgecolor="gray",
                      markeredgewidth=2, markersize=9)]
    handles += [Line2D([0], [0], color=colour(a), lw=3) for a in algos]
    labels = ["best fitness", "mean (population) fitness"] + [algo_name(a) for a in algos]
    fig.legend(handles, labels, loc="lower center", ncol=len(labels), frameon=False, bbox_to_anchor=(.5, -.01))
    fig.suptitle("Best vs mean fitness at the end of the run (small gap = converged population, large gap = diverse)",
                 fontsize=11.5)
    fig.tight_layout(rect=[0, .05, 1, .97])
    folder = os.path.join(out_dir, "overall")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, "best_vs_mean.png")
    _save(fig, path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"{folder}: best_vs_mean done")
    return [path]


def best_mean_vs_generation(json_file, out_dir="plots", stat="geomean", x="auto", y_cap_percentile=98, fraction=1.0, part="first"):
    
    if stat not in ("geomean", "mean", "median"):
        raise ValueError("stat must be 'geomean', 'mean' or 'median'")
    if x not in ("auto", "generation", "progress"):
        raise ValueError("x must be 'auto', 'generation' or 'progress'")
    data = load(json_file, fraction, part)
    muts = sorted(data)
    algos = _ordered({a for m in muts for a, _ in data[m]}, ALGO_ORDER)
    sels = _ordered({sl for m in muts for _, sl in data[m]}, SEL_ORDER)
    scol = {sl: PALETTE[i % len(PALETTE)] for i, sl in enumerate(sels)}
    stat_txt = {"geomean": "geometric mean", "mean": "mean", "median": "median"}[stat]
    folder = os.path.join(out_dir, "overall")
    os.makedirs(folder, exist_ok=True)
    written = []

    for a in algos:
        def runs_of(m, sl):
            r = data[m].get((a, sl), {})
            return [r[k] for k in sorted(r)]

        all_runs = [r for m in muts for sl in sels for r in runs_of(m, sl)]
        if not all_runs:
            continue
        same_len = len({len(r) for r in all_runs}) == 1
        if x == "generation" and not same_len:
            raise ValueError(f"{algo_name(a)}: runs have different lengths, cannot use x='generation'")
        use_gen = (x == "generation") or (x == "auto" and same_len)
        xs = np.arange(1, len(all_runs[0]) + 1) if use_gen else GRID
        xlabel = "Generation" if use_gen else "Run progress (%)"

        def series(runs, col):
            if use_gen:
                stack = np.array([r[:, col] for r in runs])
                return summarise(stack, stat, "none", axis=0)[0]
            return curve(runs, col, stat, "none")[0]

        curves = {}   # (mut, sel) -> (best, mean)
        for m in muts:
            for sl in sels:
                r = runs_of(m, sl)
                if r:
                    curves[(m, sl)] = (series(r, 0), series(r, 1))
        vals = np.concatenate([np.concatenate(v) for v in curves.values()])
        vals = vals[vals > 0]
        best_all = np.concatenate([v[0] for v in curves.values()])
        lo = best_all[best_all > 0].min() * 0.7
        start = max(float(v[0][0]) for v in curves.values())
        start = max(start, max(float(v[1][0]) for v in curves.values()))
        hi = np.percentile(vals, y_cap_percentile) * 1.5
        if y_cap_percentile >= 100:
            hi = vals.max() * 1.3
        hi = max(hi, start * 1.3, lo * 3)          # never crop the starting values

        ncols = min(len(muts), 4)
        nrows = int(np.ceil(len(muts) / ncols))
        fig, axs = plt.subplots(nrows, ncols, figsize=(6.2 * ncols, 5 * nrows + 0.8),
                                sharex=True, sharey=True, squeeze=False)
        for idx, m in enumerate(muts):
            ax = axs[idx // ncols][idx % ncols]
            peak = 0.0
            for sl in sels:
                if (m, sl) not in curves:
                    continue
                b, mn = curves[(m, sl)]
                ax.plot(xs, b, color=scol[sl], lw=2.2)
                ax.plot(xs, mn, color=scol[sl], lw=1.5, ls="--")
                skip = max(1, len(xs) // 20)          # ignore the first 5%: that is the normal starting level
                peak = max(peak, float(mn[skip:].max()), float(b[skip:].max()))
            ax.set_yscale("log"); ax.set_ylim(lo, hi); plain_log_axis(ax)
            ax.grid(alpha=0.3, which="both")
            if peak > hi:
                ax.text(.99, .97, f"spike off-scale (peak ~ {peak:,.0f})", transform=ax.transAxes, ha="right",
                        va="top", fontsize=8.5, color="#a00", bbox=dict(fc="white", ec="#a00", lw=.6, pad=2))
            n = max(len(runs_of(m, sl)) for sl in sels)
            ax.set_title(f"mutation = {m}  ({n} seed{'s' if n != 1 else ''})", fontsize=11)
            if idx % ncols == 0:
                ax.set_ylabel("Fitness (log scale)")
            if idx // ncols == nrows - 1:
                ax.set_xlabel(xlabel)
        for k in range(len(muts), nrows * ncols):
            axs[k // ncols][k % ncols].set_visible(False)
        h = [Line2D([0], [0], color=scol[sl], lw=2.5) for sl in sels] + \
            [Line2D([0], [0], color="k", lw=2.2), Line2D([0], [0], color="k", lw=1.5, ls="--")]
        fig.legend(h, [sel_name(sl) for sl in sels] + ["best fitness", "mean (population) fitness"],
                   loc="lower center", ncol=len(sels) + 2, frameon=False, bbox_to_anchor=(.5, 0))
        fig.suptitle(f"{algo_name(a)}: best and mean fitness by {xlabel.lower()} ({stat_txt} over seeds)", fontsize=13)
        fig.tight_layout(rect=[0, .05, 1, .96])
        path = os.path.join(folder, f"{a}_best_mean_vs_generation.png")
        _save(fig, path, dpi=130, bbox_inches="tight")
        plt.close(fig)
        written.append(path)
    print(f"{folder}: best/mean vs generation done ({len(written)} files)")
    return written


def run_all(json_file, out_dir="plots", stat="geomean", metric="best", fraction=1.0, part="first"):
    """Everything in one call: per-seed folders, combined folder, mutation comparisons,
    best-config heatmap and the overall result diagrams. Returns all PNG paths written."""
    out = []
    out += plot_ga_results(json_file, out_dir, metric=metric, fraction=fraction, part=part)
    out += compare_mutations(json_file, out_dir, metric=metric, fraction=fraction, part=part)
    out += best_config_and_mutation(json_file, out_dir, metric=metric, fraction=fraction, part=part)
    out += overall_diagrams(json_file, out_dir, stat=stat, metric=metric, fraction=fraction, part=part)
    # out += best_vs_mean_diagram(json_file, out_dir, stat=stat, fraction=fraction, part=part)
    out += best_mean_gap(json_file, out_dir, stat=stat, fraction=fraction, part=part)
    out += best_mean_vs_generation(json_file, out_dir, stat=stat, fraction=fraction, part=part)
    return out

run_all("Results/results.json","Results",fraction=.5)
# plot_ga_results("Results/results.json","Results")
# compare_mutations("Results/results.json","Results")
# best_config_and_mutation("Results/results.json","Results")