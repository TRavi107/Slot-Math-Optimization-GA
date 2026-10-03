from enum import Enum , auto
from FitnessFunction import evaluate_parent
from Selection import crossover, mutate
from Utility import make_pairs, save_reelset_file
from Parents import Parent, FitnessVariable, findBest, findWorstIndex 

class ReplacementType(Enum):
    SteadyState = auto()
    Generational = auto()
    ElistismGenerational = auto()

def ReplaceSingleWorstParent(parents,spins, simulationFolder ,fitnessvariable,folder,parent1,parent2,symbols,mutationCount,gen):
    child = Parent(
        fitnessvariable,
        crossover(parent1.baseReelSet, parent2.baseReelSet),
        crossover(parent1.freeReelSet, parent2.freeReelSet),
    )
    child.baseReelSet = mutate(child.baseReelSet, symbols, mutationCount)
    child.freeReelSet = mutate(child.freeReelSet, symbols, mutationCount)

    # evaluate only the child (writes it to a temp file first)
    evaluate_parent(child,spins,simulationFolder, f"{folder}/child.json")

    # replace the worst parent only if the child is closer to 1
    worst_idx = findWorstIndex(parents)
    worst = parents[worst_idx]
    replaced = child.fitnessValue < worst.fitnessValue

    if replaced:
        parents[worst_idx] = child
        # keep the file on disk in sync with the object
        save_reelset_file(child.baseReelSet, child.freeReelSet,
                        f"{folder}/parent{worst_idx}.json")

    dists = [abs(p.fitnessValue) for p in parents]
    print(f"Gen {gen + 1}: child {child.fitnessValue:.4f} | "
        f"{'replaced ' + str(worst_idx) if replaced else 'rejected'} "
        f"(worst was {worst.fitnessValue:.4f}) | "
        f"best {findBest(parents).fitnessValue:.4f}, "
        f"mean dist {sum(dists) / len(dists):.4f}")

def make_child(p1, p2, fitnessvariable, symbols, mutationCount):
    child = Parent(fitnessvariable,
                   crossover(p1.baseReelSet, p2.baseReelSet),
                   crossover(p1.freeReelSet, p2.freeReelSet))
    child.baseReelSet = mutate(child.baseReelSet, symbols, mutationCount)
    child.freeReelSet = mutate(child.freeReelSet, symbols, mutationCount)
    return child

def GenerationalReplace(parents, selected, n_elite, spins, simulatorPath,
                        fitnessvariable, folder, symbols, mutationCount, gen):
    n_children = len(parents) - n_elite
    elites = sorted(parents, key=lambda p: p.fitnessValue)[:n_elite]

    children = []
    pairs, _ = make_pairs(selected)
    for p1, p2 in pairs:
        for a, b in ((p1, p2), (p2, p1)):
            if len(children) == n_children:
                break
            c = make_child(a, b, fitnessvariable, symbols, mutationCount)
            evaluate_parent(c, spins, simulatorPath, f"{folder}/child.json")
            children.append(c)
    assert len(children) == n_children, "select 2 parents per 2 children"

    parents[:] = elites + children
    for i, p in enumerate(parents):
        save_reelset_file(p.baseReelSet, p.freeReelSet, f"{folder}/parent{i}.json")

    best = findBest(parents).fitnessValue
    mean = sum(p.fitnessValue for p in parents) / len(parents)
    print(f"Gen {gen + 1}: best {best:.4f}, mean {mean:.4f}")