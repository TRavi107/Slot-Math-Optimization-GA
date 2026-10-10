#!/usr/bin/env python3
"""
Noise study on the GA's final reelsets.

For every combination in Results/results.json (each GA replacement x selection pair
and each baseline, per mutation count and game mode) it takes the best reelset
across all GA runs (seed_<n>), re-simulates it RUNS times with different seeds, and
reports the run-to-run noise of every statistic and of the GA fitness.

  - BaseGame results (seed_<n>)      are simulated base game only, as the GA scored them
  - FreeGame results (seed_<n>_free) are simulated as the full game
  - Fitness targets and weights come from the results file itself: targets from
    bestSpin.expectedOutput, weights solved from bestSpin.errorPercent and
    bestSpin.fitness (needs at least as many saved combinations as goals).
    With fewer, pass --config GA-config.yaml; it is checked against the saved fitness.
  - Run i uses the same simulator seed for every reelset (common random numbers),
    so the paired-difference noise between combinations is measured too.

Run from the "Math Optimization" folder:
    python noise_study.py                         # all modes, all mutation counts
    python noise_study.py --mode FreeGame --mutation 5
    python noise_study.py --runs 20 --spins 40000000

Outputs (in --out, default NoiseStudy/):
    reelsets/<mode>_mutation_<m>_<combo>.json  the reelsets tested
    noise_runs.csv                             one row per simulation
    noise_summary.csv                          mean and SD per combination and metric
    report.txt                                 the printed report
"""
import argparse, csv, json, math, os, statistics as st, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor

# simulator output key for each fitness type in GA-config.yaml
OUTPUT_KEYS = {"baseRTP": "baseRTP", "baseHitRate": "baseHitRate", "freeRTP": "freeRTP",
               "freeHitRate": "freeHitRate", "freeTriggerRate": "freeTriggerRate",
               "freeRetriggerRate": "freeReTriggerRate"}

# stats worth reporting per mode (BaseGame runs skip the free spins, so free stats are meaningless there)
MODE_STATS = {
    "BaseGame": ["baseRTP", "baseHitRate", "freeTriggerRate"],
    "FreeGame": ["baseRTP", "baseHitRate", "freeTriggerRate", "freeRTP", "freeHitRate",
                 "freeReTriggerRate", "totalRTP"],
}
ALL_STATS = MODE_STATS["FreeGame"]


# ---------------------------------------------------------------- fitness goals
def mode_of(seed_key):
    return "FreeGame" if seed_key.endswith("_free") else "BaseGame"


def best_spin_records(data, mode):
    """Every bestSpin record of this mode that has targets, error % and fitness."""
    recs = []
    for seed_key, seed_entry in data.items():
        if mode_of(seed_key) != mode:
            continue
        for combos in seed_entry.get("results", {}).values():
            for entry in combos.values():
                bs = entry.get("bestSpin") or {}
                if bs.get("expectedOutput") and bs.get("errorPercent") and bs.get("fitness") is not None:
                    recs.append(bs)
    return recs


def solve(A, b):
    """Least squares A w = b via the normal equations (tiny systems, no numpy needed)."""
    n = len(A[0])
    M = [[sum(r[i] * r[j] for r in A) for j in range(n)] + [sum(r[i] * y for r, y in zip(A, b))]
         for i in range(n)]
    for c in range(n):
        piv = max(range(c, n), key=lambda r: abs(M[r][c]))
        if abs(M[piv][c]) < 1e-12:
            return None                                  # singular: records don't pin the weights
        M[c], M[piv] = M[piv], M[c]
        for r in range(n):
            if r != c:
                f = M[r][c] / M[c][c]
                M[r] = [x - f * y for x, y in zip(M[r], M[c])]
    return [M[i][n] / M[i][i] for i in range(n)]


def goals_from_results(data, mode):
    """
    Recover {stat: (target, weight)} from the results file itself.
      targets : bestSpin.expectedOutput
      weights : solved from bestSpin.errorPercent and bestSpin.fitness, because
                fitness = sum(weight * |errorPercent| / 100) for every record.
    Returns (goals, note) or (None, reason).
    """
    recs = best_spin_records(data, mode)
    if not recs:
        return None, "no bestSpin records with targets"
    keys = sorted(recs[0]["expectedOutput"])
    targets = {k: float(recs[0]["expectedOutput"][k]) for k in keys}
    for bs in recs:
        if sorted(bs["expectedOutput"]) != keys or any(
                abs(float(bs["expectedOutput"][k]) - targets[k]) > 1e-12 for k in keys):
            return None, "runs in this file used different targets - study them separately"
    if len(recs) < len(keys):
        return None, (f"only {len(recs)} saved result(s) for {len(keys)} unknown weights "
                      f"(need at least {len(keys)} combinations)")
    A = [[abs(float(bs["errorPercent"][k])) / 100 for k in keys] for bs in recs]
    b = [float(bs["fitness"]) for bs in recs]
    w = solve(A, b)
    if w is None:
        return None, "saved results don't separate the weights (errors too similar)"
    w = [round(x, 2) if abs(x - round(x, 2)) < 0.01 else x for x in w]   # undo errorPercent rounding
    worst = max(abs(sum(wi * ai for wi, ai in zip(w, row)) - y) / max(abs(y), 1e-9)
                for row, y in zip(A, b))
    if worst > 1e-3:
        return None, f"recovered weights don't reproduce the saved fitness (off by {worst:.2%})"
    return ({k: (targets[k], wi) for k, wi in zip(keys, w)},
            f"recovered from {len(recs)} saved results (reproduces every saved fitness "
            f"to within {worst:.1e})")


def goals_from_config(config_path, mode):
    import yaml                                      # only needed for this fallback
    with open(config_path) as f:
        cfg = yaml.safe_load(f)
    return {OUTPUT_KEYS[g["type"]]: (float(g["target"]), float(g["weight"]))
            for g in cfg["fitnessVariables"][mode] if g.get("enabled", True)}


def fitness_goals(data, mode, config_path):
    goals, note = goals_from_results(data, mode)
    if goals:
        return goals, note
    if not config_path:
        sys.exit(f"[{mode}] can't recover the fitness weights from the results file: {note}.\n"
                 f"Pass --config GA-config.yaml to take them from the config instead.")
    cfg_goals = goals_from_config(config_path, mode)
    # if the file has targets, make sure the config still agrees with them
    recs = best_spin_records(data, mode)
    if recs:
        saved = {k: float(v) for k, v in recs[0]["expectedOutput"].items()}
        if saved != {k: t for k, (t, _) in cfg_goals.items()}:
            sys.exit(f"[{mode}] {config_path} targets {cfg_goals} differ from the targets these "
                     f"results were optimized for {saved}. Fix the config or the results file.")
        for bs in recs:                              # check config weights reproduce saved fitness
            f = sum(w * abs(float(bs["errorPercent"][k])) / 100 for k, (_, w) in cfg_goals.items())
            if abs(f - float(bs["fitness"])) > 1e-3 * max(abs(float(bs["fitness"])), 1e-9):
                sys.exit(f"[{mode}] weights in {config_path} don't reproduce the saved fitness "
                         f"({f:.5f} vs {bs['fitness']:.5f}) - the config changed since this run.")
        return cfg_goals, f"weights from {config_path} ({note}); checked against saved fitness"
    return cfg_goals, f"from {config_path} ({note})"


def unwrap(reels):
    if reels and isinstance(reels[0], list) and reels[0] and isinstance(reels[0][0], list):
        return reels[0]
    return reels


def saved_fitness(entry):
    """Best fitness recorded for an experiment: bestSpin.fitness, else the best of its history."""
    bs = entry.get("bestSpin")
    if bs and bs.get("fitness") is not None:
        return float(bs["fitness"])
    hist = entry.get("results") or []
    vals = [row[0] for row in hist if row and row[0] is not None]
    return min(vals) if vals else math.inf


def best_per_combination(data, modes, mutations):
    """{(mode, mutation, combo): (seed_key, entry)} - lowest saved fitness across GA runs."""
    best = {}
    for seed_key, seed_entry in data.items():
        mode = mode_of(seed_key)
        if mode not in modes:
            continue
        for mut_key, combos in seed_entry.get("results", {}).items():
            m = mut_key.replace("mutation_", "")
            if mutations and m not in mutations:
                continue
            for combo, entry in combos.items():
                if "reelset" not in entry:
                    continue
                key = (mode, m, combo)
                if key not in best or saved_fitness(entry) < saved_fitness(best[key][1]):
                    best[key] = (seed_key, entry)
    return best


# ---------------------------------------------------------------- simulation
def seed_for(run):
    """Well-mixed seed per run index (splitmix64). Shared by every reelset -> CRN."""
    x = (0x5EED0000 + run) * 0x9E3779B97F4A7C15 & (2**64 - 1)
    x = (x ^ (x >> 30)) * 0xBF58476D1CE4E5B9 & (2**64 - 1)
    x = (x ^ (x >> 27)) * 0x94D049BB133111EB & (2**64 - 1)
    return (x ^ (x >> 31)) >> 1


def simulate(exe, reelset, seed, spins, base_only):
    fd, path = tempfile.mkstemp(suffix=".json"); os.close(fd)
    try:
        # simulator <spins> <reelset.json> <runBaseOnly> <out.json> <seed>
        p = subprocess.run([exe, str(spins), reelset, "true" if base_only else "false",
                            path, str(seed)], capture_output=True, text=True,
                           stdin=subprocess.DEVNULL)
        if p.returncode != 0:
            raise RuntimeError(f"simulator failed on {reelset}:\n{p.stdout}{p.stderr}")
        with open(path) as f:
            out = json.load(f)
    finally:
        os.remove(path)
    return {k: float(out[k]) for k in ALL_STATS}


def fitness(row, goals):
    return sum(w * abs(row[k] - t) / t for k, (t, w) in goals.items())


# ---------------------------------------------------------------- report helpers
def sd(v):
    return st.stdev(v) if len(v) > 1 else float("nan")


class Report:
    def __init__(self, path):
        self.f = open(path, "w")

    def __call__(self, text=""):
        print(text)
        self.f.write(text + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--simulator", default="build/simulator")
    ap.add_argument("--results", default="Results/results.json")
    ap.add_argument("--config", default=None,
                    help="only needed if the weights can't be recovered from the results file")
    ap.add_argument("--mode", choices=["BaseGame", "FreeGame", "both"], default="both")
    ap.add_argument("--mutation", nargs="*", default=[], help="mutation counts to include (default all)")
    ap.add_argument("--runs", type=int, default=30, help="simulator seeds per reelset")
    ap.add_argument("--spins", type=int, default=10_000_000, help="spins per simulation")
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 2)
    ap.add_argument("--out", default="NoiseStudy")
    a = ap.parse_args()

    if not os.path.isfile(a.simulator):
        sys.exit(f"simulator not found at {a.simulator} (pass --simulator)")
    modes = ["BaseGame", "FreeGame"] if a.mode == "both" else [a.mode]
    with open(a.results) as f:
        data = json.load(f)
    best = best_per_combination(data, modes, [str(m) for m in a.mutation])
    if not best:
        sys.exit(f"No saved reelsets for {modes} in {a.results}")
    present = sorted({k[0] for k in best})
    goals_by_mode, goals_note = {}, {}
    for mode in present:
        goals_by_mode[mode], goals_note[mode] = fitness_goals(data, mode, a.config)

    os.makedirs(os.path.join(a.out, "reelsets"), exist_ok=True)
    report = Report(os.path.join(a.out, "report.txt"))

    # ---- write the reelsets to test ----
    items = []      # (mode, mutation, combo, seed_key, saved fitness, path)
    for (mode, m, combo), (seed_key, entry) in sorted(best.items()):
        path = os.path.join(a.out, "reelsets", f"{mode}_mutation_{m}_{combo}.json")
        r = entry["reelset"]
        with open(path, "w") as f:
            json.dump({"BaseGameReel": [unwrap(r["BaseGameReel"])],
                       "FreeGameReel": [unwrap(r["FreeGameReel"])]}, f)
        items.append((mode, m, combo, seed_key, saved_fitness(entry), path))

    total = len(items) * a.runs
    report(f"Noise study: {len(items)} reelsets x {a.runs} seeds x {a.spins:,} spins "
           f"= {total} simulations ({a.workers} in parallel)")
    for mode in present:
        g = ", ".join(f"{k} target {t:g} weight {w:g}" for k, (t, w) in goals_by_mode[mode].items())
        report(f"{mode} fitness: {g}\n    {goals_note[mode]}")

    # ---- simulate ----
    jobs = [(i, r) for i in range(len(items)) for r in range(a.runs)]
    done = [0]

    def run(job):
        i, r = job
        mode, path = items[i][0], items[i][5]
        row = simulate(a.simulator, path, seed_for(r), a.spins, base_only=(mode == "BaseGame"))
        row["fitness"] = fitness(row, goals_by_mode[mode])
        done[0] += 1
        print(f"\r  {done[0]}/{total} simulations", end="", file=sys.stderr, flush=True)
        return job, row

    with ThreadPoolExecutor(a.workers) as ex:
        rows = list(ex.map(run, jobs))
    print(file=sys.stderr)

    data = [[None] * a.runs for _ in items]
    for (i, r), row in rows:
        data[i][r] = row

    with open(os.path.join(a.out, "noise_runs.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["mode", "mutation", "combination", "from_run", "sim_run", "sim_seed",
                    *ALL_STATS, "fitness"])
        for i, (mode, m, combo, seed_key, _, _) in enumerate(items):
            for r, row in enumerate(data[i]):
                # base-only runs have no meaningful free-game stats: leave them blank
                w.writerow([mode, m, combo, seed_key, r, seed_for(r),
                            *(row[k] if k in MODE_STATS[mode] else "" for k in ALL_STATS),
                            row["fitness"]])

    summary = []
    groups = sorted({(it[0], it[1]) for it in items})
    for mode, m in groups:
        idx = [i for i, it in enumerate(items) if it[0] == mode and it[1] == m]
        metrics = MODE_STATS[mode] + ["fitness"]
        report(f"\n{'=' * 78}\n{mode}, mutation {m}: {len(idx)} combinations "
               f"(best reelset of each across GA runs)\n{'=' * 78}")
        if mode == "BaseGame":
            report("Simulated base game only, as the GA scored it.")
        report("Hit / trigger / retrigger rates are '1 in X' spins.\n")

        # 1. per-combination table: mean fitness and SD of every metric
        name_w = max(len(items[i][2]) for i in idx) + 2
        report(f"{'combination':<{name_w}}{'from':>13}{'saved fit':>11}{'mean fit':>11}"
               + "".join(f"{'SD ' + k:>{len(k) + 5}}" for k in metrics))
        sds = {k: [] for k in metrics}
        for i in idx:
            mode_, _, combo, seed_key, saved, _ = items[i]
            line = f"{combo:<{name_w}}{seed_key:>13}{saved:>11.4f}" \
                   f"{st.mean(r['fitness'] for r in data[i]):>11.4f}"
            for k in metrics:
                vals = [r[k] for r in data[i]]
                s = sd(vals)
                sds[k].append(s)
                line += f"{s:>{len(k) + 5}.4g}"
                summary.append([mode, m, combo, seed_key, k, st.mean(vals), s])
            report(line)

        # 2. thresholds
        report(f"\nSmallest difference that counts as real "
               f"(one run vs one run, independent seeds: SD(diff) = sqrt(2)*SD)")
        report(f"{'metric':<20}{'median SD':>12}{'max SD':>12}{'95% (2.77 SD)':>16}{'strict (4.24 SD)':>18}")
        for k in metrics:
            med, mx = st.median(sds[k]), max(sds[k])
            report(f"{k:<20}{med:>12.4g}{mx:>12.4g}{2.77 * mx:>16.4g}{4.24 * mx:>18.4g}")
        report("(thresholds use the max SD, so they hold for the noisiest combination)")

        # 3. common random numbers across combinations
        if len(idx) > 1:
            report("\nCommon random numbers (same seed for both reelsets): paired-difference SD")
            report("divided by the independent-seed SD, over all pairs of combinations.")
            report("Below 1 = the shared seed reduces noise when comparing these reelsets.")
            report(f"{'metric':<20}{'median':>10}{'min':>10}{'max':>10}")
            for k in metrics:
                ratios = []
                for x in range(len(idx)):
                    for y in range(x + 1, len(idx)):
                        A, B = data[idx[x]], data[idx[y]]
                        ind = math.hypot(sd([r[k] for r in A]), sd([r[k] for r in B]))
                        if ind > 0:
                            ratios.append(sd([p[k] - q[k] for p, q in zip(A, B)]) / ind)
                if ratios:
                    report(f"{k:<20}{st.median(ratios):>10.2f}{min(ratios):>10.2f}{max(ratios):>10.2f}")

        # 4. are the combinations really different?
        report("\nRanking by mean fitness over all seeds (lower = better), with a 95% interval")
        report("of the mean. Overlapping intervals = the difference is within simulation noise.")
        ranked = sorted(idx, key=lambda i: st.mean(r["fitness"] for r in data[i]))
        for i in ranked:
            v = [r["fitness"] for r in data[i]]
            half = 1.96 * sd(v) / math.sqrt(len(v))
            report(f"  {items[i][2]:<{name_w}}{st.mean(v):>10.4f}  +/- {half:.4f}")

    with open(os.path.join(a.out, "noise_summary.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["mode", "mutation", "combination", "from_run", "metric", "mean", "sd"])
        w.writerows(summary)

    report(f"\nFiles written to {a.out}/: report.txt, noise_runs.csv, noise_summary.csv, reelsets/")


if __name__ == "__main__":
    main()