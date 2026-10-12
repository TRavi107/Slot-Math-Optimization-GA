"""
Set up experiment 2: the FreeGame stage re-run with ONE fixed base reelset for every method and seed.

Why: in Both mode each combination's free stage starts from the base reels that same combination found,
so free-game differences mix free-stage search quality with base-stage luck. Fixing the base reels
removes that confound. Everything else (seeds, initial free reels, budget, spins, sessions mode,
final check) stays as in the original sweep.

What it writes (nothing existing is modified):
  1. <base-file>      the fixed base reelset   (default Optimizer/ReelSets/fixed_base.json)
  2. <out-results>    a copy of the results with only the BaseGame entries (seed_<n>), no seed_<n>_free.
                      The new runs read their initial parents from it and write their own seed_<n>_free,
                      so old Both-mode free results can never mix with the new ones.
  3. <config-out>     a FreeGame config pointing at 1 and 2 (comments from the original are not kept).

Usage (from the "Math Optimization" folder):
    python Optimizer/prepare_fixedbase.py GA-config.yaml
    python Optimizer/prepare_fixedbase.py GA-config.yaml --base seed_18/mutation_1/SteadyState_RouletteSelection
    python Optimizer/prepare_fixedbase.py GA-config.yaml --mutations 3,5 --baselines HillClimbing,SimulatedAnnealing

Then (a fresh Parallel/ folder is required, see the printed notes):
    python Optimizer/run_parallel.py launch GA-config-fixedbase.yaml --runs 1-30 --threads 10
    python Optimizer/run_parallel.py merge  GA-config-fixedbase.yaml --runs 1-30
"""
import argparse
import copy
import json
import os
import re

import yaml


def pick_base(results, spec):
    """spec 'auto' = the BaseGame result with the lowest final-check fitness, else seed_k/mutation_m/Combo."""
    if spec != "auto":
        seed_key, mut_key, combo = spec.split("/")
        entry = results[seed_key]["results"][mut_key][combo]
        return spec, entry
    best = None
    for seed_key, s in results.items():
        if not re.match(r"^seed_\d+$", seed_key):
            continue
        for mut_key, combos in s.get("results", {}).items():
            for combo, entry in combos.items():
                bs = entry.get("bestSpin") or {}
                if bs.get("source") != "finalCheck" or "RandomSearch" in combo:
                    continue
                if best is None or bs["fitness"] < best[0]:
                    best = (bs["fitness"], f"{seed_key}/{mut_key}/{combo}", entry)
    if best is None:
        raise SystemExit("no BaseGame result with a final check found")
    return best[1], best[2]


def main():
    ap = argparse.ArgumentParser(description="Prepare the fixed-base-reels FreeGame experiment.")
    ap.add_argument("config", nargs="?", default="GA-config.yaml")
    ap.add_argument("--results", default=None, help="default: paths.resultFile of the config")
    ap.add_argument("--base", default="auto", help="'auto' (best final-check fitness) or seed_k/mutation_m/Combo")
    ap.add_argument("--base-file", default="Optimizer/ReelSets/fixed_base.json")
    ap.add_argument("--out-results", default="Results/results_fixedbase.json")
    ap.add_argument("--config-out", default="GA-config-fixedbase.yaml")
    ap.add_argument("--mutations", default="3,5,10")
    ap.add_argument("--baselines", default="HillClimbing,SimulatedAnnealing",
                    help="comma list; RandomSearch is left out by default (it ignores the base reels' "
                         "quality and is slow)")
    ap.add_argument("--runs", default="1-30")
    ap.add_argument("--final-check-spins", default="100_000_000", help="keep equal to the original sweep")
    args = ap.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    results_path = args.results or cfg["paths"]["resultFile"]
    with open(results_path) as f:
        results = json.load(f)

    # 1. fixed base reels
    source, entry = pick_base(results, args.base)
    bs = entry.get("bestSpin") or {}
    out = bs.get("simOutput", {})
    os.makedirs(os.path.dirname(args.base_file) or ".", exist_ok=True)
    with open(args.base_file, "w") as f:
        json.dump({"BaseGameReel": entry["reelset"]["BaseGameReel"], "source": source,
                   "finalCheck": {k: out.get(k) for k in ("baseRTP", "baseHitRate", "freeTriggerRate")}
                   | {"fitness": bs.get("fitness"), "spins": bs.get("spins")}}, f, indent=1)
    print(f"[1] fixed base reels: {source}  fitness {bs.get('fitness'):.4f}  baseRTP {out.get('baseRTP'):.4f}  "
          f"hit 1 in {out.get('baseHitRate'):.4f}  trigger 1 in {out.get('freeTriggerRate'):.2f}  -> {args.base_file}")

    # 2. results copy with BaseGame entries only
    base_only = {k: v for k, v in results.items() if re.match(r"^seed_\d+$", k)}
    dropped = len(results) - len(base_only)
    os.makedirs(os.path.dirname(args.out_results) or ".", exist_ok=True)
    with open(args.out_results, "w") as f:
        json.dump(base_only, f)
    print(f"[2] {len(base_only)} BaseGame entries (initial parents included), {dropped} free entries left out "
          f"-> {args.out_results}")

    # 3. config
    new = copy.deepcopy(cfg)
    new["run"]["gameMode"] = "FreeGame"
    new["run"]["runNumbers"] = args.runs
    new["run"]["finalCheckSpins"] = int(str(args.final_check_spins).replace("_", ""))
    fg = new.setdefault("freeGame", {})
    fg["baseReelSource"] = "manual"
    fg["baseReelFile"] = args.base_file
    fg.setdefault("evaluation", "sessions")
    fg.setdefault("sessions", "auto")
    new["experiments"]["runGA"] = True
    new["experiments"]["mutationCounts"] = [int(m) for m in args.mutations.split(",")]
    new.setdefault("baselines", {})["methods"] = [b for b in args.baselines.split(",") if b]
    new["paths"]["resultFile"] = args.out_results
    with open(args.config_out, "w", encoding="utf-8") as f:
        f.write("# Experiment 2: FreeGame stage with one fixed base reelset (made by prepare_fixedbase.py)\n")
        yaml.safe_dump(new, f, sort_keys=False)
    r = new["run"]
    print(f"[3] config -> {args.config_out}: FreeGame, base manual, mutations {new['experiments']['mutationCounts']}, "
          f"baselines {new['baselines']['methods']}, spins {r['spins']}, generations {r['generations']}, "
          f"population {r['populationSize']}, finalCheckSpins {r['finalCheckSpins']:,}, "
          f"evaluation {fg['evaluation']}")

    # notes
    orig_spins = {results[k]["meta"].get("spins") for k in base_only if "meta" in results[k]}
    if orig_spins and int(str(r["spins"]).replace("_", "")) not in {int(s) for s in orig_spins}:
        print(f"WARNING: run.spins {r['spins']} differs from the original sweep {orig_spins}")
    if os.path.isdir("Parallel"):
        print("NOTE: a Parallel/ folder exists. run_parallel.py skips any run_<n> that has a DONE marker, so "
              "move it away first (e.g. mv Parallel Parallel_sweep1), or every run will be skipped.")
    print("NOTE: use a new S3 prefix for this experiment (e.g. s3://<bucket>/fixedbase), so 'pull' does not "
          "fetch the old sweep's finished runs.")


if __name__ == "__main__":
    main()