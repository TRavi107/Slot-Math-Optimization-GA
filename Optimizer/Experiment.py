"""
Run every Selection x Replacement combination on the SAME starting
population(s) with the SAME evaluation budget, and log everything
needed to compare them.

    python Optimizer/experiment.py     # runs (resumable: finished runs are skipped)
    python Optimizer/compare.py        # plots + summary table
"""
import copy
import csv
import glob
import itertools
import json
import os
import random
import time

from Parents import Parent, FitnessVariable, VariableType, findBest
from Selection import (SelectionTypes, tournamentSelection, RouletteSelection,
                       SUS, linear_rank_weights)
from Replacement import ReplacementType, ReplaceSingleWorstParent, GenerationalReplace
from FitnessFunction import Evaluate, evaluate_parent
from Utility import generate_reelset, save_reelset_file, UpdateParentVars

# ---------------- problem ----------------
SYMBOLS = ["AA", "BB", "CC", "DD", "EE", "FF", "GG", "WD", "SC"]
REEL_SIZE = 50
COLUMNS = 5
FITNESS_VARS = [
    FitnessVariable(VariableType.baseRTP,         0, .57, 10),
    FitnessVariable(VariableType.baseHitRate,     0, 3,    5),
    FitnessVariable(VariableType.freeRTP,         0, .38, 10),
    FitnessVariable(VariableType.freeHitRate,     0, 2.7,  5),
    FitnessVariable(VariableType.freeTriggerRate, 0, 80,   3),
]

# ---------------- experiment ----------------
POP_SIZE = 10
N_ELITE = 2                 # for ElistismGenerational
MUTATIONS = 10
SPINS = 10_000_000          # spins per evaluation during the GA
VERIFY_SPINS = 100_000_000  # spins for the final, low-noise check of each run's best
EVAL_BUDGET = 200           # simulator calls per run, identical for every combo
SEEDS = [1, 2, 3]           # each seed = a different starting population
FITNESS_THRESHOLD = 1.0     # record when a run's best first drops below this

SELECTIONS = list(SelectionTypes)
REPLACEMENTS = list(ReplacementType)

SIMULATOR = "build/simulator"
RUNS_DIR = "Optimizer/Runs"
RESULTS_DIR = "Optimizer/Results"


# ---------------- per-type settings ----------------
def parents_needed(rep):
    return {ReplacementType.SteadyState: 2,
            ReplacementType.Generational: POP_SIZE,
            ReplacementType.ElistismGenerational: POP_SIZE - N_ELITE}[rep]


def evals_per_gen(rep):
    return {ReplacementType.SteadyState: 1,
            ReplacementType.Generational: POP_SIZE,
            ReplacementType.ElistismGenerational: POP_SIZE - N_ELITE}[rep]


def select(parents, sel, n):
    match sel:
        case SelectionTypes.TournamentSelection:
            return tournamentSelection(parents, winners=n)
        case SelectionTypes.RouletteSelection:
            return RouletteSelection(parents, n)
        case SelectionTypes.SUS:
            return SUS(parents, linear_rank_weights(parents, s=2), n)
        case _:
            raise ValueError(f"unknown selection {sel}")


def replace(parents, rep, selected, folder, gen):
    match rep:
        case ReplacementType.SteadyState:
            ReplaceSingleWorstParent(parents, SPINS, SIMULATOR, FITNESS_VARS, folder,
                                     selected[0], selected[1], SYMBOLS, MUTATIONS, gen)
        case ReplacementType.Generational:
            GenerationalReplace(parents, selected, 0, SPINS, SIMULATOR,
                                FITNESS_VARS, folder, SYMBOLS, MUTATIONS, gen)
        case ReplacementType.ElistismGenerational:
            GenerationalReplace(parents, selected, N_ELITE, SPINS, SIMULATOR,
                                FITNESS_VARS, folder, SYMBOLS, MUTATIONS, gen)
        case _:
            raise ValueError(f"unknown replacement {rep}")


# ---------------- logging helpers ----------------
def var_values(parent):
    return {v.varName.name: v.currentValue for v in parent.fitnessVariable}


def snapshot(parents, gen, evals, elapsed):
    fits = [p.fitnessValue for p in parents]
    genomes = {json.dumps([p.baseReelSet, p.freeReelSet]) for p in parents}
    return {
        "gen": gen,
        "evals": evals,
        "time": elapsed,
        "best": min(fits),
        "mean": sum(fits) / len(fits),
        "worst": max(fits),
        "diversity": len(genomes),          # number of distinct reelsets
        "best_vars": var_values(findBest(parents)),
    }


# ---------------- initial population (shared by all combos of a seed) ----------------
def initial_population(seed):
    """Create + evaluate once per seed, cached on disk so reruns are free."""
    folder = f"{RUNS_DIR}/initial_s{seed}"
    cache = f"{folder}/population.json"

    if os.path.exists(cache):
        with open(cache) as f:
            data = json.load(f)
        pop = []
        for d in data:
            p = Parent(FITNESS_VARS, d["base"], d["free"])
            UpdateParentVars(p, d["metrics"])
            pop.append(p)
        return pop

    rng = random.Random(seed)
    pop, data = [], []
    for i in range(POP_SIZE):
        p = Parent(FITNESS_VARS,
                   generate_reelset(SYMBOLS, REEL_SIZE, COLUMNS, rng),
                   generate_reelset(SYMBOLS, REEL_SIZE, COLUMNS, rng))
        metrics = evaluate_parent(p, SPINS, SIMULATOR, f"{folder}/parent{i}.json")
        pop.append(p)
        data.append({"base": p.baseReelSet, "free": p.freeReelSet, "metrics": metrics})
        print(f"[init s{seed}] parent{i}: fitness {p.fitnessValue:.4f}")

    with open(cache, "w") as f:
        json.dump(data, f)
    return pop


# ---------------- one run ----------------
def run_name(sel, rep, seed):
    return f"{sel.name}__{rep.name}__s{seed}"


def run_one(sel, rep, seed, initial):
    name = run_name(sel, rep, seed)
    folder = f"{RUNS_DIR}/{name}"
    random.seed(f"{name}")                   # reproducible GA randomness per run

    parents = copy.deepcopy(initial)         # every combo starts from the same population
    for i, p in enumerate(parents):
        save_reelset_file(p.baseReelSet, p.freeReelSet, f"{folder}/parent{i}.json")

    history = [snapshot(parents, 0, 0, 0.0)]
    evals, gen = 0, 0
    evals_to_threshold = 0 if history[0]["best"] <= FITNESS_THRESHOLD else None
    start = time.perf_counter()

    while evals + evals_per_gen(rep) <= EVAL_BUDGET:
        selected = select(parents, sel, parents_needed(rep))
        replace(parents, rep, selected, folder, gen)
        evals += evals_per_gen(rep)
        gen += 1

        snap = snapshot(parents, gen, evals, time.perf_counter() - start)
        history.append(snap)
        if evals_to_threshold is None and snap["best"] <= FITNESS_THRESHOLD:
            evals_to_threshold = evals
        print(f"[{name}] gen {gen:4d} | evals {evals:4d} | best {snap['best']:.4f} "
              f"| mean {snap['mean']:.4f} | distinct {snap['diversity']}")

    ga_time = time.perf_counter() - start

    # Re-evaluate the final best with many more spins: removes "lucky evaluation" bias
    best = findBest(parents)
    best_path = f"{folder}/best.json"
    save_reelset_file(best.baseReelSet, best.freeReelSet, best_path)
    t = time.perf_counter()
    verified = copy.deepcopy(best)
    UpdateParentVars(verified, Evaluate(VERIFY_SPINS, best_path, SIMULATOR))
    verify_time = time.perf_counter() - t

    result = {
        "selection": sel.name,
        "replacement": rep.name,
        "seed": seed,
        "config": {"pop_size": POP_SIZE, "n_elite": N_ELITE, "mutations": MUTATIONS,
                   "spins": SPINS, "verify_spins": VERIFY_SPINS, "eval_budget": EVAL_BUDGET},
        "generations": gen,
        "evals": evals,
        "ga_time": ga_time,
        "verify_time": verify_time,
        "evals_to_threshold": evals_to_threshold,
        "final_best_noisy": best.fitnessValue,
        "final_best_verified": verified.fitnessValue,
        "verified_vars": var_values(verified),
        "final_diversity": history[-1]["diversity"],
        "history": history,
    }
    with open(f"{RESULTS_DIR}/{name}.json", "w") as f:
        json.dump(result, f, indent=1)
    return result


# ---------------- summary ----------------
def write_summary_csv():
    rows = []
    for path in sorted(glob.glob(f"{RESULTS_DIR}/*__s*.json")):
        with open(path) as f:
            r = json.load(f)
        row = {k: r[k] for k in ("selection", "replacement", "seed", "generations", "evals",
                                 "ga_time", "evals_to_threshold", "final_best_noisy",
                                 "final_best_verified", "final_diversity")}
        row.update({f"verified_{k}": v for k, v in r["verified_vars"].items()})
        rows.append(row)
    if not rows:
        return
    with open(f"{RESULTS_DIR}/summary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {RESULTS_DIR}/summary.csv ({len(rows)} runs)")


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    combos = list(itertools.product(SELECTIONS, REPLACEMENTS))
    print(f"{len(combos)} combos x {len(SEEDS)} seeds, budget {EVAL_BUDGET} evals each")

    for seed in SEEDS:
        pending = [(s, r) for s, r in combos
                   if not os.path.exists(f"{RESULTS_DIR}/{run_name(s, r, seed)}.json")]
        if not pending:
            continue
        initial = initial_population(seed)
        for sel, rep in pending:
            print(f"\n=== {run_name(sel, rep, seed)} ===")
            run_one(sel, rep, seed, initial)

    write_summary_csv()


if __name__ == "__main__":
    main()