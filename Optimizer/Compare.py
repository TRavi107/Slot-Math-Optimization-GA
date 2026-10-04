"""
Read Optimizer/Results/*.json (from experiment.py) and produce:
  convergence.png  - best fitness vs simulator evaluations and vs wall time
  population.png   - mean fitness and diversity vs evaluations
  final.png        - verified final fitness and GA time per combo (mean +/- std over seeds)
  a ranked summary table in the terminal (and results_table.md)
"""
import collections
import glob
import json
import statistics as st

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RESULTS_DIR = "Optimizer/Results"

COLORS = {"TournamentSelection": "tab:blue", "RouletteSelection": "tab:orange", "SUS": "tab:green"}
STYLES = {"SteadyState": "-", "Generational": "--", "ElistismGenerational": ":"}


def load_groups():
    groups = collections.defaultdict(list)
    for path in glob.glob(f"{RESULTS_DIR}/*__s*.json"):
        with open(path) as f:
            r = json.load(f)
        groups[(r["selection"], r["replacement"])].append(r)
    return dict(sorted(groups.items()))


def mean_curve(runs, key):
    """Average a history field across seeds (same combo => same eval checkpoints)."""
    n = min(len(r["history"]) for r in runs)
    x_evals = [runs[0]["history"][k]["evals"] for k in range(n)]
    x_time = [st.mean(r["history"][k]["time"] for r in runs) for k in range(n)]
    y = [st.mean(r["history"][k][key] for r in runs) for k in range(n)]
    return x_evals, x_time, y


def style(sel, rep):
    return dict(color=COLORS.get(sel), linestyle=STYLES.get(rep, "-"), label=f"{sel} + {rep}")


def msd(values):
    values = [v for v in values if v is not None]
    if not values:
        return float("nan"), 0.0
    return st.mean(values), (st.stdev(values) if len(values) > 1 else 0.0)


def plot_convergence(groups):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(15, 5.5))
    for (sel, rep), runs in groups.items():
        ev, tm, best = mean_curve(runs, "best")
        a1.plot(ev, best, **style(sel, rep))
        a2.plot(tm, best, **style(sel, rep))
    a1.set(xlabel="Simulator evaluations", ylabel="Best fitness (mean over seeds)",
           yscale="log", title="Convergence per evaluation (fair compute comparison)")
    a2.set(xlabel="Wall time (s)", ylabel="Best fitness (mean over seeds)",
           yscale="log", title="Convergence per wall-clock time")
    for a in (a1, a2):
        a.grid(alpha=.3)
    a2.legend(fontsize=8, loc="upper right")
    fig.tight_layout()
    fig.savefig(f"{RESULTS_DIR}/convergence.png", dpi=150)


def plot_population(groups):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(15, 5.5))
    for (sel, rep), runs in groups.items():
        ev, _, mean = mean_curve(runs, "mean")
        _, _, div = mean_curve(runs, "diversity")
        a1.plot(ev, mean, **style(sel, rep))
        a2.plot(ev, div, **style(sel, rep))
    a1.set(xlabel="Simulator evaluations", ylabel="Population mean fitness",
           yscale="log", title="Population mean fitness")
    a2.set(xlabel="Simulator evaluations", ylabel="Distinct reelsets in population",
           title="Diversity (low = converged / clones)")
    for a in (a1, a2):
        a.grid(alpha=.3)
    a2.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(f"{RESULTS_DIR}/population.png", dpi=150)


def plot_final(groups):
    labels = [f"{s}\n{r}" for s, r in groups]
    ver = [msd([x["final_best_verified"] for x in runs]) for runs in groups.values()]
    tim = [msd([x["ga_time"] for x in runs]) for runs in groups.values()]
    colors = [COLORS.get(s) for s, _ in groups]

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(16, 5.5))
    a1.bar(labels, [m for m, _ in ver], yerr=[s for _, s in ver], color=colors, capsize=4)
    a1.set(ylabel="Verified fitness of final best (lower = better)",
           title="Final quality (re-simulated at high spin count)")
    a2.bar(labels, [m for m, _ in tim], yerr=[s for _, s in tim], color=colors, capsize=4)
    a2.set(ylabel="GA time (s)", title="Time per run")
    for a in (a1, a2):
        a.tick_params(axis="x", labelsize=7, rotation=45)
        a.grid(axis="y", alpha=.3)
    fig.tight_layout()
    fig.savefig(f"{RESULTS_DIR}/final.png", dpi=150)


def table(groups):
    rows = []
    for (sel, rep), runs in groups.items():
        v_m, v_s = msd([r["final_best_verified"] for r in runs])
        n_m, _ = msd([r["final_best_noisy"] for r in runs])
        t_m, _ = msd([r["ga_time"] for r in runs])
        hit = [r["evals_to_threshold"] for r in runs]
        e_m, _ = msd(hit)
        rows.append((v_m, sel, rep, v_s, n_m, t_m,
                     f"{sum(h is not None for h in hit)}/{len(hit)}",
                     e_m, msd([r["final_diversity"] for r in runs])[0],
                     msd([r["generations"] for r in runs])[0]))
    rows.sort()

    header = ("| Rank | Selection | Replacement | Verified fitness (mean ± std) | Noisy best | "
              "GA time (s) | Reached threshold | Evals to threshold | Final diversity | Gens |")
    lines = [header, "|" + "---|" * 10]
    for i, (v_m, sel, rep, v_s, n_m, t_m, hits, e_m, div, gens) in enumerate(rows, 1):
        lines.append(f"| {i} | {sel} | {rep} | {v_m:.4f} ± {v_s:.4f} | {n_m:.4f} | {t_m:.1f} | "
                     f"{hits} | {'–' if e_m != e_m else f'{e_m:.0f}'} | {div:.1f} | {gens:.0f} |")
    text = "\n".join(lines)
    print(text)
    with open(f"{RESULTS_DIR}/results_table.md", "w") as f:
        f.write(text + "\n")


if __name__ == "__main__":
    groups = load_groups()
    if not groups:
        raise SystemExit(f"no results in {RESULTS_DIR}; run experiment.py first")
    plot_convergence(groups)
    plot_population(groups)
    plot_final(groups)
    table(groups)
    print(f"plots written to {RESULTS_DIR}/")