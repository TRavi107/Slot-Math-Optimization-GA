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
from Parents import Parent, findBest, findBestIndex ,GameMode
from Replacement import ReplacementType, ReplaceSingleWorstParent, GenerationalReplace
from Selection import (SelectionTypes, RouletteSelection, tournamentSelection,
                       linear_rank_weights, SUS)
from Utility import (CreateInitialPopulation, EvaluateParents, LoadInitialParents,
                     save_sim_results, Evaluate)

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


def run_generation(parents, selected, replacement, mutation_count, gen, cfg):
    """Produce and evaluate one generation. Returns (best_parent, mean_distance)."""
    fixed_base_reels = parents[cfg.bestParentIndex].baseReelSet   # used in FreeGame mode

    if replacement == ReplacementType.SteadyState:
        return ReplaceSingleWorstParent(
            parents, cfg.spins, cfg.simulatorPath, cfg.fitnessVariables, cfg.folder,
            selected[0], selected[1], cfg.symbols, mutation_count,
            gen, cfg.gameMode, fixed_base_reels)

    elite = ELITE_COUNT if replacement == ReplacementType.ElistismGenerational else 0
    return GenerationalReplace(
        parents, selected, elite, cfg.spins, cfg.simulatorPath,
        cfg.fitnessVariables, cfg.folder, cfg.symbols, mutation_count,
        gen, cfg.gameMode, fixed_base_reels )


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


def load_initial_parents(cfg):
    if cfg.createNewParents:
        return _create_new_parents(cfg)

    seeds = _find_seed_parents(cfg)
    if seeds is None:
        print(f"[parents] Parents not found for seed_{cfg.runNumber} "
              f"(checked {cfg.resultFile} and {cfg.seedParentsFile})")
        return _create_new_parents(cfg)

    return [Parent(cfg.fitnessVariables, s["BaseGameReel"], s["FreeGameReel"]) for s in seeds]


def run_optimization(initial_parents, replacement, selection, mutation_count, cfg):
    generations = generations_for(replacement, cfg)
    parent_count = parents_per_generation(replacement, cfg.populationSize)
    print(f"\n>> {replacement.name} + {selection.name} | "
          f"mutation {mutation_count} | {generations} generations")

    parents = copy.deepcopy(initial_parents)
    gen_results = []

    for gen in range(generations):
        selected = select_parents(parents, selection, parent_count)
        best_parent, mean_dist = run_generation(parents, selected, replacement,
                                                mutation_count, gen, cfg)
        gen_results.append((best_parent.fitnessValue, mean_dist))

    save_sim_results(initial_parents, gen_results, findBest(parents), replacement, selection,
                     cfg.resultFile, mutation_count, cfg.runNumber)

    best_index = findBestIndex(parents)
    print(f"Best parent is {best_index}")
    return best_index


def final_check(best_index, cfg):
    """Re-run the best reelset with many spins to confirm its stats."""
    path = f"{cfg.folder}/parent{best_index}.json"
    print(f"Final check of {path} with {cfg.finalCheckSpins:,} spins...")
    out = Evaluate(cfg.finalCheckSpins, path, cfg.simulatorPath)
    for label, key in [("Total RTP", "totalRTP"), ("Base RTP", "baseRTP"),
                       ("Base hit rate", "baseHitRate"), ("Free RTP", "freeRTP"),
                       ("Free hit rate", "freeHitRate"), ("Free trigger rate", "freeTriggerRate"),
                       ("Free retrigger rate", "freeReTriggerRate")]:
        print(f"  {label:<20} {out.get(key)}")


def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else "GA-config.yaml"
    try:
        cfg = LoadConfig(config_path)
        initial_parents = load_initial_parents(cfg)
    except (ConfigError, FileNotFoundError) as e:
        print(f"\nCONFIG ERROR: {e}\n")
        sys.exit(1)

    print(f"Evaluating {len(initial_parents)} initial parents...")
    EvaluateParents(initial_parents, cfg.spins, cfg.simulatorPath, cfg.folder, 
                    cfg.gameMode == GameMode.BaseGame)

    start = time.perf_counter()
    for mutation_count in cfg.mutationCounts:
        for replacement in cfg.replacementTypes:
            for selection in cfg.selectionTypes:
                sim_start = time.perf_counter()
                best_index = run_optimization(initial_parents, replacement, selection,
                                              mutation_count, cfg)
                if cfg.finalCheckSpins > 0:
                    final_check(best_index, cfg)
                print(f"{replacement.name}_{selection.name} took "
                      f"{time.perf_counter() - sim_start:.1f}s")

    print(f"\nTotal time: {(time.perf_counter() - start) / 60:.1f} min")


if __name__ == "__main__":
    main()