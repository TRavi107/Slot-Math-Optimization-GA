"""
Statistical tests for the experiment.

1. Re-evaluate: each run's final best reelset is scored again with 100M spins on a
   seed the run never used (the in-run best is biased low). --reeval auto|stored|run|off
2. Test: runs are paired by seed. Per mutation count and family:
   Friedman -> Wilcoxon signed-rank -> Holm. Effect size Vargha-Delaney A12.
   Families: strategy, selection (per strategy), ga_vs_baselines, all (exploratory)
3. Noise floor: fitness SD at 10M spins is 0.034 base / 0.10 free (NoiseStudy.py),
   scaled by 1/sqrt(spins); a gap must be > 2.77 SD. Claims are listed only if
   Holm-significant, A12 at least small and above the floor.

    python Optimizer/Stats/Stats.py
    python Optimizer/Stats/Stats.py --stage free
    python Optimizer/Stats/Stats.py --reeval off      # quick look, in-run numbers

Output (Results/stats or Results/stats/FreeGame): stats_report.md, stats_pairwise.csv,
stats_friedman.csv, stats_runs.csv, reeval_<stage>.json (cache)
"""
import argparse
import hashlib
import itertools
import json
import os
import re
import sys
import time

import numpy as np
import pandas as pd
from scipy import stats

STAGES = {"base": r"^seed_\d+$", "free": r"^seed_\d+_free$"}
STAGE_MODE = {"base": "BaseGame", "free": "FreeGame"}
BASELINE_TAG = "Baseline"
STRATS = ["SteadyState", "ElistismGenerational", "Generational"]
SL = {"SteadyState": "Steady-state", "ElistismGenerational": "Elitist generational", "Generational": "Generational"}
SELL = {"TournamentSelection": "Tournament", "RouletteSelection": "Roulette", "SUS": "SUS"}
BL = {"HillClimbing": "Hill climbing", "SimulatedAnnealing": "Simulated annealing", "RandomSearch": "Random search"}
NO_MUTATION = {"RandomSearch"}   # its result is identical under every mutation_<m> key
TARGET = 0.2                      # error threshold for --metric evals

# simulator noise study: fitness SD of one 10M-spin measurement (worst case over reelsets)
NOISE_SD_10M = {"base": 0.034, "free": 0.10}
Z_DIFF_95 = 2.77                  # 1.96 * sqrt(2): two independent measurements, 95%

# simulator output key for each fitness variable type (same as Parents.OUTPUT_KEYS)
OUTPUT_KEYS = {"baseRTP": "baseRTP", "baseHitRate": "baseHitRate", "freeRTP": "freeRTP",
               "freeHitRate": "freeHitRate", "freeTriggerRate": "freeTriggerRate",
               "freeRetriggerRate": "freeReTriggerRate"}


def _int(v):
    return int(str(v).replace("_", "").strip())


# ---- config ----
def load_settings(config_path, stage):
    """Fitness goals for the stage, simulator path and a scratch folder, read from the GA config."""
    import yaml
    with open(config_path, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    mode = STAGE_MODE[stage]
    fv = raw.get("fitnessVariables") or []
    if isinstance(fv, dict):
        fv = fv.get(mode) or []
    goals = [(OUTPUT_KEYS[g["type"]], float(g["target"]), float(g["weight"]))
             for g in fv if g.get("enabled", True)]
    if not goals:
        raise SystemExit(f"[stats] no enabled fitness goals for {mode} in {config_path}")
    paths = raw.get("paths") or {}
    return dict(goals=goals, simulator=str(paths.get("simulatorPath", "build/simulator")),
                scratch=str(paths.get("tempParentsFolder", "Optimizer/ReelSets/TempParents")))


def fitness_of(output, goals):
    """Optimizer's fitness: sum of weight * |actual - target| / target (lower = better)."""
    return sum(w * abs(output[k] - t) / t for k, t, w in goals)


# ---- loading ----
def _unwrap(reels):
    """Parent files have an extra list level: [[reel0, reel1, ...]]."""
    if reels and isinstance(reels[0], list) and reels[0] and isinstance(reels[0][0], list):
        return reels[0]
    return reels


def load(json_file, stage="base"):
    """One row per run, with what is needed to test it and to re-evaluate its final reelset."""
    with open(json_file) as f:
        raw = json.load(f)
    keys = [k for k in raw if re.match(STAGES[stage], k)]
    if not keys:
        raise SystemExit(f"No {stage}-game runs in {json_file}")
    rows = []
    for seed_key in keys:
        meta = raw[seed_key].get("meta", {})
        budget = meta.get("generations", 1000)
        for mut_key, combos in raw[seed_key].get("results", {}).items():
            mm = re.match(r"^mutation_(\d+)$", mut_key)
            if not mm:
                continue
            for combo_key, entry in combos.items():
                strat, sel = combo_key.split("_", 1)
                strat = strat.replace("ElitismGenerational", "ElistismGenerational")
                arr = np.asarray(entry.get("results", []), dtype=float)
                if arr.ndim != 2 or len(arr) == 0:
                    continue
                bsf = np.minimum.accumulate(arr[:, 0])
                ev = np.arange(1, len(bsf) + 1) * (budget / len(bsf))
                hit = np.where(bsf <= TARGET)[0]
                is_bl = sel == BASELINE_TAG
                rows.append(dict(
                    seed=seed_key, master_seed=meta.get("masterSeed", re.findall(r"\d+", seed_key)[0]),
                    mutation=int(mm.group(1)), combo=combo_key, strategy=strat, selection=sel,
                    is_baseline=is_bl,
                    method=(BL.get(strat, strat) if is_bl else f"{SL.get(strat, strat)} + {SELL.get(sel, sel)}"),
                    run_spins=meta.get("spins"),
                    final_best=bsf[-1],
                    # never reached the target -> worse than any run that did (budget + 1); ranks stay valid
                    evals=float(ev[hit[0]]) if len(hit) else budget + 1.0,
                    reelset=entry.get("reelset"), best_spin=entry.get("bestSpin")))
    return pd.DataFrame(rows)


# ---- re-evaluation ----
def _reeval_seed(master, stage, mutation, combo):
    """Simulator seed for this script's re-evaluation: a label no optimizer stream uses, so it is
    independent of the run's own simulator seed and of its final-check seed."""
    from Optimizer.Utility.Seeding import derive_seed   # project module (Optimizer/), only needed when simulating
    strat = combo.split("_", 1)[0]
    m = "any" if strat in NO_MUTATION else mutation    # random search: one reelset for every rate
    return derive_seed(master, "stats_reeval", STAGE_MODE[stage], m, combo)


def _reelset_hash(reelset):
    return hashlib.sha1(json.dumps(reelset, sort_keys=True).encode()).hexdigest()[:12]


def reevaluate(df, mode, stage, spins, settings, cache_path):
    """Adds reeval_error, reeval_spins, reeval_seed and reeval_source to df."""
    goals = settings["goals"]
    cache = {}
    if os.path.isfile(cache_path):
        with open(cache_path) as f:
            cache = json.load(f)

    def stored(r):
        bs = r.best_spin
        if mode == "run" or not bs or bs.get("source") != "finalCheck":
            return None
        if _int(bs.get("spins", 0)) < spins:
            return None
        return bs

    todo = [i for i, r in df.iterrows() if stored(r) is None]
    if mode == "stored" and todo:
        bad = df.loc[todo[:5]]
        raise SystemExit(f"[stats] --reeval stored: {len(todo)} run(s) have no final check with at least "
                         f"{spins:,} spins, e.g. {', '.join(bad.seed + '/' + bad.combo)}. "
                         f"Use --reeval auto to simulate them here.")

    out = {c: [] for c in ("reeval_error", "reeval_spins", "reeval_seed", "reeval_source")}
    sim_needed = []
    for i, r in df.iterrows():
        bs = stored(r)
        if bs is not None:
            out["reeval_error"].append(fitness_of(bs["simOutput"], goals))
            out["reeval_spins"].append(_int(bs["spins"]))
            out["reeval_seed"].append(str(bs.get("seed", "")))
            out["reeval_source"].append("final check (optimizer)")
            continue
        if not r.reelset:
            raise SystemExit(f"[stats] {r.seed}/{r.combo} has no saved reelset to re-evaluate")
        seed = _reeval_seed(r.master_seed, stage, r.mutation, r.combo)
        key = f"{seed}|{spins}|{_reelset_hash(r.reelset)}"
        sim_needed.append((i, key, seed, r))
        out["reeval_error"].append(np.nan)
        out["reeval_spins"].append(spins)
        out["reeval_seed"].append(str(seed))
        out["reeval_source"].append("re-run (Stats.py)")

    unique = {k: (s, r) for _, k, s, r in sim_needed if k not in cache}
    if unique:
        from Optimizer.Utility.Utility import Evaluate, save_reelset_file   # project modules (Optimizer/)
        if not os.path.isfile(settings["simulator"]):
            raise SystemExit(f"[stats] simulator not found at {settings['simulator']} (paths.simulatorPath). "
                             "Build it, or run from the project root.")
        base_only = stage == "base"      # same mode as the optimizer scored this stage in
        path = os.path.join(settings["scratch"], "stats_reeval.json")
        print(f"[stats] re-evaluating {len(unique)} final reelset(s) with {spins:,} spins each "
              f"({'base game only' if base_only else 'full game'}); "
              f"{len(sim_needed) - len(unique)} more already cached or shared (random search is one run per seed)")
        t0 = time.perf_counter()
        for n, (key, (seed, r)) in enumerate(unique.items(), start=1):
            rs = r.reelset
            save_reelset_file(_unwrap(rs["BaseGameReel"]), _unwrap(rs["FreeGameReel"]), path)
            sim = Evaluate(spins, path, settings["simulator"], seed, base_only)
            cache[key] = dict(seed=str(seed), spins=spins, baseOnly=base_only, run=f"{r.seed}/{r.combo}",
                              mutation=r.mutation, simOutput=sim)
            with open(cache_path + ".tmp", "w") as f:       # save after every run: safe to stop and resume
                json.dump(cache, f)
            os.replace(cache_path + ".tmp", cache_path)
            el = time.perf_counter() - t0
            print(f"  {n}/{len(unique)}  {r.seed}/mutation_{r.mutation}/{r.combo}: "
                  f"error {fitness_of(sim, goals):.4f} (in-run {r.final_best:.4f})  "
                  f"| ~{el / n * (len(unique) - n) / 60:.0f} min left", flush=True)

    for i, key, _, _ in sim_needed:
        out["reeval_error"][df.index.get_loc(i)] = fitness_of(cache[key]["simOutput"], goals)
    for c, v in out.items():
        df[c] = v
    return df


# ---- statistics ----
def a12(x, y):
    """Vargha-Delaney A12 for MINIMISATION: probability a run of x ends lower than a run of y (ties = 1/2)."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    lt = (x[:, None] < y[None, :]).sum()
    eq = (x[:, None] == y[None, :]).sum()
    return (lt + 0.5 * eq) / (len(x) * len(y))


def magnitude(a):
    d = abs(a - 0.5)
    return "negligible" if d < 0.06 else "small" if d < 0.14 else "medium" if d < 0.21 else "large"


def holm(p):
    """Holm-Bonferroni adjusted p-values (step-down, monotone)."""
    p = np.asarray(p, float)
    adj, running = np.empty(len(p)), 0.0
    for rank, i in enumerate(np.argsort(p)):
        running = max(running, (len(p) - rank) * p[i])
        adj[i] = min(1.0, running)
    return adj


def wilcoxon_p(x, y):
    """Two-sided paired Wilcoxon signed-rank p-value; 1.0 if every pair is tied."""
    if np.all(np.asarray(x, float) == np.asarray(y, float)):
        return 1.0
    return float(stats.wilcoxon(x, y, zero_method="pratt", alternative="two-sided").pvalue)


def min_attainable_p(n):
    """Smallest two-sided p an exact signed-rank test can give with n pairs (all differences one sign)."""
    return 2.0 / 2 ** n


def compare_family(wide, family, mutation, alpha, floor):
    """wide: rows = seeds, columns = methods (incomplete seeds dropped). Returns (friedman_row, pair_rows)."""
    wide = wide.dropna()
    n, k = wide.shape
    fr = dict(family=family, mutation=mutation, n_seeds=n, k_methods=k, chi2=np.nan, p=np.nan, kendall_w=np.nan)
    if n < 2 or k < 2:
        return fr, []
    if k >= 3:
        chi2, p = stats.friedmanchisquare(*[wide[c].values for c in wide.columns])
        fr.update(chi2=chi2, p=p, kendall_w=chi2 / (n * (k - 1)))   # Kendall's W = omnibus effect size
    rows = []
    for a, b in itertools.combinations(wide.columns, 2):
        x, y = wide[a].values, wide[b].values
        A = a12(x, y)
        if A < 0.5:                       # orient every row as "better vs worse"
            a, b, x, y, A = b, a, y, x, 1 - A
        gap = np.median(y) - np.median(x)
        rows.append(dict(family=family, mutation=mutation, better=a, worse=b, n_seeds=n,
                         median_better=np.median(x), median_worse=np.median(y), median_gap=gap,
                         noise_floor=floor, above_noise=bool(floor is None or gap > floor),
                         wins=int((x < y).sum()), ties=int((x == y).sum()),
                         p_raw=wilcoxon_p(x, y), A12=A, magnitude=magnitude(A), omnibus_p=fr["p"]))
    _apply_holm(rows, alpha)
    return fr, rows


def _apply_holm(rows, alpha):
    for r, pa in zip(rows, holm([r["p_raw"] for r in rows])):
        r["p_holm"], r["significant"] = pa, bool(pa < alpha)


def families(df, score):
    """Yield (family name, mutation, wide table seeds x methods) for every planned family."""
    for m in sorted(df.mutation.unique()):
        g = df[df.mutation == m]
        ga, bl = g[~g.is_baseline], g[g.is_baseline]
        s = ga.groupby(["seed", "strategy"])[score].median().unstack()
        yield "strategy", m, s[[c for c in STRATS if c in s.columns]].rename(columns=SL)
        for st in STRATS:
            sub = ga[ga.strategy == st]
            if sub.selection.nunique() > 1:
                yield (f"selection ({SL[st]})", m,
                       sub.pivot_table(index="seed", columns="selection", values=score).rename(columns=SELL))
        if not bl.empty and not ga.empty:
            yield "ga_vs_baselines", m, g.pivot_table(index="seed", columns="method", values=score)
        yield "all (exploratory)", m, g.pivot_table(index="seed", columns="method", values=score)


# ---- report ----
def fmt_p(p):
    return "n/a" if p != p else ("< 0.001" if p < 0.001 else f"{p:.3f}")


def p_text(p):
    return f"p_Holm {fmt_p(p)}" if p < 0.001 else f"p_Holm = {fmt_p(p)}"


def write_report(df, fried, pair, out, args, score, unit, floor, min_n):
    L = [f"# Statistical tests ({unit}, lower is better)", ""]
    if score == "reeval_error":
        src = df.reeval_source.value_counts()
        spins = sorted(set(int(s) for s in df.reeval_spins))
        L += ["## Re-evaluation", "",
              f"Each run's final best reelset was measured again on a simulator seed the run never used "
              f"({', '.join(f'{s:,}' for s in spins)} spins). Sources: "
              + "; ".join(f"{v} runs from {k}" for k, v in src.items()) + ".", "",
              "In-run final best vs re-evaluated error (median over seeds). The in-run value is the lowest of "
              "many noisy measurements, so it is biased low; the ratio shows how much.", "",
              "| Mutation | Method | In-run final best | Re-evaluated | Re-evaluated / in-run |", "|---|---|---|---|---|"]
        g = df.groupby(["mutation", "method"])[["final_best", "reeval_error"]].median().reset_index()
        for _, r in g.iterrows():
            L.append(f"| {r.mutation} | {r.method} | {r.final_best:.4g} | {r.reeval_error:.4g} | "
                     f"{r.reeval_error / r.final_best:.2f} |")
        L.append("")
    elif score == "final_best":
        L += ["> **Note:** these are the in-run final best errors (lowest of ~1000 noisy measurements, biased "
              "low). Use the re-evaluated errors (--reeval auto) for the paper.", ""]

    L += [f"Paired by seed. Friedman omnibus test, then two-sided Wilcoxon signed-rank tests with Holm "
          f"correction within each family; alpha = {args.alpha}. Effect size = Vargha-Delaney A12 "
          f"(probability the better method reaches a lower value on a run; 0.5 = no difference)."]
    if floor is not None:
        L += [f"Noise floor = {floor:.4g}: the smallest gap two independent {unit} measurements can resolve "
              f"at 95% (2.77 x simulator SD at the spins used)."]
    L.append("")
    if min_n is not None and min_attainable_p(min_n) >= args.alpha:
        L += [f"> **Warning:** the smallest family has only {min_n} seeds. With {min_n} pairs the exact Wilcoxon "
              f"test cannot give p below {min_attainable_p(min_n):.4f}, so nothing can be significant at "
              f"alpha = {args.alpha}, however large the effect. Add seeds (20-30 is typical).", ""]

    L += ["## Omnibus tests (Friedman)", "",
          "| Family | Mutation | Seeds | Methods | chi2 | p | Kendall's W |", "|---|---|---|---|---|---|---|"]
    for _, r in fried.iterrows():
        L.append(f"| {r.family} | {r.mutation} | {r.n_seeds} | {r.k_methods} | "
                 f"{r.chi2:.2f} | {fmt_p(r.p)} | {r.kendall_w:.2f} |")
    for fam, g in pair.groupby("family", sort=False):
        if fam.startswith("all"):
            continue
        L += ["", f"## {fam}", "",
              "| Mutation | Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |",
              "|---|---|---|---|---|---|---|---|---|"]
        for _, r in g.iterrows():
            star = " *" if r.significant else ""
            L.append(f"| {r.mutation} | {r.better} | {r.worse} | {r.median_better:.4g} / {r.median_worse:.4g} | "
                     f"{'yes' if r.above_noise else 'no'} | {r.wins}/{r.n_seeds} | {fmt_p(r.p_holm)}{star} | "
                     f"{r.A12:.2f} | {r.magnitude} |")

    ok = pair[pair.significant & pair.above_noise & (pair.magnitude != "negligible")
              & ~pair.family.str.startswith("all")]
    L += ["", "## Claims you can make", "",
          "Significant after Holm, A12 at least small, and median gap above the noise floor.", ""]
    if ok.empty:
        L.append("None. Report the medians and A12 values as descriptive, not as wins.")
    for _, r in ok.iterrows():
        L.append(f"- Mutation {r.mutation}: {r.better} reached a lower {unit} than {r.worse} "
                 f"(median {r.median_better:.4g} vs {r.median_worse:.4g}; Wilcoxon signed-rank, "
                 f"n = {r.n_seeds} seeds, {p_text(r.p_holm)}; A12 = {r.A12:.2f}, {r.magnitude}).")
    near = pair[pair.significant & ~pair.above_noise & ~pair.family.str.startswith("all")]
    if not near.empty:
        L += ["", f"{len(near)} comparison(s) are significant but their median gap is below the noise floor; "
                  "treat those as 'no practical difference'."]
    with open(os.path.join(out, "stats_report.md"), "w") as f:
        f.write("\n".join(L) + "\n")


# ---- main ----
def main():
    ap = argparse.ArgumentParser(description="Re-evaluate final reelsets, then Friedman + Wilcoxon/Holm + A12.")
    ap.add_argument("results", nargs="?", default="Results/results.json")
    ap.add_argument("--stage", choices=["base", "free"], default="base")
    ap.add_argument("--config", default="GA-config.yaml", help="for fitness targets and the simulator path")
    ap.add_argument("--metric", choices=["final", "evals"], default="final",
                    help="final = final best error (default); evals = evaluations to reach error <= 0.2 "
                         "(a property of the run itself, so it is not re-evaluated)")
    ap.add_argument("--reeval", choices=["auto", "stored", "run", "off"], default="auto")
    ap.add_argument("--reeval-spins", type=_int, default=100_000_000,
                    help="spins per re-evaluation; also the minimum a stored final check needs (default 100M)")
    ap.add_argument("--noise-sd", type=float, default=None,
                    help="fitness SD of one 10M-spin measurement (default 0.034 base, 0.10 free, noise study)")
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # project modules live next to this file
    out = args.out or (os.path.join("Results", "stats") if args.stage == "base"
                       else os.path.join("Results", "stats", "FreeGame"))
    os.makedirs(out, exist_ok=True)
    df = load(args.results, args.stage)

    if args.metric == "evals":
        score, unit, floor = "evals", f"evaluations to reach error <= {TARGET}", None
    elif args.reeval == "off":
        score, unit = "final_best", "in-run final best error"
        spins = min(_int(s) for s in df.run_spins.dropna()) if df.run_spins.notna().any() else 10_000_000
    else:
        settings = load_settings(args.config, args.stage)
        df = reevaluate(df, args.reeval, args.stage, args.reeval_spins, settings,
                        os.path.join(out, f"reeval_{args.stage}.json"))
        score, unit = "reeval_error", "re-evaluated error"
        spins = int(df.reeval_spins.min())
    if args.metric == "final":
        sd10 = args.noise_sd if args.noise_sd is not None else NOISE_SD_10M[args.stage]
        floor = Z_DIFF_95 * sd10 * np.sqrt(10_000_000 / spins)

    keep = [c for c in ["seed", "mutation", "combo", "method", "final_best", "evals", "reeval_error",
                        "reeval_spins", "reeval_seed", "reeval_source"] if c in df.columns]
    df[keep].to_csv(os.path.join(out, "stats_runs.csv"), index=False)

    fried, pair = [], []
    bl_names = set(BL.values())
    for fam, m, wide in families(df, score):
        fr, rows = compare_family(wide, fam, m, args.alpha, floor)
        if fam == "ga_vs_baselines":      # only GA-vs-baseline pairs, Holm over just those
            rows = [r for r in rows if (r["better"] in bl_names) != (r["worse"] in bl_names)]
            _apply_holm(rows, args.alpha)
        fried.append(fr)
        pair.extend(rows)
    fried, pair = pd.DataFrame(fried), pd.DataFrame(pair)
    fried.to_csv(os.path.join(out, "stats_friedman.csv"), index=False)
    pair.to_csv(os.path.join(out, "stats_pairwise.csv"), index=False)
    min_n = int(fried.n_seeds.min()) if len(fried) else None
    write_report(df, fried, pair, out, args, score, unit, floor, min_n)

    print(f"[stats] {len(df)} runs | {df.seed.nunique()} seeds | "
          f"mutation counts {sorted(int(m) for m in df.mutation.unique())} | tested: {unit}")
    if floor is not None:
        print(f"[stats] noise floor {floor:.4g}")
    n_sig = int(pair.significant.sum()) if len(pair) else 0
    print(f"[stats] {len(pair)} pairwise comparisons, {n_sig} significant after Holm at alpha = {args.alpha}")
    if min_n is not None and min_attainable_p(min_n) >= args.alpha:
        print(f"[stats] WARNING: some families have only {min_n} seeds; the exact Wilcoxon test cannot reach "
              f"p < {args.alpha} with so few. Add seeds.")
    print(f"[stats] wrote {out}/stats_report.md and the CSVs")


if __name__ == "__main__":
    main()