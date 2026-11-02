"""
Slot reelset optimizer - entry point.

    python Optimizer/main.py                  # uses GA-config.yaml
    python Optimizer/main.py my_config.yaml

All settings are in the YAML config. This file has the GA loop, the baseline
runner and the sweep over runs / stages / combinations. Seeding, starting parents,
free-game base reels and the summary are in Utility/Helpers.py.

Game modes (run.gameMode):
    BaseGame   tune base reels                          -> seed_<n>
    FreeGame   base reels fixed, tune free reels        -> seed_<n>_free
    Both       BaseGame sweep, then FreeGame sweep; each free-game combination
               starts from the base reels the same combination found

Each run number is the master seed for everything (parents, selection, crossover,
mutation, simulator), so the same run number + config gives the same seed_<n>.
See Running.md for the details.
"""
import copy
import json
import sys
import time

from Stats import Compute
from Baselines import (BaselineType, Problem, results_key, uses_mutation,
                       random_search, hill_climbing, simulated_annealing)
from Utility.Config import LoadConfig, ConfigError
from Utility.Helpers import (sim_seed_for, ga_stream_labels, ga_seed_for, baseline_stream_labels,
                     baseline_seed_for, final_check_seed_for, baseline_final_check_seed_for,
                     ga_key, results_seed, load_initial_parents, with_base_reels,
                     evaluate_population, base_reels_from_file, base_reels_from_same_combos,
                     evaluation_for, evaluation_meta,
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
    if cfg.gameMode.name == "FreeGame":
        meta["freeEvaluation"] = cfg.freeEvaluation
        if cfg.freeEvaluation == "sessions":
            meta["freeSessions"] = cfg.freeSessions or "auto (spins / trigger rate)"
            meta["triggerRateSpins"] = cfg.triggerRateSpins
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
                   fixed_base_reels, rng, sim_seed, evaluation=None):
    """
    Produce and evaluate one generation. Returns (best_parent, mean_distance).
    fixed_base_reels: base reels every child uses in FreeGame mode (None in BaseGame mode).
    evaluation: what the simulator plays (Helpers.evaluation_for); None = mode default.
    """
    if replacement == ReplacementType.SteadyState:
        return ReplaceSingleWorstParent(
            parents, cfg.spins, cfg.simulatorPath, cfg.fitnessVariables, cfg.folder,
            selected[0], selected[1], cfg.symbols, mutation_count,
            gen, cfg.gameMode, fixed_base_reels, rng, sim_seed, eval_mode=evaluation)

    elite = ELITE_COUNT if replacement == ReplacementType.ElistismGenerational else 0
    return GenerationalReplace(
        parents, selected, elite, cfg.spins, cfg.simulatorPath,
        cfg.fitnessVariables, cfg.folder, cfg.symbols, mutation_count,
        gen, cfg.gameMode, fixed_base_reels, rng, sim_seed, eval_mode=evaluation)


# ---------------- one experiment ----------------
def run_optimization(initial_parents, replacement, selection, mutation_count, cfg,
                     fixed_base_reels, evaluation=None):
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
                                                fixed_base_reels, rng, sim_seed, evaluation)
        gen_results.append((best_parent.fitnessValue, mean_dist))

        if best_parent.fitnessValue < best_ever.fitnessValue:   # lower = better
            best_ever = copy.deepcopy(best_parent)
            best_ever_gen = gen + 1

    combo_meta = {
        "gaSeed": str(ga_seed),
        "finalCheckSeed": str(final_check_seed_for(cfg, mutation_count, replacement, selection)),
        "bestFoundInGeneration": best_ever_gen,
    }
    if cfg.gameMode.name == "FreeGame" and evaluation is not None:
        combo_meta["evaluation"] = evaluation_meta(evaluation)
    save_sim_results(initial_parents, gen_results, best_ever, replacement, selection,
                     cfg.resultFile, mutation_count, results_seed(cfg),
                     run_meta=run_meta(cfg), combo_meta=combo_meta)

    last_best = findBest(parents).fitnessValue
    found = f"generation {best_ever_gen}" if best_ever_gen else "the initial population"
    print(f"Best ever: fitness {best_ever.fitnessValue:.4f}, found in {found} "
          f"(last generation's best: {last_best:.4f})")
    return best_ever


def run_baseline(start_parents, method, mutation_count, cfg, fixed_base_reels, evaluation=None):
    """One baseline run with the GA's starting population, budget, spins, sim seed and mutation. Returns (BaselineRun, combo_meta)."""
    budget = cfg.generations
    seed = baseline_seed_for(cfg, method, mutation_count)
    rng = make_rng(cfg.runNumber, *baseline_stream_labels(cfg, method, mutation_count))
    problem = Problem(cfg.fitnessVariables, cfg.symbols, cfg.reelSize, cfg.columnCount,
                      cfg.gameMode, fixed_base_reels, mutation_count, cfg.spins,
                      cfg.simulatorPath, cfg.folder, sim_seed_for(cfg), evaluation)

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
    if cfg.gameMode.name == "FreeGame" and evaluation is not None:
        combo_meta["evaluation"] = evaluation_meta(evaluation)
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
    if free_game:
        print(f"[free game] Candidates evaluated with: {cfg.freeEvaluation}")

    if manual_base is not None:
        initial_parents = with_base_reels(initial_parents, manual_base)

    # record what this run starts from (overwrites any older run with this number)
    start_run_entry(initial_parents, cfg.resultFile, results_seed(cfg), run_meta(cfg))

    # trigger rate of every base reelset, measured once (FreeGame + evaluation sessions)
    trigger_rates = {}

    # BaseGame and manual: the starting population and the evaluation are the same for
    # every combination, so evaluate once. "same" evaluates per combination because the
    # base changes.
    stage_evaluation = None
    if not same_bases:
        stage_evaluation = evaluation_for(cfg, manual_base, trigger_rates)
        evaluate_population(initial_parents, cfg, "", stage_evaluation)

    def starting_point(mutation_count, key):
        """(evaluated starting parents, fixed base reels, evaluation) for one experiment."""
        if not same_bases:
            return initial_parents, manual_base, stage_evaluation
        base = same_bases[(mutation_count, key)]
        evaluation = evaluation_for(cfg, base, trigger_rates)
        parents = with_base_reels(initial_parents, base)
        evaluate_population(parents, cfg, f" on {key} base reels", evaluation)
        return parents, base, evaluation

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
                    parents, base, evaluation = starting_point(mutation_count,
                                                               ga_key(replacement, selection))
                    m1 = Compute.mark()
                    best_parent = run_optimization(parents, replacement, selection,
                                                   mutation_count, cfg, base, evaluation)
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

            parents, base, evaluation = starting_point(mutation_count, key)
            m1 = Compute.mark()
            run, meta = run_baseline(parents, method, mutation_count, cfg, base, evaluation)
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
    """Every stage of cfg.runMode for cfg.runNumber (Both = BaseGame then FreeGame).
    Returns [(combination label, best fitness)] for the summary."""
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