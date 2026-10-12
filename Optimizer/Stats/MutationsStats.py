"""
Mutation-count tests for the GA reelset-tuning experiment (companion to Stats.py).

Stats.py tests methods against each other at ONE mutation count at a time. This script adds the two
comparisons it does not make:

  1. mutation (<method>)      For each method: mutation 1 vs 3 vs 5 vs 10.
                              Friedman across the four counts, then pairwise Wilcoxon + Holm.
  2. best mutation            Every method at its OWN best mutation count (lowest median error),
                              then GA vs baselines (Holm over the GA-baseline pairs only) and an
                              exploratory everything-vs-everything family.

Same statistics as Stats.py: runs are paired by seed (every method and mutation count on seed_k starts
from the same initial population), two-sided Wilcoxon signed-rank (zero_method="pratt"), Holm
correction inside each family, Vargha-Delaney A12, and the same noise floor
(2.77 x fitness SD, 0.034 base / 0.10 free at 10M spins, scaled to the re-check spins).

Scores are the stored final checks (bestSpin, source "finalCheck"), with fitness recomputed from the
config's targets and weights - the numbers Stats.py uses with --reeval auto/stored when every run has
a final check. Random search ignores the mutation count, so it is left out of both families.

Caveat for family 2: each method's best mutation count is picked on the same 30 seeds it is then
tested on, which slightly favours methods whose medians vary more across counts. Say so in the paper,
or pick the counts on one stage and test on the other.

Usage (from the "Math Optimization" folder):
    python Optimizer/MutationStats.py                         # Results/results.json, base game
    python Optimizer/MutationStats.py --stage free
    python Optimizer/MutationStats.py Results/other.json --stage free --out Results/stats/mut_free

Writes to <out> (default Results/stats/mutation_<stage>):
    mutation_report.md       tables + one sentence per supported claim
    mutation_pairwise.csv    every comparison      mutation_friedman.csv   omnibus tests
    best_mutation.csv        each method's best count and median at every count
"""
import argparse
import itertools
import json
import os
import re

import numpy as np
import pandas as pd
from scipy import stats

STAGES = {"base": r"^seed_\d+$", "free": r"^seed_\d+_free$"}
STAGE_MODE = {"base": "BaseGame", "free": "FreeGame"}
SL = {"SteadyState": "Steady-state", "ElistismGenerational": "Elitist generational", "Generational": "Generational"}
SELL = {"TournamentSelection": "Tournament", "RouletteSelection": "Roulette", "SUS": "SUS"}
BL = {"HillClimbing": "Hill climbing", "SimulatedAnnealing": "Simulated annealing", "RandomSearch": "Random search"}
NO_MUTATION = {"RandomSearch"}
NOISE_SD_10M = {"base": 0.034, "free": 0.10}
Z_DIFF_95 = 2.77
OUTPUT_KEYS = {"baseRTP": "baseRTP", "baseHitRate": "baseHitRate", "freeRTP": "freeRTP",
               "freeHitRate": "freeHitRate", "freeTriggerRate": "freeTriggerRate",
               "freeRetriggerRate": "freeReTriggerRate"}


# ----------------------------------------------------------------- loading
def load_goals(config_path, stage):
    import yaml
    with open(config_path, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    fv = raw.get("fitnessVariables") or []
    if isinstance(fv, dict):
        fv = fv.get(STAGE_MODE[stage]) or []
    goals = [(OUTPUT_KEYS[g["type"]], float(g["target"]), float(g["weight"])) for g in fv if g.get("enabled", True)]
    if not goals:
        raise SystemExit(f"no enabled fitness goals for {STAGE_MODE[stage]} in {config_path}")
    return goals


def fitness_of(output, goals):
    return sum(w * abs(output[k] - t) / t for k, t, w in goals)


def load(json_file, stage, goals):
    with open(json_file) as f:
        raw = json.load(f)
    rows, missing = [], []
    for seed_key in (k for k in raw if re.match(STAGES[stage], k)):
        for mut_key, combos in raw[seed_key].get("results", {}).items():
            mm = re.match(r"^mutation_(\d+)$", mut_key)
            if not mm:
                continue
            for combo_key, entry in combos.items():
                strat, sel = combo_key.split("_", 1)
                if strat in NO_MUTATION:
                    continue
                bs = entry.get("bestSpin") or {}
                if bs.get("source") != "finalCheck":
                    missing.append(f"{seed_key}/{mut_key}/{combo_key}")
                    continue
                is_bl = sel == "Baseline"
                rows.append(dict(seed=seed_key, mutation=int(mm.group(1)), is_baseline=is_bl,
                                 method=BL.get(strat, strat) if is_bl else f"{SL.get(strat, strat)} + {SELL.get(sel, sel)}",
                                 error=fitness_of(bs["simOutput"], goals), spins=int(bs.get("spins", 0))))
    if missing:
        raise SystemExit(f"{len(missing)} run(s) have no stored final check, e.g. {missing[:3]}. "
                         "Run Stats.py (which can re-evaluate them) instead.")
    if not rows:
        raise SystemExit(f"no {stage}-game runs in {json_file}")
    return pd.DataFrame(rows)


# ----------------------------------------------------------------- statistics (same as Stats.py)
def a12(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    return ((x[:, None] < y[None, :]).sum() + 0.5 * (x[:, None] == y[None, :]).sum()) / (len(x) * len(y))


def magnitude(a):
    d = abs(a - 0.5)
    return "negligible" if d < 0.06 else "small" if d < 0.14 else "medium" if d < 0.21 else "large"


def holm(p):
    p = np.asarray(p, float)
    adj, running = np.empty(len(p)), 0.0
    for rank, i in enumerate(np.argsort(p)):
        running = max(running, (len(p) - rank) * p[i])
        adj[i] = min(1.0, running)
    return adj


def wilcoxon_p(x, y):
    if np.all(np.asarray(x, float) == np.asarray(y, float)):
        return 1.0
    return float(stats.wilcoxon(x, y, zero_method="pratt", alternative="two-sided").pvalue)


def compare_family(wide, family, alpha, floor, keep=None):
    wide = wide.dropna()
    n, k = wide.shape
    fr = dict(family=family, n_seeds=n, k=k, chi2=np.nan, p=np.nan, kendall_w=np.nan)
    if k >= 3 and n >= 2:
        chi2, p = stats.friedmanchisquare(*[wide[c].values for c in wide.columns])
        fr.update(chi2=chi2, p=p, kendall_w=chi2 / (n * (k - 1)))
    rows = []
    for a, b in itertools.combinations(wide.columns, 2):
        if keep is not None and not keep(a, b):
            continue
        x, y = wide[a].values, wide[b].values
        A = a12(x, y)
        if A < 0.5:
            a, b, x, y, A = b, a, y, x, 1 - A
        gap = np.median(y) - np.median(x)
        rows.append(dict(family=family, better=a, worse=b, n_seeds=n, median_better=np.median(x),
                         median_worse=np.median(y), median_gap=gap, above_noise=bool(gap > floor),
                         wins=int((x < y).sum()), p_raw=wilcoxon_p(x, y), A12=A, magnitude=magnitude(A),
                         omnibus_p=fr["p"]))
    for r, pa in zip(rows, holm([r["p_raw"] for r in rows])):
        r["p_holm"], r["significant"] = pa, bool(pa < alpha)
    return fr, rows


# ----------------------------------------------------------------- report
def fmt_p(p):
    return "n/a" if p != p else ("< 0.001" if p < 0.001 else f"{p:.3f}")


def main():
    ap = argparse.ArgumentParser(description="Mutation-count tests: across counts per method, and best count per method.")
    ap.add_argument("results", nargs="?", default="Results/results.json")
    ap.add_argument("--stage", choices=["base", "free"], default="base")
    ap.add_argument("--config", default="GA-config.yaml")
    ap.add_argument("--noise-sd", type=float, default=None)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    out = args.out or os.path.join("Results", "stats", f"mutation_{args.stage}")
    os.makedirs(out, exist_ok=True)
    df = load(args.results, args.stage, load_goals(args.config, args.stage))
    spins = int(df.spins.min())
    sd10 = args.noise_sd if args.noise_sd is not None else NOISE_SD_10M[args.stage]
    floor = Z_DIFF_95 * sd10 * np.sqrt(10_000_000 / spins)
    muts = sorted(int(m) for m in df.mutation.unique())

    fried, pair = [], []
    # 1. across mutation counts, one family per method
    for method, g in df.groupby("method", sort=True):
        wide = g.pivot_table(index="seed", columns="mutation", values="error")[muts]
        wide.columns = [f"m={m}" for m in wide.columns]
        fr, rows = compare_family(wide, f"mutation ({method})", args.alpha, floor)
        fried.append(fr); pair.extend(rows)

    # 2. every method at its own best mutation count
    med = df.pivot_table(index="method", columns="mutation", values="error", aggfunc="median")[muts]
    best_m = med.idxmin(axis=1)
    best = pd.DataFrame({"best_mutation": best_m, "best_median": med.min(axis=1)}).join(
        med.rename(columns=lambda m: f"median_m{m}"))
    best["is_baseline"] = [df[df.method == m].is_baseline.iloc[0] for m in best.index]
    best.sort_values("best_median").to_csv(os.path.join(out, "best_mutation.csv"))
    label = {m: f"{m} (m={best_m[m]})" for m in best.index}
    parts = [df[(df.method == m) & (df.mutation == best_m[m])].set_index("seed").error.rename(label[m]) for m in best.index]
    wide_best = pd.concat(parts, axis=1)
    bl_labels = {label[m] for m in best.index if best.loc[m, "is_baseline"]}
    fr, rows = compare_family(wide_best, "best mutation: ga_vs_baselines", args.alpha, floor,
                              keep=lambda a, b: (a in bl_labels) != (b in bl_labels))
    fried.append(fr); pair.extend(rows)
    fr, rows = compare_family(wide_best, "best mutation: all (exploratory)", args.alpha, floor)
    fried.append(fr); pair.extend(rows)

    fried, pair = pd.DataFrame(fried), pd.DataFrame(pair)
    fried.to_csv(os.path.join(out, "mutation_friedman.csv"), index=False)
    pair.to_csv(os.path.join(out, "mutation_pairwise.csv"), index=False)

    # ---- report
    L = [f"# Mutation-count tests ({STAGE_MODE[args.stage]}, re-evaluated error, lower is better)", "",
         f"{len(df)} runs, {df.seed.nunique()} seeds, mutation counts {muts}, scores from the stored "
         f"{spins:,}-spin final checks. Random search is left out (it ignores the mutation count).", "",
         f"Paired by seed. Friedman, then two-sided Wilcoxon signed-rank with Holm correction inside each family; "
         f"alpha = {args.alpha}. A12 = probability the better setting ends lower on a run (0.5 = no difference). "
         f"Noise floor = {floor:.4g}.", "",
         "## Best mutation count per method (median error at each count)", "",
         "| Method | " + " | ".join(f"m={m}" for m in muts) + " | Best | Friedman p | Kendall's W |",
         "|---|" + "---|" * (len(muts) + 3)]
    fmap = fried.set_index("family")
    for m in best.sort_values("best_median").index:
        f = fmap.loc[f"mutation ({m})"]
        cells = [(f"**{med.loc[m, k]:.4g}**" if k == best_m[m] else f"{med.loc[m, k]:.4g}") for k in muts]
        L.append(f"| {m} | " + " | ".join(cells) + f" | m={best_m[m]} | {fmt_p(f.p)} | {f.kendall_w:.2f} |")
    L += ["", "Friedman p below alpha = the method's result depends on the mutation count. "
              "Kendall's W: 0.1 small, 0.3 moderate, 0.5+ strong.", ""]

    def table(fam_rows, title):
        L.extend(["", f"## {title}", "", "| Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |",
                  "|---|---|---|---|---|---|---|---|"])
        for _, r in fam_rows.iterrows():
            L.append(f"| {r.better} | {r.worse} | {r.median_better:.4g} / {r.median_worse:.4g} | "
                     f"{'yes' if r.above_noise else 'no'} | {r.wins}/{r.n_seeds} | {fmt_p(r.p_holm)}{' *' if r.significant else ''} | "
                     f"{r.A12:.2f} | {r.magnitude} |")

    L += ["## Pairwise: mutation counts within each method"]
    for fam, g in pair[pair.family.str.startswith("mutation (")].groupby("family", sort=False):
        table(g, fam[len("mutation ("):-1])
    table(pair[pair.family == "best mutation: ga_vs_baselines"], "Each method at its best mutation count: GA vs baselines")
    L += ["", "Each method's best count was chosen on the same seeds it is tested on (slightly optimistic for every method)."]

    ok = pair[pair.significant & pair.above_noise & (pair.magnitude != "negligible") & ~pair.family.str.contains("exploratory")]
    L += ["", "## Claims you can make", "", "Significant after Holm, A12 at least small, and median gap above the noise floor.", ""]
    if ok.empty:
        L.append("None.")
    for _, r in ok.iterrows():
        ctx = r.family[len("mutation ("):-1] + ": " if r.family.startswith("mutation (") else "At each method's best mutation count: "
        L.append(f"- {ctx}{r.better} reached a lower re-evaluated error than {r.worse} (median {r.median_better:.4g} vs "
                 f"{r.median_worse:.4g}; Wilcoxon signed-rank, n = {r.n_seeds} seeds, p_Holm "
                 f"{'< 0.001' if r.p_holm < 0.001 else '= ' + format(r.p_holm, '.3f')}; A12 = {r.A12:.2f}, {r.magnitude}).")
    with open(os.path.join(out, "mutation_report.md"), "w") as f:
        f.write("\n".join(L) + "\n")
    print(f"[mutation stats] {len(df)} runs | noise floor {floor:.4g} | "
          f"{int(pair.significant.sum())} of {len(pair)} comparisons significant | wrote {out}/mutation_report.md")


if __name__ == "__main__":
    main()