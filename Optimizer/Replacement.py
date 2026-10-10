from enum import Enum, auto
from Selection import crossover, mutate
from Utility.Utility import EvaluateAndSaveParents, make_pairs
from Parents import Parent, FitnessVariable, findBest, findWorstIndex, GameMode


class ReplacementType(Enum):
    SteadyState = auto()
    Generational = auto()
    ElistismGenerational = auto()


def ReplaceSingleWorstParent(parents, spins, simulationFolder, fitnessvariable, folder,
                             parent1, parent2, symbols, mutationCount, gen,
                             gameMode, parentBaseReel, rng, sim_seed):
    child = make_child(parent1, parent2, fitnessvariable, symbols, mutationCount,
                       gameMode, parentBaseReel, rng)

    # evaluate only the child (writes it to a temp file first)
    EvaluateAndSaveParents(child, spins, simulationFolder, f"{folder}/child.json",
                           gameMode == GameMode.BaseGame, sim_seed)

    # replace the worst parent only if the child is better
    worst_idx = findWorstIndex(parents)
    worst = parents[worst_idx]
    replaced = child.fitnessValue < worst.fitnessValue

    if replaced:
        parents[worst_idx] = child

    dists = [abs(p.fitnessValue) for p in parents]
    bestParent = findBest(parents)
    meanDist = sum(dists) / len(dists)
    print(f"Gen {gen + 1}: child {child.fitnessValue:.4f} | "
          f"{'replaced ' + str(worst_idx) if replaced else 'rejected'} "
          f"(worst was {worst.fitnessValue:.4f}) | "
          f"best {bestParent.fitnessValue:.4f}, "
          f"mean dist {meanDist:.4f}")

    return bestParent, meanDist


def make_child(p1, p2, fitnessvariable, symbols, mutationCount, gameMode, parentBaseReel, rng):
    match gameMode:
        case GameMode.BaseGame:
            child = Parent(
                fitnessvariable,
                crossover(p1.baseReelSet, p2.baseReelSet, rng),
                p1.freeReelSet,  # using parent just for placeholder
            )
            child.baseReelSet = mutate(child.baseReelSet, symbols, mutationCount, rng)
        case GameMode.FreeGame:
            child = Parent(
                fitnessvariable,
                parentBaseReel,
                crossover(p1.freeReelSet, p2.freeReelSet, rng),
            )
            child.freeReelSet = mutate(child.freeReelSet, symbols, mutationCount, rng)
    return child


def GenerationalReplace(parents, selected, n_elite, spins, simulatorPath,
                        fitnessvariable, folder, symbols, mutationCount,
                        gen, gameMode, parentBaseReel, rng, sim_seed):
    n_children = len(parents) - n_elite
    elites = sorted(parents, key=lambda p: p.fitnessValue)[:n_elite]

    children = []
    pairs, _ = make_pairs(selected)
    for p1, p2 in pairs:
        for a, b in ((p1, p2), (p2, p1)):
            if len(children) == n_children:
                break
            c = make_child(a, b, fitnessvariable, symbols, mutationCount,
                           gameMode, parentBaseReel, rng)
            EvaluateAndSaveParents(c, spins, simulatorPath, f"{folder}/child.json",
                                   gameMode == GameMode.BaseGame, sim_seed)
            children.append(c)
    assert len(children) == n_children, "select 2 parents per 2 children"

    parents[:] = elites + children

    bestparent = findBest(parents)
    mean = sum(p.fitnessValue for p in parents) / len(parents)
    print(f"Gen {gen + 1}: best {bestparent.fitnessValue:.4f}, mean {mean:.4f}")
    return bestparent, mean