"""
Baseline optimizers for reelset tuning, run under exactly the GA's conditions.

What every baseline shares with the GA (so the comparison is fair):
    starting reelsets   the run's evaluated initial population; a baseline starts
                        from its best member (the GA has seen all of them too)
    budget              run.generations fitness evaluations after the initial
                        population - the same 1000 the GA spends
    simulator seed      the run's sim seed (common random numbers): a reelset gets
                        the same score whichever method proposes it
    spins, goals        the same run.spins and fitnessVariables
    mutation operator   Selection.mutate with the same mutation count

Methods
    RandomSearch        every evaluation is a brand-new random reelset; keep the best.
                        Does not use the mutation count.
    HillClimbing        (1+1)-EA: mutate the current reelset, keep the child if it is
                        at least as good. Ties are accepted, so it can drift across
                        flat regions. This is a Steady-state GA with population 1 and
                        no crossover, so it is the baseline the GA most needs to beat.
    SimulatedAnnealing  like HillClimbing, but a worse child is still accepted with
                        probability exp(-delta / T), where
                            delta = ln(child fitness) - ln(current fitness)
                        and T cools geometrically from startTemperature to
                        endTemperature over the budget.

Why ln(fitness) in the annealing test: the error falls from ~50 to ~0.05 during a
run. On an absolute scale any temperature is either far too hot near the end or
frozen at the start. On a log scale T means "how much relative worsening is
tolerated": T = 0.14 accepts a child 10 % worse than the current one about half the
time; T = 0.002 practically never does.

History layout (one row per evaluation, same layout as the GA's results):
    [best fitness so far, fitness of the reelset the method is currently on]
RandomSearch's second column is the reelset it just sampled. Row k is the state
after k + 1 evaluations, so Compare.py plots baselines and GA on one x-axis.
"""
import copy
import math
from dataclasses import dataclass
from enum import Enum, auto

from Parents import Parent, GameMode, findBest
from Selection import mutate
from Utility import EvaluateAndSaveParents, generate_reelset


class BaselineType(Enum):
    RandomSearch = auto()
    HillClimbing = auto()
    SimulatedAnnealing = auto()


# results.json key is <Method>_Baseline, next to the GA's <Replacement>_<Selection>
BASELINE_TAG = "Baseline"


def results_key(method):
    return f"{method.name}_{BASELINE_TAG}"


def uses_mutation(method):
    """RandomSearch never mutates, so its result is the same for every mutation count."""
    return method != BaselineType.RandomSearch


@dataclass
class Problem:
    """Everything a baseline needs to make and score reelsets, as the GA does."""
    fitnessVariables: list
    symbols: list
    reelSize: int
    columnCount: int
    gameMode: GameMode
    fixedBaseReels: list | None     # FreeGame: base reels every candidate uses
    mutationCount: int
    spins: int
    simulatorPath: str
    folder: str
    simSeed: int

    def evaluate(self, parent):
        EvaluateAndSaveParents(parent, self.spins, self.simulatorPath,
                               f"{self.folder}/baseline.json",
                               self.gameMode == GameMode.BaseGame, self.simSeed)
        return parent.fitnessValue

    def _tuned(self, parent):
        """The reels this mode tunes: base reels in BaseGame, free reels in FreeGame."""
        return parent.baseReelSet if self.gameMode == GameMode.BaseGame else parent.freeReelSet

    def _with_tuned(self, source, reels):
        """New candidate: `reels` as the tuned part, everything else from `source`."""
        if self.gameMode == GameMode.BaseGame:
            return Parent(self.fitnessVariables, reels, source.freeReelSet)
        base = self.fixedBaseReels if self.fixedBaseReels is not None else source.baseReelSet
        return Parent(self.fitnessVariables, base, reels)

    def neighbour(self, parent, rng):
        """The GA's mutation, applied to one reelset (no crossover)."""
        return self._with_tuned(parent, mutate(self._tuned(parent), self.symbols,
                                               self.mutationCount, rng))

    def random_candidate(self, source, rng):
        """A fresh random reelset, generated the way the initial population is."""
        return self._with_tuned(source, generate_reelset(self.symbols, self.reelSize,
                                                         self.columnCount, rng))


@dataclass
class BaselineRun:
    history: list        # [(best so far, current), ...], one row per evaluation
    best: Parent         # best reelset found (the starting reelset counts)
    bestFoundAt: int     # evaluation that found it; 0 = the starting reelset
    accepted: int        # moves accepted (RandomSearch: improvements of the best)


def _start(start_population):
    best = findBest(start_population)
    if not math.isfinite(best.fitnessValue):
        raise ValueError("Evaluate the initial population before running a baseline")
    return copy.deepcopy(best)


def _log(method, k, budget, cand, moved, current, best):
    print(f"{method} {k}/{budget}: candidate {cand:.4f} | "
          f"{'accepted' if moved else 'rejected'} | current {current:.4f}, best {best:.4f}")


def random_search(start_population, budget, problem, rng):
    best = _start(start_population)
    history, found, improved = [], 0, 0
    for k in range(1, budget + 1):
        cand = problem.random_candidate(best, rng)
        f = problem.evaluate(cand)
        better = f < best.fitnessValue
        if better:
            best, found, improved = cand, k, improved + 1
        history.append((best.fitnessValue, f))
        _log("RandomSearch", k, budget, f, better, f, best.fitnessValue)
    return BaselineRun(history, best, found, improved)


def hill_climbing(start_population, budget, problem, rng):
    current = _start(start_population)
    history, found, accepted = [], 0, 0
    for k in range(1, budget + 1):
        cand = problem.neighbour(current, rng)
        f = problem.evaluate(cand)
        moved = f <= current.fitnessValue            # (1+1)-EA: ties accepted
        if moved:
            if f < current.fitnessValue:
                found = k
            current = cand
            accepted += 1
        history.append((current.fitnessValue, current.fitnessValue))
        _log("HillClimbing", k, budget, f, moved, current.fitnessValue, current.fitnessValue)
    return BaselineRun(history, current, found, accepted)


def temperature(k, budget, t_start, t_end):
    """Geometric cooling: t_start at evaluation 1, t_end at the last evaluation."""
    if budget <= 1:
        return t_end
    return t_start * (t_end / t_start) ** ((k - 1) / (budget - 1))


def _ln(f):
    return math.log(max(f, 1e-12))     # a perfect score of 0 must not break the log


def simulated_annealing(start_population, budget, problem, rng, t_start, t_end):
    current = _start(start_population)
    best = current
    history, found, accepted = [], 0, 0
    for k in range(1, budget + 1):
        t = temperature(k, budget, t_start, t_end)
        cand = problem.neighbour(current, rng)
        f = problem.evaluate(cand)
        delta = _ln(f) - _ln(current.fitnessValue)
        moved = delta <= 0 or rng.random() < math.exp(-delta / t)
        if moved:
            current = cand
            accepted += 1
        if current.fitnessValue < best.fitnessValue:
            best, found = current, k
        history.append((best.fitnessValue, current.fitnessValue))
        _log("SimulatedAnnealing", k, budget, f, moved, current.fitnessValue, best.fitnessValue)
    return BaselineRun(history, best, found, accepted)