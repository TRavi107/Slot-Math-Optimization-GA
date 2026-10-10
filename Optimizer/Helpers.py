"""
Run plumbing for main.py: things that should not need editing when you change
the algorithms or the experiment.

    seeds          every seed a run uses, derived from the runNumber
    results keys   where each experiment is saved in the results file
    parents        which reelsets a run starts from
    free game      where the fixed base reels come from, checked before spinning
    run helpers    per-run config copy, final check and bestSpin record, end-of-batch summary

Careful with the seed functions: changing a label changes the random stream, so
existing seed_<n> results would no longer be reproducible.
"""
import copy
import dataclasses
import json
import os

from Baselines import BASELINE_TAG, results_key, uses_mutation
from Config import ConfigError
from Parents import Parent, OUTPUT_KEYS
from Seeding import derive_seed, make_rng
from Utility import (CreateInitialPopulation, EvaluateParents, LoadInitialParents,
                     save_reelset_file, Evaluate)


# =====================================================================
#  Seeds
# =====================================================================
def sim_seed_for(cfg):
    """
    One simulator seed for every evaluation in this run, GA and baselines alike
    (common random numbers): all reelsets see the same reel stops, so fitness
    differences come from the reels, not from spin luck.
    """
    return derive_seed(cfg.runNumber, "sim", cfg.gameMode.name)


def ga_stream_labels(cfg, mutation_count, replacement, selection):
    """Labels of one GA combination's random stream (selection, crossover, mutation)."""
    return ("ga", cfg.gameMode.name, mutation_count, replacement.name, selection.name)


def ga_seed_for(cfg, mutation_count, replacement, selection):
    return derive_seed(cfg.runNumber, *ga_stream_labels(cfg, mutation_count, replacement, selection))


def baseline_stream_labels(cfg, method, mutation_count):
    """
    Labels of one baseline's random stream. RandomSearch ignores the mutation count,
    so it has one stream per run: its result is identical under every mutation_<m> key.
    """
    if not uses_mutation(method):
        return ("baseline", cfg.gameMode.name, method.name)
    return ("baseline", cfg.gameMode.name, method.name, mutation_count)


def baseline_seed_for(cfg, method, mutation_count):
    return derive_seed(cfg.runNumber, *baseline_stream_labels(cfg, method, mutation_count))


def _final_check_seed(cfg, mutation_count, first, second):
    return derive_seed(cfg.runNumber, "final_check", cfg.gameMode.name,
                       mutation_count, first, second)


def final_check_seed_for(cfg, mutation_count, replacement, selection):
    """Different from sim_seed, so the final check is an independent validation."""
    return _final_check_seed(cfg, mutation_count, replacement.name, selection.name)


def baseline_final_check_seed_for(cfg, method, mutation_count):
    m = mutation_count if uses_mutation(method) else "any"
    return _final_check_seed(cfg, m, method.name, BASELINE_TAG)


# =====================================================================
#  Results keys
# =====================================================================
def ga_key(replacement, selection):
    return f"{replacement.name}_{selection.name}"


def experiment_keys(cfg):
    """Results key of every experiment run per mutation count: GA combinations, then baselines."""
    keys = []
    if cfg.runGA:
        keys += [ga_key(rep, sel) for rep in cfg.replacementTypes for sel in cfg.selectionTypes]
    keys += [results_key(b) for b in cfg.baselineTypes]
    return keys


def results_seed(cfg):
    """
    Key results are saved under: BaseGame -> seed_<n>, FreeGame -> seed_<n>_free.
    Keeping them apart lets both stages share one runNumber without the free-game
    run overwriting the BaseGame results it reads its base reels from.
    """
    return f"{cfg.runNumber}_free" if cfg.gameMode.name == "FreeGame" else cfg.runNumber


# =====================================================================
#  Starting parents
# =====================================================================
def _read_json(path):
    """Return parsed JSON, or None if the file is missing, empty or broken."""
    if not os.path.isfile(path) or os.path.getsize(path) == 0:
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"[parents] WARNING: could not read {path} ({e})")
        return None


def _usable(reelsets, source, cfg):
    """Check a list of {BaseGameReel, FreeGameReel} entries matches the population size."""
    if not reelsets:
        return False
    if len(reelsets) != cfg.populationSize:
        print(f"[parents] {source} has {len(reelsets)} parents but populationSize is "
              f"{cfg.populationSize} - ignoring it")
        return False
    return True


def _find_seed_parents(cfg):
    """
    Look for existing initial parents, in this order:
      1. results file -> seed_<runNumber> -> initial_population
      2. paths.seedParentsFile
    Returns a list of {BaseGameReel, FreeGameReel} dicts, or None if nothing usable.
    """
    seed_key = f"seed_{cfg.runNumber}"

    results = _read_json(cfg.resultFile) or {}
    initial = results.get(seed_key, {}).get("initial_population")
    if _usable(initial, f"{cfg.resultFile} [{seed_key}]", cfg):
        print(f"[parents] Using initial parents of {seed_key} from {cfg.resultFile}")
        return initial

    seed_file = _read_json(cfg.seedParentsFile)
    if _usable(seed_file, cfg.seedParentsFile, cfg):
        print(f"[parents] Using seed parents from {cfg.seedParentsFile}")
        return seed_file

    return None


def _create_new_parents(cfg):
    # seeded: the same runNumber always generates the same initial population
    rng = make_rng(cfg.runNumber, "initial_population")
    print(f"[parents] Creating {cfg.populationSize} new random parents in {cfg.parentsFolder} "
          f"(seed {cfg.runNumber})")
    CreateInitialPopulation(cfg.parentsFolder, cfg.populationSize,
                            cfg.symbols, cfg.reelSize, cfg.columnCount, rng)
    return LoadInitialParents(cfg.parentsFolder, cfg.populationSize, cfg.fitnessVariables)


def _base_run_parents(cfg):
    """FreeGame + same: the initial parents the BaseGame run (seed_<runNumber>) started from."""
    seed_key = f"seed_{cfg.runNumber}"
    initial = (_read_json(cfg.resultFile) or {}).get(seed_key, {}).get("initial_population")
    if not _usable(initial, f"{cfg.resultFile} [{seed_key}]", cfg):
        return None
    print(f"[parents] FreeGame: starting from the BaseGame run's initial parents ({seed_key})")
    return [Parent(cfg.fitnessVariables, s["BaseGameReel"], s["FreeGameReel"]) for s in initial]


def load_initial_parents(cfg):
    """
    The parents a run starts from, in this order:
      1. FreeGame + same: the parents the BaseGame run with this runNumber started from
      2. results file -> seed_<runNumber> -> initial_population (re-running or extending a run)
      3. paths.seedParentsFile (a fixed starting set you provide)
      4. otherwise new random parents, seeded by the runNumber
    Saved parents always win over regenerating them: they are what the run really used,
    even if the reel layout or generator has changed since, or the run predates seeding.
    For fresh parents, use a new runNumber.
    """
    # FreeGame + same continues the BaseGame run, so it starts from the same parents
    if cfg.gameMode.name == "FreeGame" and cfg.freeGameBaseSource == "same":
        parents = _base_run_parents(cfg)
        if parents is not None:
            return parents

    seeds = _find_seed_parents(cfg)
    if seeds is None:
        print(f"[parents] No saved parents for seed_{cfg.runNumber} "
              f"(checked {cfg.resultFile} and {cfg.seedParentsFile})")
        return _create_new_parents(cfg)

    return [Parent(cfg.fitnessVariables, s["BaseGameReel"], s["FreeGameReel"]) for s in seeds]


def with_base_reels(parents, base_reels):
    """Copy of parents where every parent uses the same base reels (fair free-game comparison)."""
    parents = copy.deepcopy(parents)
    for p in parents:
        p.baseReelSet = copy.deepcopy(base_reels)
    return parents


def evaluate_population(parents, cfg, label):
    """Simulate and score every parent (BaseGame mode: base game only)."""
    print(f"Evaluating {len(parents)} initial parents{label}...")
    EvaluateParents(parents, cfg.spins, cfg.simulatorPath, cfg.folder,
                    cfg.gameMode.name == "BaseGame",
                    sim_seed_for(cfg))


# =====================================================================
#  Free game: fixed base reels
# =====================================================================
def _unwrap_reelset(reels):
    """Parent files written by save_reelset_file have an extra list level: [[reel0, reel1, ...]]."""
    if reels and isinstance(reels[0], list) and reels[0] and isinstance(reels[0][0], list):
        return reels[0]
    return reels


def _check_base_reels(reels, where, cfg):
    reels = _unwrap_reelset(reels)
    if len(reels) != cfg.columnCount:
        raise ConfigError(f"freeGame: base reels from {where} have {len(reels)} reels, "
                          f"expected {cfg.columnCount}")
    unknown = {s for reel in reels for s in reel} - set(cfg.symbols)
    if unknown:
        raise ConfigError(f"freeGame: base reels from {where} contain unknown symbols {sorted(unknown)}")
    return copy.deepcopy(reels)


def base_reels_from_file(cfg):
    """manual: one reelset file, used for every combination."""
    data = _read_json(cfg.baseReelFile)
    if data is None:
        raise ConfigError(f"freeGame: base reel file '{cfg.baseReelFile}' not found or empty")
    reels = data["BaseGameReel"] if isinstance(data, dict) else data
    return _check_base_reels(reels, cfg.baseReelFile, cfg)


def base_reels_from_same_combos(cfg):
    """
    same: for every experiment in this run (each GA combination and each baseline, per
    mutation count), read the best base reels the BaseGame run with the same runNumber
    (seed_<runNumber>) saved for that same experiment. A baseline's free-game stage
    therefore continues that baseline's own base-game result.
    Everything is loaded up front so a missing entry stops the run before any spinning.
    Returns {(mutation, results key): base_reels}.
    """
    data = _read_json(cfg.resultFile)
    if data is None:
        raise ConfigError(f"freeGame: results file '{cfg.resultFile}' not found or empty. "
                          "Run a BaseGame optimization first, or use baseReelSource: manual")

    seed_key = f"seed_{cfg.runNumber}"
    if seed_key not in data:
        raise ConfigError(f"freeGame: no BaseGame results for runNumber {cfg.runNumber} "
                          f"('{seed_key}') in {cfg.resultFile}. Run BaseGame mode with this "
                          f"runNumber first. Available: {', '.join(data) or 'none'}")
    saved = data[seed_key].get("results", {})

    bases = {}
    missing = []
    for m in cfg.mutationCounts:
        for key in experiment_keys(cfg):
            path = f"mutation_{m}/{key}"
            entry = saved.get(f"mutation_{m}", {}).get(key)
            if entry is None:
                missing.append(path)
                continue
            bases[(m, key)] = _check_base_reels(
                entry["reelset"]["BaseGameReel"], f"{seed_key}/{path}", cfg)

    if missing:
        raise ConfigError(f"freeGame: {seed_key} has no BaseGame result for: {', '.join(missing)}")
    return bases


def preflight(cfg):
    """
    Check every run can start before any spinning, so a 30-run batch can't fail
    hours in because run 17 has no BaseGame results to read.
    """
    if cfg.gameMode.name != "FreeGame":
        return
    if cfg.freeGameBaseSource == "manual":
        base_reels_from_file(cfg)
        return
    for n in cfg.runNumbers:
        base_reels_from_same_combos(for_run(cfg, n))


# =====================================================================
#  Run helpers
# =====================================================================
def for_run(cfg, run_number):
    """Copy of the config for one run: identical settings, this run number as the seed."""
    return dataclasses.replace(cfg, runNumber=run_number)


def final_check(best_parent, cfg, seed):
    """Re-run the best reelset (full game) with many spins to confirm its stats.
    Returns the simulator output."""
    path = f"{cfg.folder}/best.json"
    save_reelset_file(best_parent.baseReelSet, best_parent.freeReelSet, path)
    print(f"Final check of best reelset with {cfg.finalCheckSpins:,} spins (seed {seed})...")
    out = Evaluate(cfg.finalCheckSpins, path, cfg.simulatorPath, seed)
    for label, key in [("Total RTP", "totalRTP"), ("Base RTP", "baseRTP"),
                       ("Base hit rate", "baseHitRate"), ("Free RTP", "freeRTP"),
                       ("Free hit rate", "freeHitRate"), ("Free trigger rate", "freeTriggerRate"),
                       ("Free retrigger rate", "freeReTriggerRate")]:
        print(f"  {label:<20} {out.get(key)}")
    return out


def best_spin_record(output, cfg, source, full_game, spins):
    """
    The best reelset's stats, as saved under "bestSpin":
        source          finalCheck (re-run with finalCheckSpins) or optimizationRun
                        (finalCheckSpins is 0: the stats it was scored on during the run)
        spins           how many spins these numbers come from
        seed            simulator seed of that simulation
        fullGame        false = base game only (BaseGame tuning skips playing free spins,
                        so free-game stats there are not meaningful)
        fitness         fitness of these stats (same formula as the optimizer; lower = better)
        simOutput       the simulator's full output
        expectedOutput  the target of every enabled goal, by simulator key
        errorPercent    (actual - target) / target * 100 per goal; + = above target
    """
    expected, error = {}, {}
    fitness = 0.0
    for var in cfg.fitnessVariables:
        key = OUTPUT_KEYS[var.varName]
        actual, target = output[key], var.targetValue
        expected[key] = target
        error[key] = round((actual - target) / target * 100, 4)
        fitness += abs(actual - target) / target * var.weight
    return {
        "source": source,
        "spins": output.get("spinCount", spins),
        "seed": str(output.get("seed", "")),
        "fullGame": full_game,
        "fitness": fitness,
        "simOutput": output,
        "expectedOutput": expected,
        "errorPercent": error,
    }


def check_best(best_parent, cfg, seed):
    """
    bestSpin record for one experiment's best reelset: re-checked with finalCheckSpins
    if that is on, otherwise the output it was scored on during the optimization run.
    """
    if cfg.finalCheckSpins > 0:
        out = final_check(best_parent, cfg, seed)
        return best_spin_record(out, cfg, "finalCheck", True, cfg.finalCheckSpins)

    if best_parent.simOutput is None:
        raise ValueError("best reelset has no simulator output - it was never evaluated")
    record = best_spin_record(best_parent.simOutput, cfg, "optimizationRun",
                              cfg.gameMode.name != "BaseGame", cfg.spins)
    print(f"Best reelset stats from the optimization run ({record['spins']:,} spins; "
          f"finalCheckSpins is 0): fitness {record['fitness']:.4f}")
    return record


def print_summary(all_results):
    """Best fitness per combination (rows) for every run (columns)."""
    if len(all_results) < 2:
        return
    runs = list(all_results)
    labels = [label for label, _ in all_results[runs[0]]]
    width = max(len(l) for l in labels) + 2
    print("\n================ Best fitness per run ================")
    print(f"{'combination':<{width}}" + "".join(f"{'seed_' + str(r):>12}" for r in runs)
          + f"{'mean':>12}")
    for i, label in enumerate(labels):
        values = [all_results[r][i][1] for r in runs]
        print(f"{label:<{width}}" + "".join(f"{v:>12.4f}" for v in values)
              + f"{sum(values) / len(values):>12.4f}")