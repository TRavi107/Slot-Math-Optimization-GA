"""
Slot reelset optimizer - entry point.

Usage:
    python main.py                   # uses GA-config.yaml
    python main.py my_config.yaml    # uses another config file

All settings live in the YAML config; nothing here needs editing for a normal run.
This file holds the experiment itself: the GA's settings and generation loop, the
baseline runner and the sweep over runs, stages and combinations. The run plumbing
that shouldn't need editing (seeds, starting parents, free-game base reels, summary)
lives in Helpers.py.

GAME MODES (run.gameMode)
    BaseGame   tune the base reels                         -> saved under seed_<n>
    FreeGame   keep base reels fixed, tune the free reels  -> saved under seed_<n>_free
    Both       for every run number: the whole BaseGame sweep first, then the whole
               FreeGame sweep. Each free-game combination (mutation + replacement +
               selection, or mutation + baseline) uses the best base reels that SAME
               combination just found in the BaseGame stage as its fixed base reels,
               and starts from the same initial parents. Results are identical to
               running BaseGame and then FreeGame (baseReelSource: same) separately
               with the same run number and settings.

MULTIPLE RUNS
    run.runNumbers lists the runs to execute, e.g. [1, 2, 3] or "1-30".
    The whole experiment sweep is repeated once per run number, and each run is
    saved under its own seed_<n> - exactly as if it had been run on its own.
    To re-create one run later, set runNumbers: [n] with the same config.

REPRODUCIBILITY
    Each run number is that run's master seed. Every random choice (initial
    parents, selection, crossover, mutation) and every simulator call is seeded
    from it, so the same run number + config reproduces seed_<n> exactly.
    Each (gameMode, mutation, replacement, selection) combination has its own
    random stream, so running a single combination gives the same result as
    running it inside a full sweep. Each baseline has its own stream too.

BASELINES
    baselines.methods adds Random search, Hill climbing (1+1)-EA and Simulated
    annealing to every run. They get the GA's budget (run.generations evaluations),
    its starting reelsets (they start from the best initial parent), its spins and
    its simulator seed, and are saved next to the GA under
        seed_<n> -> results -> mutation_<m> -> <Method>_Baseline
    Set experiments.runGA: false to add baselines to runs whose GA results already
    exist, without re-running the GA (each run starts from the initial_population
    saved for it in the results file).

STARTING PARENTS
    A run reuses the initial parents saved for its runNumber if there are any,
    otherwise it generates new ones seeded by the runNumber
    (see Helpers.load_initial_parents). For fresh parents, use a new runNumber.

COMPUTING COST (see Compute.py)
    Every simulator call is timed. Each experiment saves its total timing (search,
    final check, wall time) under ... -> <combo> -> timing,
    and each stage of a run saves its totals under seed_<n> -> compute and the machine
    (CPU, threads, OS, compiler, build mode) under seed_<n> -> machines.
    Compare.py turns these into the computing-cost charts and report.
"""
import copy
import json
import sys
import time

import Stats.Compute as Compute
from Baselines import (BaselineType, Problem, results_key, uses_mutation,
                       random_search, hill_climbing, simulated_annealing)
from Utility.Config import LoadConfig, ConfigError
from Utility.Helpers import (sim_seed_for, ga_stream_labels, ga_seed_for, baseline_stream_labels,
                     baseline_seed_for, final_check_seed_for, baseline_final_check_seed_for,
                     ga_key, results_seed, load_initial_parents, with_base_reels,
                     evaluate_population, base_reels_from_file, base_reels_from_same_combos,
                     preflight, for_run, for_stage, is_both, check_best, print_summary)
from Parents import findBest
from Replacement import ReplacementType, ReplaceSingleWorstParent, GenerationalReplace
from Selection import (SelectionTypes, RouletteSelection, tournamentSelection,
                       linear_rank_weights, SUS)
from Utility.Seeding import make_rng
from Utility.Utility import (save_sim_results, save_baseline_results, save_best_spin, start_run_entry,
                     save_run_compute)

# ---------------- algorithm constants ----------------
ELITE_COUNT = 2            # parents carried over unchanged in ElistismGenerational
STEADY_STATE_PARENTS = 2   # parents selected per generation in SteadyState
SUS_PRESSURE = 2           # selection pressure for linear rank weights (SUS)

STAGE_TAG = {"BaseGame": "base", "FreeGame": "free"}   # summary label prefix in Both mode


def run_meta(cfg):
    """Saved once per seed_<n>: the settings that produced this run."""
    meta = {
        "masterSeed": cfg.runNumber,
        "gameMode": cfg.gameMode.name,
        "simSeed": str(sim_seed_for(cfg)),   # string: 64-bit safe in any JSON reader
        "spins": cfg.spins,
        "populationSize": cfg.populationSize,
        "generations": cfg.generations,
        "finalCheckSpins": cfg.finalCheckSpins,
    }
    if is_both(cfg):
        meta["runMode"] = "Both (BaseGame then FreeGame, base reels per combination)"
    return meta


# ---------------- GA mechanics ----------------
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


def select_parents(parents, selection, count, rng):
    match selection:
        case SelectionTypes.TournamentSelection:
            return tournamentSelection(parents, winners=count, rng=rng)
        case SelectionTypes.RouletteSelection:
            return RouletteSelection(parents, count, rng=rng)
        case SelectionTypes.SUS:
            weights = linear_rank_weights(parents, s=SUS_PRESSURE)
            return SUS(parents, weights, count, rng=rng)
    raise ValueError(f"Unsupported selection type: {selection}")


def run_generation(parents, selected, replacement, mutation_count, gen, cfg,
                   fixed_base_reels, rng, sim_seed):
    """
    Produce and evaluate one generation. Returns (best_parent, mean_distance).
    fixed_base_reels: base reels every child uses in FreeGame mode (None in BaseGame mode).
    """
    if replacement == ReplacementType.SteadyState:
        return ReplaceSingleWorstParent(
            parents, cfg.spins, cfg.simulatorPath, cfg.fitnessVariables, cfg.folder,
            selected[0], selected[1], cfg.symbols, mutation_count,
            gen, cfg.gameMode, fixed_base_reels, rng, sim_seed)

    elite = ELITE_COUNT if replacement == ReplacementType.ElistismGenerational else 0
    return GenerationalReplace(
        parents, selected, elite, cfg.spins, cfg.simulatorPath,
        cfg.fitnessVariables, cfg.folder, cfg.symbols, mutation_count,
        gen, cfg.gameMode, fixed_base_reels, rng, sim_seed)


# ---------------- one experiment ----------------
def run_optimization(initial_parents, replacement, selection, mutation_count, cfg, fixed_base_reels):
    generations = generations_for(replacement, cfg)
    parent_count = parents_per_generation(replacement, cfg.populationSize)

    ga_seed = ga_seed_for(cfg, mutation_count, replacement, selection)
    rng = make_rng(cfg.runNumber, *ga_stream_labels(cfg, mutation_count, replacement, selection))
    sim_seed = sim_seed_for(cfg)

    print(f"\n>> {replacement.name} + {selection.name} | "
          f"mutation {mutation_count} | {generations} generations | GA seed {ga_seed}")

    parents = copy.deepcopy(initial_parents)
    gen_results = []

    # best parent seen in ANY generation (the initial population counts too).
    # Generational replacement without elitism can drop its best parent, so the
    # last generation's best is not always the best that was found.
    best_ever = copy.deepcopy(findBest(parents))
    best_ever_gen = 0

    for gen in range(generations):
        selected = select_parents(parents, selection, parent_count, rng)
        best_parent, mean_dist = run_generation(parents, selected, replacement,
                                                mutation_count, gen, cfg,
                                                fixed_base_reels, rng, sim_seed)
        gen_results.append((best_parent.fitnessValue, mean_dist))

        if best_parent.fitnessValue < best_ever.fitnessValue:   # lower = better
            best_ever = copy.deepcopy(best_parent)
            best_ever_gen = gen + 1

    combo_meta = {
        "gaSeed": str(ga_seed),
        "finalCheckSeed": str(final_check_seed_for(cfg, mutation_count, replacement, selection)),
        "bestFoundInGeneration": best_ever_gen,
    }
    save_sim_results(initial_parents, gen_results, best_ever, replacement, selection,
                     cfg.resultFile, mutation_count, results_seed(cfg),
                     run_meta=run_meta(cfg), combo_meta=combo_meta)

    last_best = findBest(parents).fitnessValue
    found = f"generation {best_ever_gen}" if best_ever_gen else "the initial population"
    print(f"Best ever: fitness {best_ever.fitnessValue:.4f}, found in {found} "
          f"(last generation's best: {last_best:.4f})")
    return best_ever


def run_baseline(start_parents, method, mutation_count, cfg, fixed_base_reels):
    """
    One baseline run on the GA's terms: same evaluated starting population, same
    budget (run.generations evaluations), same spins and simulator seed, same
    mutation operator. Returns (BaselineRun, combo_meta).
    """
    budget = cfg.generations
    seed = baseline_seed_for(cfg, method, mutation_count)
    rng = make_rng(cfg.runNumber, *baseline_stream_labels(cfg, method, mutation_count))
    problem = Problem(cfg.fitnessVariables, cfg.symbols, cfg.reelSize, cfg.columnCount,
                      cfg.gameMode, fixed_base_reels, mutation_count, cfg.spins,
                      cfg.simulatorPath, cfg.folder, sim_seed_for(cfg))

    m_text = f"mutation {mutation_count}" if uses_mutation(method) else "no mutation"
    print(f"\n>> {method.name} baseline | {m_text} | {budget} evaluations | seed {seed}")

    combo_meta = {
        "method": method.name,
        "baselineSeed": str(seed),
        "finalCheckSeed": str(baseline_final_check_seed_for(cfg, method, mutation_count)),
        "evaluations": budget,
        "startsFrom": "best parent of initial_population",
        "resultsColumns": ["bestSoFar", "current"],
    }
    match method:
        case BaselineType.RandomSearch:
            run = random_search(start_parents, budget, problem, rng)
            combo_meta["usesMutationCount"] = False
        case BaselineType.HillClimbing:
            run = hill_climbing(start_parents, budget, problem, rng)
            combo_meta["acceptance"] = "child <= current (ties accepted)"
        case BaselineType.SimulatedAnnealing:
            run = simulated_annealing(start_parents, budget, problem, rng,
                                      cfg.saStartTemperature, cfg.saEndTemperature)
            combo_meta.update({
                "acceptance": "exp(-(ln child - ln current) / T)",
                "startTemperature": cfg.saStartTemperature,
                "endTemperature": cfg.saEndTemperature,
                "cooling": "geometric",
            })
        case _:
            raise ValueError(f"Unsupported baseline: {method}")

    combo_meta["bestFoundAtEvaluation"] = run.bestFoundAt
    combo_meta["accepted"] = run.accepted

    found = f"evaluation {run.bestFoundAt}" if run.bestFoundAt else "the starting reelset"
    print(f"Best ever: fitness {run.best.fitnessValue:.4f}, found at {found} "
          f"({run.accepted} accepted)")
    return run, combo_meta


def _cost_line(label, timing):
    """Console line: wall time of one experiment and its time per evaluation."""
    n = timing["evaluations"]
    per = f", {timing['searchSeconds'] / n:.2f} s per evaluation" if n else ""
    return f"{label} took {timing['wallSeconds']:.1f}s ({n} evaluations{per})"


# ---------------- one stage of one run: every experiment ----------------
def run_stage(cfg):
    """
    Run the full experiment sweep for cfg.runNumber in one game mode (cfg.gameMode).
    Returns [(combination label, best fitness)] for the end-of-batch summary.
    """
    stage_start, stage_mark = time.perf_counter(), Compute.mark()
    machine = {}

    def machine_id():
        """The machine's id; described once the simulator has reported its build."""
        if not machine:
            info = Compute.machine_info(cfg.simulatorPath)
            machine.update(id=Compute.machine_id(info), info=info)
        return machine["id"]

    print(f"[seed] master seed (runNumber) = {cfg.runNumber}, "
          f"simulator seed = {sim_seed_for(cfg)}")
    initial_parents = load_initial_parents(cfg)

    free_game = cfg.gameMode.name == "FreeGame"
    manual_base = None     # FreeGame + manual: one base for every combination
    same_bases = {}        # FreeGame + same:   base per (mutation, experiment)
    if free_game and cfg.freeGameBaseSource == "manual":
        manual_base = base_reels_from_file(cfg)
        print(f"[free game] Base reels fixed from {cfg.baseReelFile} for all combinations")
    elif free_game:
        same_bases = base_reels_from_same_combos(cfg)
        print(f"[free game] Base reels per combination from seed_{cfg.runNumber} "
              f"({len(same_bases)} found)")

    if manual_base is not None:
        initial_parents = with_base_reels(initial_parents, manual_base)

    # record what this run starts from (overwrites any older run with this number)
    start_run_entry(initial_parents, cfg.resultFile, results_seed(cfg), run_meta(cfg))

    # BaseGame and manual: the starting population is the same for every combination,
    # so evaluate it once. "same" evaluates per combination because the base changes.
    if not same_bases:
        evaluate_population(initial_parents, cfg, "")

    def starting_point(mutation_count, key):
        """(evaluated starting parents, fixed base reels) for one experiment."""
        if not same_bases:
            return initial_parents, manual_base
        base = same_bases[(mutation_count, key)]
        parents = with_base_reels(initial_parents, base)
        evaluate_population(parents, cfg, f" on {key} base reels")
        return parents, base

    def timed(t0, m0, m1, m2):
        """Timing of one experiment: start evaluations, search, final check (marks m0..m2..now)."""
        return Compute.experiment_timing(Compute.since(m0, m1), Compute.since(m1, m2),
                                         Compute.since(m2), time.perf_counter() - t0, machine_id())

    summary = []
    random_search_done = {}   # RandomSearch ignores mutation: base reels -> (run, meta, record, timing, m)
    for mutation_count in cfg.mutationCounts:
        if cfg.runGA:
            for replacement in cfg.replacementTypes:
                for selection in cfg.selectionTypes:
                    t0, m0 = time.perf_counter(), Compute.mark()
                    parents, base = starting_point(mutation_count, ga_key(replacement, selection))
                    m1 = Compute.mark()
                    best_parent = run_optimization(parents, replacement, selection,
                                                   mutation_count, cfg, base)
                    m2 = Compute.mark()
                    # stats of the best reelset: final check, or the run's own output
                    record = check_best(best_parent, cfg, final_check_seed_for(
                        cfg, mutation_count, replacement, selection))
                    timing = timed(t0, m0, m1, m2)
                    save_best_spin(record, ga_key(replacement, selection), cfg.resultFile,
                                   mutation_count, results_seed(cfg), timing=timing)
                    print(_cost_line(f"{replacement.name}_{selection.name}", timing))

                    label = f"m{mutation_count} {replacement.name}_{selection.name}"
                    summary.append((label, best_parent.fitnessValue))

        for method in cfg.baselineTypes:
            t0, m0 = time.perf_counter(), Compute.mark()
            key = results_key(method)
            label = f"m{mutation_count} {key}"

            # RandomSearch gives the same result under every mutation count, so run it
            # once and store a copy under each mutation_<m> key (charts need it there).
            # The copy's timing is marked reusedFrom, so it is not counted twice.
            cache_key = None
            if not uses_mutation(method):
                base = same_bases[(mutation_count, key)] if same_bases else manual_base
                cache_key = json.dumps(base)
                if cache_key in random_search_done:
                    run, meta, record, timing, first_m = random_search_done[cache_key]
                    save_baseline_results(run.history, run.best, key, cfg.resultFile,
                                          mutation_count, results_seed(cfg),
                                          run_meta=run_meta(cfg), combo_meta=meta)
                    save_best_spin(record, key, cfg.resultFile, mutation_count, results_seed(cfg),
                                   timing=dict(timing, reusedFrom=f"mutation_{first_m}"))
                    print(f"\n>> {method.name} baseline | mutation {mutation_count}: "
                          f"same as above (random search does not use mutation), "
                          f"saved again under mutation_{mutation_count}")
                    summary.append((label, run.best.fitnessValue))
                    continue

            parents, base = starting_point(mutation_count, key)
            m1 = Compute.mark()
            run, meta = run_baseline(parents, method, mutation_count, cfg, base)
            save_baseline_results(run.history, run.best, key, cfg.resultFile,
                                  mutation_count, results_seed(cfg),
                                  run_meta=run_meta(cfg), combo_meta=meta)
            m2 = Compute.mark()
            record = check_best(run.best, cfg,
                                baseline_final_check_seed_for(cfg, method, mutation_count))
            timing = timed(t0, m0, m1, m2)
            save_best_spin(record, key, cfg.resultFile, mutation_count, results_seed(cfg),
                           timing=timing)
            if cache_key is not None:
                random_search_done[cache_key] = (run, meta, record, timing, mutation_count)
            print(_cost_line(key, timing))
            summary.append((label, run.best.fitnessValue))

    # total time of this stage (every combination, start population included),
    # and the machine that ran it
    stage_calls = Compute.since(stage_mark)
    total = round(time.perf_counter() - stage_start, 3)
    if stage_calls:
        machine_id()
        save_run_compute({"totalSeconds": total}, machine["id"], machine["info"],
                         cfg.resultFile, results_seed(cfg))
        calls = Compute.summary(stage_calls)
        print(f"\n[compute] {Compute.describe(machine['info'], calls.get('threads', []))}")
        print(f"[compute] stage took {total / 3600:.2f} h, {calls['seconds'] / 3600:.2f} h of it simulating "
              f"({len(stage_calls)} simulator calls)")
        Compute.warn_if_slow_build()
    return summary


# ---------------- one run: every stage ----------------
def run_one(cfg):
    """
    Run every stage of cfg.runMode for cfg.runNumber: BaseGame, FreeGame, or (Both)
    BaseGame then FreeGame. In Both, the free stage reads each combination's best base
    reels from the BaseGame results this run has just saved under seed_<n>.
    Returns [(combination label, best fitness)] for the end-of-batch summary.
    """
    summary = []
    both = is_both(cfg)
    for i, mode in enumerate(cfg.stages, start=1):
        stage_cfg = for_stage(cfg, mode)
        if both:
            note = ("" if mode.name == "BaseGame" else
                    " - base reels per combination = that combination's best BaseGame reels")
            print(f"\n======== Stage {i}/{len(cfg.stages)}: {mode.name} "
                  f"(saved as seed_{results_seed(stage_cfg)}){note} ========")
        stage_start = time.perf_counter()
        results = run_stage(stage_cfg)
        if both:
            tag = STAGE_TAG[mode.name]
            results = [(f"{tag} {label}", fit) for label, fit in results]
            print(f"\n{mode.name} stage took {(time.perf_counter() - stage_start) / 60:.1f} min")
        summary += results
    return summary


def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else "GA-config.yaml"
    try:
        cfg = LoadConfig(config_path)
        preflight(cfg)
    except (ConfigError, FileNotFoundError) as e:
        print(f"\nCONFIG ERROR: {e}\n")
        sys.exit(1)

    runs = cfg.runNumbers
    saved_as = ", ".join("seed_" + str(results_seed(for_stage(for_run(cfg, n), mode)))
                         for n in runs for mode in cfg.stages)
    print(f"[mode] {cfg.runMode}" + (" -> BaseGame then FreeGame for every run, each free-game "
                                     "combination on its own best BaseGame reels"
                                     if is_both(cfg) else ""))
    print(f"[runs] {len(runs)} run(s): {runs}  ->  saved as {saved_as}")
    if cfg.baselineTypes:
        print(f"[baselines] {', '.join(b.name for b in cfg.baselineTypes)} "
              f"({cfg.generations} evaluations each)"
              + ("" if cfg.runGA else "  |  GA skipped (experiments.runGA: false)"))

    all_results = {}
    start, start_mark = time.perf_counter(), Compute.mark()
    for i, n in enumerate(runs, start=1):
        print(f"\n################ Run {i}/{len(runs)}: runNumber {n} ################")
        run_start = time.perf_counter()
        try:
            all_results[n] = run_one(for_run(cfg, n))
        except (ConfigError, FileNotFoundError) as e:
            print(f"\nCONFIG ERROR in run {n}: {e}\n"
                  f"Completed runs are saved; re-run the rest with runNumbers: "
                  f"{runs[i - 1:]}")
            sys.exit(1)
        print(f"\nRun {n} took {(time.perf_counter() - run_start) / 60:.1f} min")

    print_summary(all_results)
    calls = Compute.summary(Compute.since(start_mark))
    print(f"\nTotal time: {(time.perf_counter() - start) / 60:.1f} min "
          f"({calls['evaluations']} simulator calls, {calls['seconds'] / 60:.1f} min of it simulating)")


if __name__ == "__main__":
    main()