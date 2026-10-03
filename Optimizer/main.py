from Utility import generate_reelset, save_reelset_file,UpdateParentVars \
                    , make_pairs
from FitnessFunction import Evaluate, evaluate_parent
from Parents import Parent, findWorstIndex, findBest, findWorst , findBestIndex , \
                    VariableType , FitnessVariable     
from Selection import crossover,RouletteSelection, tournamentSelection, mutate , \
                        linear_rank_weights ,boltzmann_weights, SUS ,\
                        SelectionTypes
from Replacement import ReplacementType ,ReplaceSingleWorstParent ,GenerationalReplace
import json
import time
# ---------------- variables ----------------
symbols = ["AA", "BB", "CC", "DD", "EE", "FF", "GG", "WD", "SC"]
reelSize = 50
columnCount = 5
fitnessvariable = [
    FitnessVariable(VariableType.baseRTP , 0 , .57,10),
    FitnessVariable(VariableType.baseHitRate , 0 , 3,5),
    FitnessVariable(VariableType.freeRTP , 0 , .38,10),
    FitnessVariable(VariableType.freeHitRate , 0 , 2.7,5),
    FitnessVariable(VariableType.freeTriggerRate , 0 , 80,3),
]

populationSize = 10
generations = 50
mutationCount = 10
spins = 10_000_000
createInitialPopulation = True
selectionType = SelectionTypes.SUS
replacementTpye = ReplacementType.Generational

folder = "Optimizer/ReelSets"
simulatorPath = "build/simulator"

print(f"Selection is {selectionType.name} and replacement is {replacementTpye.name}")

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
    output = evaluate_parent(p,spins,simulatorPath, f"{folder}/parent{i}.json")
    UpdateParentVars(parents[i],output)
    print(f"parent{i}: fitness {p.fitnessValue:.4f}, rtp {output['totalRTP'] * 100:.2f} %")

# ---------------- evolution loop ----------------

for gen in range(generations):
    start = time.perf_counter()
    selectedParents = []
    match replacementTpye:
        case ReplacementType.SteadyState:
            parentNumber = 2
        case ReplacementType.Generational:
            parentNumber = 10
        case ReplacementType.ElistismGenerational:
            parentNumber = 8
    
    match selectionType:
        case SelectionTypes.TournamentSelection:
            selectedParents = tournamentSelection(parents, winners=parentNumber)
            
        case SelectionTypes.RouletteSelection:
            selectedParents = RouletteSelection(parents,parentNumber)

        case SelectionTypes.SUS:
            weights = linear_rank_weights(parents,s=2)
            selectedParents = SUS(parents, weights, parentNumber)

            
    match replacementTpye:
        case ReplacementType.Generational:
            GenerationalReplace(parents, selectedParents, 0, spins, simulatorPath,
                                fitnessvariable, folder, symbols, mutationCount, gen)
        case ReplacementType.ElistismGenerational:
            GenerationalReplace(parents, selectedParents, 2, spins, simulatorPath,
                                fitnessvariable, folder, symbols, mutationCount, gen)

        case ReplacementType.SteadyState:

            ReplaceSingleWorstParent(parents,spins,simulatorPath,fitnessvariable,folder,
                            selectedParents[0],selectedParents[1],symbols,mutationCount ,gen)

    elapsed = time.perf_counter() - start
    print(f"Single gen Took {elapsed:.4f} seconds")

# output = Evaluate(300_000_000, f"{folder}/parent{findBestIndex(parents)}.json",simulatorPath)
# print(output['totalRTP'])
# print(output['baseHitRate'])
findBest(parents).printData()


