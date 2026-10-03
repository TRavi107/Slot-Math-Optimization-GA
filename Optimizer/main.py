from Utility import generate_reelset, save_reelset_file,UpdateParentVars
from FitnessFunction import Evaluate
from Parents import Parent, findWorstIndex, findBest, findWorst , findBestIndex , \
                    VariableType , FitnessVariable     
from Selection import crossover, tournamentSelection, mutate
import json

# ---------------- variables ----------------
symbols = ["AA", "BB", "CC", "DD", "EE", "FF", "GG", "WD", "SC"]
reelSize = 50
columnCount = 5
fitnessvariable = [
    FitnessVariable(VariableType.baseRTP , 0 , .57,100),
    FitnessVariable(VariableType.baseHitRate , 0 , 3,3),
    FitnessVariable(VariableType.freeRTP , 0 , .38,100),
    FitnessVariable(VariableType.freeHitRate , 0 , 2.7,3),
    FitnessVariable(VariableType.freeTriggerRate , 0 , 80,10),
]

populationSize = 10
generations = 100
mutationCount = 10
spins = 10_000_000
createInitialPopulation = False
folder = "Optimizer/ReelSets"
simulatorPath = "build/simulator"

def evaluate_parent(parent, path):
    """Write the parent's reels to `path`, simulate it, store its fitness."""
    save_reelset_file(parent.baseReelSet, parent.freeReelSet, path)
    output = Evaluate(spins, path,simulatorPath)
    UpdateParentVars(parent,output)
    return output

# ---------------- create initial population (run once, then comment out) ----------------
if(createInitialPopulation):
    for i in range(populationSize):
        base = generate_reelset(symbols, reelSize, columnCount)
        free = generate_reelset(symbols, reelSize, columnCount)
        save_reelset_file(base, free, f"{folder}/parent{i}.json")

# ---------------- load population ----------------
parents = []
for i in range(populationSize):
    with open(f"{folder}/parent{i}.json") as f:
        data = json.load(f)
    # [0] unwraps the extra list level, so baseReelSet[0] is reel 0
    parents.append(Parent(fitnessvariable,data["BaseGameReel"][0], data["FreeGameReel"][0]))

# ---------------- evaluate initial population ONCE ----------------
for i, p in enumerate(parents):
    output = evaluate_parent(p, f"{folder}/parent{i}.json")
    UpdateParentVars(parents[i],output)
    print(f"parent{i}: fitness {p.fitnessValue:.4f}, rtp {output['totalRTP'] * 100:.2f} %")

# ---------------- evolution loop ----------------
for gen in range(generations):
    # tournament selection
    parent1, parent2 = tournamentSelection(parents)

    # crossover (base from base, free from free) then mutation
    child = Parent(
        fitnessvariable,
        crossover(parent1.baseReelSet, parent2.baseReelSet),
        crossover(parent1.freeReelSet, parent2.freeReelSet),
    )
    child.baseReelSet = mutate(child.baseReelSet, symbols, mutationCount)
    child.freeReelSet = mutate(child.freeReelSet, symbols, mutationCount)

    # evaluate only the child (writes it to a temp file first)
    evaluate_parent(child, f"{folder}/child.json")

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


# output = Evaluate(300_000_000, f"{folder}/parent{findBestIndex(parents)}.json",simulatorPath)
# print(output['totalRTP'])
# print(output['baseHitRate'])
findBest(parents).printData()
