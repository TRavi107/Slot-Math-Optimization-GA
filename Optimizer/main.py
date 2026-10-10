"""
Slot reelset optimizer - entry point.

Usage:
    python main.py                   # uses config.yaml
    python main.py my_config.yaml    # uses another config file

All settings live in the YAML config; nothing here needs editing for a normal run.
"""
import copy
import json
import os
import sys
import time

from Config import LoadConfig, ConfigError
from Parents import Parent, findBest
from Replacement import ReplacementType, ReplaceSingleWorstParent, GenerationalReplace
from Selection import (SelectionTypes, RouletteSelection, tournamentSelection,
                       linear_rank_weights, SUS)
from Utility import (CreateInitialPopulation, EvaluateParents, LoadInitialParents,
                     save_sim_results, save_reelset_file, Evaluate)

# ---------------- algorithm constants ----------------
ELITE_COUNT = 2            # parents carried over unchanged in ElistismGenerational
STEADY_STATE_PARENTS = 2   # parents selected per generation in SteadyState
SUS_PRESSURE = 2           # selection pressure for linear rank weights (SUS)


# ---------------- helpers ----------------
def parents_per_generation(replacement, population_size):
    """How many parents are selected each generation for a replacement strategy."""
    match replacement:
        case ReplacementType.SteadyState:
            return STEADY_STATE_PARENTS
        case ReplacementType.Generational:
            return population_size
        case ReplacementType.ElistismGenerational:
            return population_size - ELITE_COUNT
    raise ValueError(f"Unsupported replacement type: {replacement}")


def generations_for(replacement, cfg):
    """Generational strategies replace a whole batch per generation, so they run fewer generations."""
    if replacement == ReplacementType.SteadyState:
        return cfg.generations
    return max(1, cfg.generations // parents_per_generation(replacement, cfg.populationSize))


def select_parents(parents, selection, count):
    match selection:
        case SelectionTypes.TournamentSelection:
            return tournamentSelection(parents, winners=count)
        case SelectionTypes.RouletteSelection:
            return RouletteSelection(parents, count)
        case SelectionTypes.SUS:
            weights = linear_rank_weights(parents, s=SUS_PRESSURE)
            return SUS(parents, weights, count)
    raise ValueError(f"Unsupported selection type: {selection}")


def run_generation(parents, selected, replacement, mutation_count, gen, cfg, fixed_base_reels):
    """
    Produce and evaluate one generation. Returns (best_parent, mean_distance).
    fixed_base_reels: base reels every child uses in FreeGame mode (None in BaseGame mode).
    """
    if replacement == ReplacementType.SteadyState:
        return ReplaceSingleWorstParent(
            parents, cfg.spins, cfg.simulatorPath, cfg.fitnessVariables, cfg.folder,
            selected[0], selected[1], cfg.symbols, mutation_count,
            gen, cfg.gameMode, fixed_base_reels)

    elite = ELITE_COUNT if replacement == ReplacementType.ElistismGenerational else 0
    return GenerationalReplace(
        parents, selected, elite, cfg.spins, cfg.simulatorPath,
        cfg.fitnessVariables, cfg.folder, cfg.symbols, mutation_count,
        gen, cfg.gameMode, fixed_base_reels)


# ---------------- main steps ----------------
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
    print(f"[parents] Creating {cfg.populationSize} new random parents in {cfg.parentsFolder}")
    CreateInitialPopulation(cfg.parentsFolder, cfg.populationSize,
                            cfg.symbols, cfg.reelSize, cfg.columnCount)
    return LoadInitialParents(cfg.parentsFolder, cfg.populationSize, cfg.fitnessVariables)


def _base_run_parents(cfg):
    """FreeGame + same: the initial parents the BaseGame run (seed_<runNumber>) started from."""
    seed_key = f"seed_{cfg.runNumber}"
    initial = (_read_json(cfg.resultFile) or {}).get(seed_key, {}).get("initial_population")
    if not _usable(initial, f"{cfg.resultFile} [{seed_key}]", cfg):
        return None
    note = " (createNewParents ignored)" if cfg.createNewParents else ""
    print(f"[parents] FreeGame: starting from the BaseGame run's initial parents ({seed_key}){note}")
    return [Parent(cfg.fitnessVariables, s["BaseGameReel"], s["FreeGameReel"]) for s in initial]


def load_initial_parents(cfg):
    # FreeGame + same continues the BaseGame run, so it starts from the same parents
    if cfg.gameMode.name == "FreeGame" and cfg.freeGameBaseSource == "same":
        parents = _base_run_parents(cfg)
        if parents is not None:
            return parents

    if cfg.createNewParents:
        return _create_new_parents(cfg)

    seeds = _find_seed_parents(cfg)
    if seeds is None:
        print(f"[parents] Parents not found for seed_{cfg.runNumber} "
              f"(checked {cfg.resultFile} and {cfg.seedParentsFile})")
        return _create_new_parents(cfg)

    return [Parent(cfg.fitnessVariables, s["BaseGameReel"], s["FreeGameReel"]) for s in seeds]


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
    same: for every (mutation, replacement, selection) in this run, read the best base reels
    the BaseGame run with the same runNumber (seed_<runNumber>) saved for that combination.
    Everything is loaded up front so a missing entry stops the run before any spinning.
    Returns {(mutation, replacement, selection): base_reels}.
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
        for rep in cfg.replacementTypes:
            for sel in cfg.selectionTypes:
                path = f"mutation_{m}/{rep.name}_{sel.name}"
                entry = saved.get(f"mutation_{m}", {}).get(f"{rep.name}_{sel.name}")
                if entry is None:
                    missing.append(path)
                    continue
                bases[(m, rep, sel)] = _check_base_reels(
                    entry["reelset"]["BaseGameReel"], f"{seed_key}/{path}", cfg)

    if missing:
        raise ConfigError(f"freeGame: {seed_key} has no BaseGame result for: {', '.join(missing)}")
    return bases


def results_seed(cfg):
    """
    Key results are saved under: BaseGame -> seed_<n>, FreeGame -> seed_<n>_free.
    Keeping them apart lets both stages share one runNumber without the free-game
    run overwriting the BaseGame results it reads its base reels from.
    """
    return f"{cfg.runNumber}_free" if cfg.gameMode.name == "FreeGame" else cfg.runNumber


def run_optimization(initial_parents, replacement, selection, mutation_count, cfg, fixed_base_reels):
    generations = generations_for(replacement, cfg)
    parent_count = parents_per_generation(replacement, cfg.populationSize)
    print(f"\n>> {replacement.name} + {selection.name} | "
          f"mutation {mutation_count} | {generations} generations")

    parents = copy.deepcopy(initial_parents)
    gen_results = []

    # best parent seen in ANY generation (the initial population counts too).
    # Generational replacement without elitism can drop its best parent, so the
    # last generation's best is not always the best that was found.
    best_ever = copy.deepcopy(findBest(parents))
    best_ever_gen = 0

    for gen in range(generations):
        selected = select_parents(parents, selection, parent_count)
        best_parent, mean_dist = run_generation(parents, selected, replacement,
                                                mutation_count, gen, cfg, fixed_base_reels)
        gen_results.append((best_parent.fitnessValue, mean_dist))

        if best_parent.fitnessValue < best_ever.fitnessValue:   # lower = better
            best_ever = copy.deepcopy(best_parent)
            best_ever_gen = gen + 1

    save_sim_results(initial_parents, gen_results, best_ever, replacement, selection,
                     cfg.resultFile, mutation_count, results_seed(cfg))

    last_best = findBest(parents).fitnessValue
    found = f"generation {best_ever_gen}" if best_ever_gen else "the initial population"
    print(f"Best ever: fitness {best_ever.fitnessValue:.4f}, found in {found} "
          f"(last generation's best: {last_best:.4f})")
    return best_ever


def final_check(best_parent, cfg):
    """Re-run the best reelset (full game) with many spins to confirm its stats."""
    path = f"{cfg.folder}/best.json"
    save_reelset_file(best_parent.baseReelSet, best_parent.freeReelSet, path)
    print(f"Final check of best reelset with {cfg.finalCheckSpins:,} spins...")
    out = Evaluate(cfg.finalCheckSpins, path, cfg.simulatorPath)
    for label, key in [("Total RTP", "totalRTP"), ("Base RTP", "baseRTP"),
                       ("Base hit rate", "baseHitRate"), ("Free RTP", "freeRTP"),
                       ("Free hit rate", "freeHitRate"), ("Free trigger rate", "freeTriggerRate"),
                       ("Free retrigger rate", "freeReTriggerRate")]:
        print(f"  {label:<20} {out.get(key)}")


def with_base_reels(parents, base_reels):
    """Copy of parents where every parent uses the same base reels (fair free-game comparison)."""
    parents = copy.deepcopy(parents)
    for p in parents:
        p.baseReelSet = copy.deepcopy(base_reels)
    return parents


def evaluate(parents, cfg, label):
    print(f"Evaluating {len(parents)} initial parents{label}...")
    EvaluateParents(parents, cfg.spins, cfg.simulatorPath, cfg.folder,
                    cfg.gameMode.name == "BaseGame")   # BaseGame: simulate base game only


def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else "GA-config.yaml"
    try:
        cfg = LoadConfig(config_path)
        initial_parents = load_initial_parents(cfg)

        free_game = cfg.gameMode.name == "FreeGame"
        manual_base = None     # FreeGame + manual: one base for every combination
        same_bases = {}        # FreeGame + same:   base per combination
        if free_game and cfg.freeGameBaseSource == "manual":
            manual_base = base_reels_from_file(cfg)
            print(f"[free game] Base reels fixed from {cfg.baseReelFile} for all combinations")
        elif free_game:
            same_bases = base_reels_from_same_combos(cfg)
            print(f"[free game] Base reels per combination from seed_{cfg.runNumber} "
                  f"({len(same_bases)} found)")
    except (ConfigError, FileNotFoundError) as e:
        print(f"\nCONFIG ERROR: {e}\n")
        sys.exit(1)

    # BaseGame and manual: the starting population is the same for every combination,
    # so evaluate it once. "same" evaluates per combination because the base changes.
    if not same_bases:
        if manual_base is not None:
            initial_parents = with_base_reels(initial_parents, manual_base)
        evaluate(initial_parents, cfg, "")

    start = time.perf_counter()
    for mutation_count in cfg.mutationCounts:
        for replacement in cfg.replacementTypes:
            for selection in cfg.selectionTypes:
                sim_start = time.perf_counter()

                parents, base = initial_parents, manual_base
                if same_bases:
                    base = same_bases[(mutation_count, replacement, selection)]
                    parents = with_base_reels(initial_parents, base)
                    evaluate(parents, cfg, f" on {replacement.name}_{selection.name} base reels")

                best_parent = run_optimization(parents, replacement, selection,
                                               mutation_count, cfg, base)
                if cfg.finalCheckSpins > 0:
                    final_check(best_parent, cfg)
                print(f"{replacement.name}_{selection.name} took "
                      f"{time.perf_counter() - sim_start:.1f}s")

    print(f"\nTotal time: {(time.perf_counter() - start) / 60:.1f} min")


if __name__ == "__main__":
    main()