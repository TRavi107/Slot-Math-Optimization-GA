import random

from Utility import CreateInitialPopulation, EvaluateParents ,LoadInitialParents\
                    , make_pairs , save_sim_results
from Parents import Parent, findWorstIndex, findBest, findWorst , findBestIndex , \
                    UpdateParentVars,VariableType , FitnessVariable , GameMode 
from Selection import RouletteSelection, tournamentSelection, mutate , \
                        linear_rank_weights ,boltzmann_weights, SUS ,\
                        SelectionTypes
from Replacement import ReplacementType ,ReplaceSingleWorstParent ,GenerationalReplace
import json
import time
import copy

# ---------------- variables ----------------
symbols = ["AA", "BB", "CC", "DD", "EE", "FF", "GG", "WD", "SC"]
reelSize = 50
columnCount = 5
fitnessvariable = [
    FitnessVariable(VariableType.baseRTP , 0 , .57,10),
    FitnessVariable(VariableType.baseHitRate , 0 , 3,5),
    # FitnessVariable(VariableType.freeRTP , 0 , .38,10),
    # FitnessVariable(VariableType.freeHitRate , 0 , 2.7,5),
    # FitnessVariable(VariableType.freeRetriggerRate , 0 , 60,4),
    FitnessVariable(VariableType.freeTriggerRate , 0 , 80,3),
]
gameMode = GameMode.BaseGame
bestParentIndex= 5 # for free game mode

populationSize = 10
spins = 10_000_000

folder = "Optimizer/ReelSets/TempParents"
parentsFolder = "Optimizer/ReelSets/InitialParents"
resultFile = "Results/results.json"
simulatorPath = "build/simulator"

def RunOptimization(initialParents, generations,runNumber,replacementTpye,selectionType,mutationCount):

    print(f"Selection is {selectionType.name} and replacement is {replacementTpye.name}")

    parents = copy.deepcopy(initialParents)
    
    # ---------------- evolution loop ----------------
    genResults = []

    for gen in range(generations):
        
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
                bestparent,meanDist = GenerationalReplace(parents, selectedParents, 0, spins, simulatorPath,
                                    fitnessvariable, folder, symbols, mutationCount, gen ,
                                    gameMode,parents[bestParentIndex].baseReelSet)
            case ReplacementType.ElistismGenerational:
                bestparent,meanDist = GenerationalReplace(parents, selectedParents, 2, spins, simulatorPath,
                                    fitnessvariable, folder, symbols, mutationCount, 
                                    gen, gameMode,parents[bestParentIndex].baseReelSet)

            case ReplacementType.SteadyState:

                bestparent,meanDist = ReplaceSingleWorstParent(parents,spins,simulatorPath,fitnessvariable,folder,
                                selectedParents[0],selectedParents[1],symbols,mutationCount ,
                                gen,gameMode, parents[bestParentIndex].baseReelSet)
            
        
        genResults.append((bestparent.fitnessValue, meanDist))

    key = save_sim_results(initialParents,genResults,findBest(parents), replacementTpye, selectionType,
                        resultFile, mutationCount,runNumber)

    print(f"Best parent is {findBestIndex(parents)}")

    # output = Evaluate(100_000_000,f"{folder}/parent{findBestIndex(parents)}.json",simulatorPath)
    # print(f"Total rt {output['totalRTP']}")
    # print(f"Free trigger rate {output['freeTriggerRate']}")
    # print(f"Free retrigger rate {output['freeReTriggerRate']}")
    # print(f"Base hitrate {output['baseHitRate']}")
    # print(f"Free hitrate {output['freeHitRate']}")
    # print(f"Free rtp {output['freeRTP']}")
    # print(f"base rtp {output['baseRTP']}")

replacementTypes = [ReplacementType.Generational,ReplacementType.SteadyState,ReplacementType.ElistismGenerational]
selectionTypes = [SelectionTypes.RouletteSelection,SelectionTypes.TournamentSelection,SelectionTypes.SUS]
mutationCounts = [3] # 10% 20 % 30 % since reel length is 50
runNumber = 4
generations = 1000
createNewparents  = False
initialParents =[]


parentsReels = [
      {
        "BaseGameReel": [
          ["WD", "FF", "WD", "GG", "DD", "FF", "AA", "CC", "EE", "BB", "EE", "SC", "CC", "FF", "AA", "GG", "SC", "CC", "FF", "BB", "WD", "AA", "AA", "GG", "DD", "DD", "SC", "BB", "GG", "GG", "BB", "WD", "BB", "SC", "SC", "DD", "AA", "WD", "BB", "EE", "EE", "SC", "FF", "WD", "FF", "AA", "CC", "FF", "CC", "CC"],
          ["BB", "CC", "FF", "AA", "AA", "AA", "WD", "AA", "SC", "DD", "CC", "EE", "EE", "EE", "GG", "WD", "DD", "FF", "BB", "WD", "SC", "EE", "DD", "BB", "FF", "AA", "SC", "CC", "EE", "CC", "CC", "BB", "DD", "AA", "SC", "EE", "EE", "SC", "FF", "BB", "CC", "SC", "SC", "WD", "BB", "SC", "SC", "DD", "AA", "EE"],
          ["BB", "SC", "WD", "DD", "BB", "SC", "GG", "WD", "DD", "WD", "GG", "WD", "FF", "SC", "SC", "DD", "SC", "CC", "EE", "CC", "FF", "CC", "WD", "FF", "FF", "AA", "AA", "SC", "FF", "CC", "BB", "GG", "SC", "DD", "GG", "BB", "DD", "WD", "BB", "FF", "GG", "GG", "GG", "CC", "EE", "BB", "FF", "BB", "EE", "BB"],
          ["GG", "FF", "SC", "SC", "FF", "SC", "GG", "DD", "GG", "BB", "WD", "AA", "AA", "EE", "DD", "GG", "BB", "WD", "WD", "SC", "FF", "WD", "FF", "GG", "CC", "CC", "GG", "FF", "WD", "WD", "EE", "BB", "DD", "CC", "GG", "AA", "FF", "EE", "DD", "SC", "GG", "GG", "SC", "BB", "CC", "WD", "BB", "AA", "WD", "AA"],
          ["SC", "WD", "EE", "CC", "SC", "AA", "CC", "GG", "FF", "AA", "SC", "SC", "WD", "WD", "SC", "EE", "WD", "EE", "EE", "FF", "SC", "AA", "GG", "AA", "BB", "DD", "WD", "DD", "CC", "FF", "GG", "WD", "SC", "SC", "EE", "CC", "CC", "AA", "BB", "GG", "DD", "EE", "FF", "EE", "CC", "CC", "EE", "AA", "DD", "AA"]
        ],
        "FreeGameReel": [
          ["GG", "CC", "GG", "AA", "DD", "AA", "SC", "FF", "SC", "DD", "SC", "CC", "CC", "WD", "CC", "AA", "WD", "EE", "WD", "AA", "DD", "GG", "BB", "FF", "WD", "FF", "DD", "SC", "BB", "WD", "GG", "WD", "FF", "CC", "DD", "AA", "FF", "DD", "WD", "WD", "GG", "GG", "WD", "EE", "WD", "BB", "SC", "BB", "SC", "FF"],
          ["BB", "CC", "BB", "FF", "FF", "SC", "DD", "WD", "GG", "BB", "BB", "SC", "SC", "FF", "EE", "BB", "FF", "GG", "BB", "EE", "WD", "WD", "WD", "FF", "SC", "GG", "WD", "CC", "CC", "DD", "DD", "WD", "AA", "GG", "DD", "SC", "GG", "FF", "BB", "DD", "FF", "EE", "BB", "DD", "FF", "BB", "GG", "WD", "FF", "WD"],
          ["WD", "EE", "DD", "WD", "EE", "WD", "BB", "DD", "AA", "AA", "BB", "EE", "BB", "BB", "SC", "GG", "DD", "AA", "DD", "EE", "AA", "DD", "EE", "BB", "GG", "DD", "DD", "EE", "EE", "FF", "AA", "SC", "DD", "FF", "SC", "CC", "DD", "SC", "WD", "BB", "AA", "EE", "GG", "BB", "EE", "CC", "BB", "CC", "SC", "FF"],
          ["GG", "FF", "GG", "EE", "DD", "FF", "WD", "WD", "BB", "CC", "EE", "AA", "FF", "CC", "CC", "WD", "BB", "WD", "AA", "EE", "FF", "SC", "SC", "FF", "FF", "GG", "SC", "EE", "FF", "BB", "EE", "WD", "FF", "FF", "BB", "CC", "BB", "EE", "FF", "CC", "AA", "DD", "CC", "FF", "BB", "GG", "CC", "EE", "CC", "EE"],
          ["SC", "BB", "WD", "GG", "EE", "WD", "SC", "SC", "FF", "FF", "EE", "GG", "WD", "AA", "AA", "AA", "CC", "DD", "EE", "GG", "CC", "DD", "GG", "BB", "EE", "EE", "FF", "BB", "AA", "DD", "WD", "DD", "CC", "BB", "FF", "SC", "WD", "DD", "CC", "AA", "AA", "GG", "FF", "GG", "DD", "BB", "WD", "CC", "BB", "SC"]
        ]
      },
      {
        "BaseGameReel": [
          ["DD", "WD", "GG", "SC", "DD", "BB", "BB", "BB", "AA", "BB", "BB", "FF", "CC", "SC", "GG", "BB", "AA", "AA", "EE", "FF", "AA", "EE", "EE", "FF", "AA", "GG", "FF", "SC", "WD", "GG", "CC", "WD", "DD", "WD", "GG", "CC", "WD", "DD", "DD", "WD", "BB", "WD", "EE", "DD", "CC", "WD", "EE", "AA", "SC", "EE"],
          ["EE", "WD", "FF", "CC", "WD", "CC", "CC", "CC", "BB", "FF", "DD", "AA", "CC", "AA", "WD", "DD", "WD", "BB", "FF", "WD", "FF", "GG", "WD", "SC", "AA", "EE", "GG", "AA", "AA", "WD", "BB", "SC", "WD", "BB", "EE", "BB", "EE", "AA", "BB", "BB", "SC", "SC", "DD", "SC", "BB", "DD", "DD", "AA", "WD", "BB"],
          ["SC", "FF", "CC", "EE", "BB", "FF", "GG", "SC", "AA", "FF", "FF", "GG", "WD", "EE", "SC", "AA", "GG", "DD", "CC", "EE", "BB", "GG", "BB", "AA", "EE", "EE", "FF", "SC", "DD", "EE", "DD", "SC", "AA", "WD", "FF", "CC", "EE", "BB", "GG", "GG", "SC", "DD", "AA", "SC", "BB", "FF", "AA", "AA", "SC", "WD"],
          ["DD", "EE", "FF", "DD", "AA", "DD", "AA", "AA", "WD", "GG", "FF", "FF", "DD", "GG", "CC", "FF", "FF", "GG", "SC", "WD", "CC", "CC", "WD", "GG", "GG", "GG", "DD", "EE", "GG", "GG", "CC", "DD", "DD", "BB", "BB", "FF", "AA", "AA", "DD", "SC", "BB", "SC", "EE", "WD", "DD", "CC", "SC", "WD", "DD", "GG"],
          ["WD", "CC", "BB", "FF", "AA", "SC", "WD", "AA", "FF", "GG", "GG", "DD", "FF", "WD", "SC", "GG", "SC", "BB", "AA", "WD", "SC", "SC", "AA", "EE", "AA", "EE", "BB", "GG", "GG", "BB", "GG", "EE", "SC", "SC", "BB", "WD", "DD", "GG", "SC", "SC", "DD", "CC", "WD", "GG", "SC", "WD", "DD", "BB", "FF", "CC"]
        ],
        "FreeGameReel": [
          ["SC", "DD", "EE", "GG", "DD", "EE", "SC", "DD", "SC", "FF", "AA", "CC", "BB", "DD", "GG", "BB", "FF", "SC", "BB", "GG", "AA", "EE", "BB", "AA", "DD", "DD", "AA", "FF", "GG", "AA", "SC", "EE", "BB", "BB", "CC", "WD", "CC", "CC", "CC", "EE", "WD", "EE", "CC", "WD", "EE", "SC", "SC", "EE", "WD", "SC"],
          ["SC", "FF", "BB", "CC", "AA", "GG", "GG", "DD", "EE", "DD", "EE", "GG", "SC", "GG", "SC", "GG", "SC", "BB", "BB", "EE", "EE", "CC", "CC", "AA", "AA", "BB", "BB", "FF", "DD", "CC", "SC", "SC", "WD", "BB", "GG", "SC", "EE", "BB", "DD", "BB", "SC", "FF", "SC", "AA", "CC", "GG", "WD", "FF", "BB", "EE"],
          ["GG", "AA", "BB", "EE", "WD", "CC", "GG", "BB", "SC", "BB", "CC", "DD", "SC", "AA", "FF", "DD", "GG", "WD", "DD", "WD", "FF", "WD", "FF", "SC", "BB", "AA", "BB", "GG", "AA", "WD", "FF", "WD", "BB", "GG", "BB", "WD", "FF", "GG", "FF", "AA", "DD", "BB", "DD", "GG", "FF", "AA", "EE", "CC", "CC", "DD"],
          ["BB", "EE", "WD", "GG", "SC", "AA", "EE", "AA", "CC", "CC", "FF", "GG", "CC", "EE", "EE", "BB", "FF", "CC", "DD", "FF", "EE", "SC", "WD", "WD", "AA", "SC", "BB", "EE", "EE", "AA", "GG", "DD", "CC", "SC", "FF", "EE", "CC", "DD", "BB", "CC", "BB", "GG", "FF", "BB", "AA", "EE", "EE", "FF", "WD", "EE"],
          ["BB", "SC", "SC", "EE", "BB", "FF", "CC", "FF", "AA", "EE", "WD", "BB", "DD", "DD", "BB", "CC", "EE", "AA", "AA", "GG", "EE", "GG", "DD", "BB", "AA", "FF", "GG", "WD", "CC", "GG", "EE", "EE", "SC", "CC", "CC", "FF", "DD", "SC", "SC", "CC", "CC", "GG", "FF", "DD", "EE", "SC", "BB", "WD", "FF", "GG"]
        ]
      },
      {
        "BaseGameReel": [
          ["CC", "EE", "GG", "FF", "WD", "SC", "SC", "WD", "BB", "AA", "FF", "CC", "DD", "SC", "GG", "WD", "GG", "BB", "WD", "FF", "GG", "EE", "CC", "DD", "DD", "DD", "DD", "WD", "GG", "CC", "AA", "FF", "CC", "SC", "FF", "GG", "EE", "AA", "AA", "AA", "GG", "FF", "EE", "SC", "AA", "FF", "DD", "SC", "BB", "FF"],
          ["CC", "DD", "GG", "WD", "GG", "CC", "EE", "CC", "CC", "EE", "SC", "WD", "SC", "AA", "FF", "WD", "DD", "FF", "EE", "EE", "FF", "DD", "DD", "AA", "AA", "GG", "SC", "CC", "BB", "SC", "BB", "WD", "EE", "EE", "AA", "WD", "DD", "DD", "SC", "GG", "EE", "BB", "DD", "CC", "FF", "AA", "AA", "SC", "SC", "AA"],
          ["AA", "WD", "GG", "CC", "EE", "WD", "AA", "AA", "AA", "BB", "FF", "EE", "CC", "FF", "SC", "SC", "CC", "EE", "DD", "EE", "EE", "SC", "FF", "DD", "CC", "WD", "DD", "EE", "GG", "DD", "DD", "GG", "CC", "CC", "SC", "CC", "EE", "EE", "WD", "SC", "DD", "EE", "GG", "FF", "AA", "AA", "EE", "SC", "CC", "DD"],
          ["WD", "WD", "DD", "EE", "EE", "CC", "WD", "AA", "WD", "DD", "WD", "BB", "AA", "AA", "EE", "CC", "DD", "GG", "WD", "WD", "SC", "SC", "AA", "CC", "SC", "AA", "SC", "EE", "BB", "CC", "FF", "GG", "EE", "AA", "SC", "GG", "DD", "CC", "AA", "DD", "SC", "FF", "WD", "BB", "SC", "EE", "WD", "DD", "WD", "CC"],
          ["CC", "SC", "WD", "CC", "EE", "SC", "CC", "GG", "BB", "EE", "CC", "EE", "DD", "EE", "WD", "FF", "EE", "EE", "CC", "GG", "SC", "SC", "BB", "EE", "DD", "SC", "EE", "EE", "EE", "AA", "FF", "FF", "SC", "EE", "DD", "EE", "GG", "FF", "BB", "AA", "WD", "EE", "CC", "GG", "CC", "DD", "WD", "AA", "SC", "WD"]
        ],
        "FreeGameReel": [
          ["BB", "AA", "WD", "SC", "DD", "GG", "CC", "DD", "FF", "GG", "CC", "SC", "FF", "DD", "CC", "BB", "FF", "GG", "DD", "FF", "EE", "EE", "AA", "WD", "WD", "EE", "FF", "CC", "SC", "EE", "FF", "SC", "AA", "EE", "WD", "BB", "GG", "AA", "DD", "EE", "WD", "AA", "BB", "AA", "CC", "FF", "BB", "FF", "WD", "GG"],
          ["FF", "WD", "EE", "FF", "CC", "FF", "SC", "DD", "FF", "AA", "EE", "WD", "EE", "WD", "BB", "AA", "DD", "EE", "DD", "DD", "DD", "DD", "DD", "FF", "CC", "FF", "CC", "WD", "GG", "AA", "WD", "CC", "DD", "CC", "CC", "SC", "CC", "DD", "GG", "DD", "BB", "BB", "GG", "BB", "BB", "WD", "DD", "BB", "EE", "DD"],
          ["CC", "CC", "WD", "FF", "SC", "BB", "GG", "EE", "SC", "GG", "FF", "AA", "FF", "CC", "GG", "GG", "SC", "DD", "FF", "AA", "WD", "CC", "AA", "EE", "CC", "DD", "AA", "BB", "CC", "BB", "SC", "EE", "SC", "BB", "FF", "WD", "GG", "GG", "WD", "EE", "SC", "WD", "EE", "CC", "BB", "DD", "AA", "EE", "WD", "FF"],
          ["GG", "EE", "SC", "CC", "BB", "SC", "GG", "CC", "CC", "BB", "AA", "DD", "BB", "EE", "GG", "DD", "BB", "CC", "DD", "GG", "CC", "EE", "WD", "WD", "GG", "WD", "AA", "EE", "SC", "WD", "SC", "CC", "WD", "EE", "SC", "FF", "WD", "FF", "DD", "AA", "WD", "WD", "EE", "FF", "WD", "GG", "FF", "GG", "GG", "BB"],
          ["FF", "WD", "EE", "CC", "GG", "EE", "WD", "GG", "AA", "CC", "EE", "BB", "DD", "WD", "WD", "GG", "DD", "SC", "EE", "WD", "AA", "GG", "GG", "EE", "DD", "CC", "FF", "CC", "CC", "SC", "AA", "SC", "AA", "CC", "FF", "DD", "FF", "SC", "CC", "WD", "DD", "FF", "AA", "FF", "CC", "DD", "DD", "GG", "EE", "WD"]
        ]
      },
      {
        "BaseGameReel": [
          ["SC", "BB", "FF", "AA", "GG", "WD", "FF", "BB", "GG", "GG", "FF", "DD", "FF", "WD", "AA", "GG", "EE", "FF", "WD", "BB", "BB", "SC", "DD", "CC", "SC", "EE", "EE", "EE", "DD", "WD", "GG", "WD", "CC", "SC", "EE", "FF", "AA", "AA", "CC", "SC", "CC", "FF", "SC", "WD", "CC", "GG", "EE", "GG", "WD", "BB"],
          ["WD", "SC", "SC", "AA", "GG", "GG", "SC", "AA", "BB", "FF", "FF", "FF", "DD", "GG", "SC", "DD", "CC", "FF", "FF", "DD", "BB", "WD", "CC", "FF", "BB", "AA", "FF", "DD", "WD", "DD", "EE", "FF", "DD", "CC", "EE", "FF", "WD", "DD", "CC", "WD", "BB", "GG", "BB", "EE", "BB", "EE", "FF", "GG", "BB", "AA"],
          ["BB", "AA", "WD", "BB", "CC", "BB", "AA", "SC", "AA", "BB", "DD", "AA", "CC", "SC", "SC", "EE", "DD", "GG", "EE", "WD", "SC", "EE", "CC", "FF", "SC", "DD", "DD", "FF", "CC", "GG", "GG", "GG", "EE", "DD", "CC", "WD", "AA", "BB", "AA", "WD", "FF", "WD", "EE", "BB", "FF", "WD", "WD", "CC", "CC", "WD"],
          ["FF", "WD", "AA", "BB", "WD", "GG", "AA", "CC", "AA", "CC", "DD", "EE", "FF", "WD", "AA", "FF", "SC", "GG", "DD", "DD", "WD", "FF", "EE", "GG", "AA", "FF", "CC", "AA", "FF", "WD", "AA", "FF", "DD", "WD", "DD", "EE", "SC", "GG", "CC", "SC", "CC", "SC", "CC", "GG", "WD", "DD", "EE", "EE", "GG", "DD"],
          ["AA", "BB", "DD", "GG", "SC", "AA", "GG", "WD", "CC", "EE", "DD", "DD", "BB", "BB", "BB", "FF", "BB", "FF", "FF", "GG", "SC", "EE", "CC", "GG", "GG", "GG", "CC", "SC", "EE", "GG", "DD", "BB", "SC", "SC", "DD", "EE", "AA", "DD", "SC", "DD", "FF", "EE", "CC", "DD", "FF", "BB", "BB", "AA", "AA", "BB"]
        ],
        "FreeGameReel": [
          ["BB", "BB", "FF", "CC", "SC", "AA", "CC", "WD", "FF", "SC", "AA", "DD", "EE", "EE", "SC", "GG", "CC", "BB", "SC", "DD", "CC", "WD", "EE", "AA", "GG", "EE", "DD", "DD", "AA", "DD", "AA", "WD", "AA", "DD", "CC", "BB", "AA", "DD", "SC", "WD", "GG", "AA", "AA", "DD", "EE", "SC", "DD", "DD", "EE", "GG"],
          ["WD", "CC", "SC", "DD", "SC", "GG", "BB", "GG", "EE", "WD", "FF", "AA", "FF", "AA", "GG", "DD", "DD", "CC", "SC", "FF", "CC", "GG", "SC", "GG", "AA", "GG", "GG", "FF", "EE", "DD", "EE", "BB", "EE", "GG", "DD", "CC", "DD", "FF", "GG", "WD", "GG", "SC", "FF", "DD", "DD", "SC", "SC", "WD", "AA", "AA"],
          ["DD", "EE", "DD", "GG", "WD", "DD", "CC", "FF", "GG", "DD", "WD", "WD", "DD", "FF", "EE", "BB", "GG", "SC", "FF", "EE", "WD", "FF", "AA", "BB", "BB", "WD", "EE", "GG", "FF", "AA", "GG", "FF", "SC", "GG", "FF", "EE", "GG", "SC", "GG", "DD", "BB", "DD", "EE", "GG", "CC", "DD", "FF", "CC", "SC", "WD"],
          ["WD", "CC", "CC", "DD", "EE", "CC", "SC", "EE", "CC", "BB", "CC", "EE", "AA", "EE", "GG", "FF", "GG", "EE", "DD", "EE", "EE", "GG", "GG", "BB", "CC", "CC", "CC", "SC", "BB", "FF", "AA", "DD", "SC", "BB", "AA", "CC", "CC", "CC", "GG", "AA", "SC", "EE", "AA", "SC", "GG", "FF", "DD", "GG", "DD", "FF"],
          ["DD", "DD", "GG", "WD", "FF", "AA", "GG", "GG", "EE", "BB", "CC", "GG", "CC", "WD", "SC", "CC", "EE", "DD", "WD", "CC", "CC", "EE", "CC", "DD", "CC", "CC", "BB", "AA", "FF", "WD", "FF", "AA", "FF", "BB", "GG", "BB", "CC", "EE", "GG", "EE", "CC", "SC", "SC", "AA", "SC", "CC", "SC", "CC", "WD", "CC"]
        ]
      },
      {
        "BaseGameReel": [
          ["EE", "AA", "FF", "AA", "WD", "WD", "GG", "DD", "GG", "BB", "SC", "GG", "BB", "SC", "WD", "BB", "FF", "SC", "SC", "CC", "WD", "FF", "EE", "EE", "SC", "CC", "CC", "AA", "DD", "EE", "BB", "WD", "CC", "WD", "GG", "DD", "BB", "DD", "FF", "CC", "CC", "WD", "BB", "AA", "EE", "FF", "GG", "EE", "SC", "FF"],
          ["EE", "BB", "AA", "SC", "EE", "DD", "FF", "AA", "BB", "GG", "CC", "AA", "DD", "DD", "AA", "CC", "EE", "FF", "WD", "DD", "EE", "DD", "WD", "GG", "FF", "DD", "WD", "BB", "DD", "WD", "DD", "EE", "WD", "DD", "GG", "AA", "FF", "SC", "WD", "CC", "AA", "WD", "CC", "BB", "SC", "GG", "FF", "GG", "FF", "FF"],
          ["WD", "CC", "EE", "AA", "DD", "DD", "SC", "FF", "EE", "EE", "FF", "DD", "WD", "DD", "BB", "CC", "DD", "DD", "CC", "FF", "GG", "AA", "CC", "FF", "EE", "DD", "AA", "EE", "EE", "AA", "DD", "BB", "AA", "SC", "CC", "GG", "CC", "BB", "BB", "DD", "DD", "CC", "SC", "DD", "CC", "DD", "BB", "FF", "BB", "DD"],
          ["CC", "EE", "BB", "BB", "AA", "WD", "GG", "EE", "BB", "CC", "SC", "FF", "DD", "CC", "WD", "EE", "EE", "BB", "GG", "DD", "AA", "WD", "SC", "BB", "EE", "GG", "SC", "WD", "WD", "EE", "SC", "SC", "FF", "BB", "AA", "SC", "BB", "WD", "WD", "BB", "FF", "CC", "DD", "GG", "SC", "EE", "WD", "FF", "AA", "EE"],
          ["WD", "BB", "DD", "DD", "AA", "CC", "FF", "DD", "CC", "FF", "AA", "WD", "CC", "WD", "SC", "BB", "BB", "WD", "CC", "WD", "AA", "DD", "BB", "CC", "WD", "FF", "WD", "WD", "EE", "WD", "WD", "GG", "SC", "SC", "GG", "EE", "CC", "EE", "EE", "EE", "FF", "WD", "AA", "SC", "SC", "WD", "GG", "EE", "WD", "DD"]
        ],
        "FreeGameReel": [
          ["FF", "GG", "DD", "EE", "AA", "SC", "FF", "DD", "WD", "AA", "FF", "WD", "DD", "CC", "SC", "DD", "CC", "FF", "GG", "GG", "FF", "GG", "AA", "WD", "BB", "GG", "AA", "GG", "FF", "EE", "WD", "BB", "CC", "CC", "DD", "BB", "SC", "FF", "WD", "SC", "WD", "CC", "FF", "GG", "BB", "FF", "EE", "SC", "FF", "WD"],
          ["GG", "EE", "CC", "DD", "FF", "BB", "BB", "SC", "SC", "DD", "AA", "EE", "WD", "SC", "SC", "BB", "WD", "DD", "DD", "CC", "SC", "AA", "GG", "FF", "GG", "BB", "EE", "FF", "AA", "EE", "BB", "WD", "CC", "AA", "FF", "EE", "AA", "GG", "SC", "FF", "GG", "GG", "AA", "SC", "EE", "EE", "GG", "FF", "FF", "BB"],
          ["DD", "WD", "GG", "AA", "WD", "DD", "EE", "SC", "DD", "FF", "GG", "EE", "SC", "GG", "EE", "SC", "BB", "AA", "BB", "EE", "AA", "BB", "BB", "BB", "DD", "SC", "BB", "FF", "EE", "SC", "DD", "EE", "SC", "CC", "CC", "CC", "DD", "FF", "GG", "SC", "WD", "EE", "AA", "FF", "CC", "SC", "EE", "AA", "DD", "GG"],
          ["FF", "CC", "AA", "GG", "GG", "WD", "AA", "CC", "CC", "AA", "CC", "EE", "WD", "AA", "GG", "SC", "CC", "SC", "EE", "CC", "GG", "BB", "EE", "WD", "CC", "SC", "SC", "CC", "GG", "GG", "CC", "DD", "AA", "WD", "WD", "FF", "WD", "DD", "BB", "SC", "BB", "EE", "AA", "CC", "FF", "FF", "CC", "WD", "FF", "GG"],
          ["EE", "BB", "GG", "GG", "WD", "DD", "BB", "EE", "AA", "DD", "FF", "FF", "SC", "FF", "FF", "EE", "WD", "FF", "FF", "SC", "EE", "FF", "AA", "GG", "AA", "DD", "DD", "FF", "SC", "DD", "CC", "EE", "AA", "EE", "CC", "FF", "SC", "GG", "WD", "CC", "AA", "CC", "BB", "FF", "GG", "EE", "SC", "GG", "CC", "GG"]
        ]
      },
      {
        "BaseGameReel": [
          ["FF", "EE", "SC", "AA", "CC", "EE", "WD", "CC", "SC", "AA", "CC", "AA", "GG", "EE", "SC", "GG", "FF", "WD", "AA", "DD", "AA", "EE", "AA", "EE", "CC", "SC", "SC", "EE", "SC", "DD", "BB", "DD", "BB", "BB", "DD", "DD", "CC", "AA", "GG", "AA", "WD", "CC", "GG", "AA", "GG", "FF", "EE", "WD", "CC", "WD"],
          ["EE", "FF", "AA", "GG", "GG", "DD", "WD", "SC", "BB", "EE", "AA", "SC", "WD", "GG", "WD", "FF", "DD", "AA", "WD", "AA", "CC", "SC", "FF", "FF", "GG", "SC", "CC", "FF", "BB", "WD", "BB", "AA", "WD", "BB", "AA", "CC", "GG", "BB", "BB", "AA", "EE", "WD", "DD", "DD", "DD", "AA", "AA", "GG", "AA", "AA"],
          ["EE", "CC", "DD", "FF", "DD", "WD", "EE", "AA", "FF", "FF", "EE", "GG", "FF", "FF", "CC", "EE", "BB", "GG", "CC", "SC", "WD", "AA", "WD", "CC", "DD", "AA", "GG", "SC", "SC", "WD", "WD", "BB", "CC", "AA", "GG", "FF", "BB", "EE", "FF", "GG", "SC", "DD", "DD", "FF", "CC", "AA", "BB", "EE", "EE", "SC"],
          ["AA", "GG", "DD", "BB", "CC", "BB", "EE", "EE", "FF", "SC", "AA", "AA", "EE", "CC", "WD", "CC", "BB", "GG", "EE", "WD", "WD", "DD", "GG", "BB", "GG", "CC", "GG", "GG", "FF", "CC", "BB", "AA", "AA", "AA", "FF", "DD", "BB", "GG", "BB", "DD", "DD", "AA", "DD", "CC", "WD", "DD", "DD", "BB", "DD", "EE"],
          ["BB", "BB", "WD", "BB", "SC", "CC", "SC", "AA", "DD", "AA", "GG", "FF", "WD", "EE", "BB", "FF", "WD", "BB", "DD", "DD", "GG", "AA", "WD", "GG", "BB", "EE", "WD", "EE", "DD", "WD", "WD", "CC", "DD", "FF", "AA", "BB", "EE", "CC", "BB", "WD", "CC", "FF", "CC", "GG", "DD", "EE", "WD", "FF", "AA", "FF"]
        ],
        "FreeGameReel": [
          ["DD", "CC", "FF", "FF", "WD", "GG", "BB", "SC", "AA", "EE", "EE", "FF", "WD", "GG", "FF", "DD", "CC", "WD", "WD", "GG", "WD", "EE", "FF", "EE", "SC", "WD", "BB", "GG", "AA", "AA", "WD", "CC", "CC", "BB", "WD", "EE", "GG", "DD", "FF", "AA", "SC", "GG", "BB", "GG", "GG", "GG", "BB", "DD", "GG", "FF"],
          ["GG", "GG", "CC", "DD", "DD", "GG", "SC", "BB", "EE", "DD", "GG", "CC", "SC", "CC", "AA", "WD", "GG", "AA", "DD", "WD", "CC", "CC", "SC", "EE", "BB", "AA", "BB", "FF", "FF", "AA", "EE", "EE", "BB", "DD", "SC", "EE", "EE", "DD", "FF", "EE", "DD", "SC", "EE", "WD", "CC", "FF", "WD", "EE", "DD", "SC"],
          ["AA", "CC", "AA", "WD", "WD", "FF", "EE", "FF", "GG", "SC", "DD", "DD", "WD", "DD", "WD", "EE", "GG", "AA", "FF", "FF", "BB", "WD", "CC", "BB", "SC", "BB", "BB", "GG", "SC", "EE", "FF", "DD", "GG", "EE", "BB", "CC", "CC", "WD", "FF", "SC", "EE", "FF", "EE", "AA", "AA", "SC", "DD", "EE", "FF", "GG"],
          ["CC", "EE", "BB", "WD", "BB", "AA", "FF", "AA", "WD", "EE", "CC", "DD", "DD", "FF", "SC", "BB", "SC", "GG", "BB", "GG", "CC", "GG", "BB", "AA", "CC", "BB", "AA", "FF", "WD", "EE", "CC", "BB", "CC", "CC", "GG", "DD", "FF", "FF", "FF", "SC", "BB", "SC", "CC", "WD", "DD", "CC", "GG", "CC", "SC", "AA"],
          ["EE", "GG", "WD", "AA", "GG", "BB", "FF", "CC", "DD", "CC", "EE", "AA", "CC", "SC", "WD", "WD", "WD", "WD", "SC", "WD", "DD", "GG", "SC", "EE", "FF", "BB", "BB", "SC", "AA", "GG", "WD", "AA", "FF", "EE", "FF", "WD", "DD", "CC", "WD", "FF", "AA", "FF", "CC", "AA", "AA", "GG", "EE", "BB", "SC", "SC"]
        ]
      },
      {
        "BaseGameReel": [
          ["DD", "SC", "EE", "DD", "FF", "EE", "CC", "FF", "BB", "WD", "WD", "EE", "BB", "WD", "CC", "CC", "GG", "SC", "BB", "DD", "EE", "DD", "FF", "CC", "DD", "GG", "BB", "EE", "FF", "SC", "FF", "FF", "BB", "CC", "EE", "FF", "WD", "WD", "GG", "FF", "AA", "DD", "WD", "WD", "CC", "CC", "BB", "FF", "DD", "AA"],
          ["EE", "DD", "AA", "BB", "AA", "FF", "CC", "FF", "AA", "CC", "FF", "FF", "BB", "CC", "WD", "EE", "SC", "FF", "GG", "EE", "SC", "GG", "FF", "AA", "DD", "CC", "AA", "AA", "SC", "BB", "GG", "EE", "EE", "SC", "WD", "FF", "DD", "DD", "DD", "GG", "WD", "CC", "EE", "CC", "AA", "GG", "EE", "CC", "FF", "CC"],
          ["SC", "EE", "FF", "CC", "EE", "SC", "SC", "SC", "GG", "WD", "CC", "BB", "AA", "SC", "CC", "FF", "BB", "GG", "FF", "WD", "WD", "GG", "DD", "FF", "CC", "EE", "EE", "GG", "WD", "AA", "BB", "DD", "AA", "SC", "SC", "EE", "FF", "FF", "CC", "GG", "AA", "EE", "AA", "SC", "GG", "SC", "AA", "GG", "BB", "CC"],
          ["SC", "EE", "EE", "AA", "GG", "AA", "FF", "GG", "SC", "WD", "AA", "SC", "DD", "CC", "SC", "SC", "DD", "SC", "GG", "EE", "BB", "EE", "DD", "FF", "CC", "BB", "BB", "AA", "WD", "CC", "CC", "SC", "DD", "DD", "FF", "CC", "GG", "BB", "WD", "AA", "WD", "WD", "AA", "AA", "EE", "SC", "CC", "SC", "BB", "DD"],
          ["SC", "BB", "WD", "WD", "AA", "CC", "CC", "DD", "BB", "GG", "DD", "WD", "CC", "SC", "GG", "EE", "SC", "FF", "DD", "DD", "FF", "FF", "FF", "FF", "BB", "WD", "WD", "FF", "FF", "GG", "WD", "WD", "AA", "WD", "SC", "SC", "CC", "EE", "DD", "DD", "CC", "EE", "EE", "CC", "DD", "WD", "EE", "FF", "BB", "WD"]
        ],
        "FreeGameReel": [
          ["BB", "GG", "DD", "SC", "DD", "SC", "AA", "AA", "WD", "AA", "DD", "FF", "EE", "SC", "WD", "FF", "EE", "AA", "BB", "WD", "SC", "EE", "FF", "BB", "WD", "AA", "BB", "BB", "WD", "SC", "DD", "AA", "CC", "AA", "DD", "SC", "BB", "CC", "GG", "BB", "WD", "EE", "GG", "SC", "EE", "GG", "DD", "BB", "BB", "FF"],
          ["EE", "AA", "WD", "GG", "GG", "BB", "SC", "BB", "EE", "AA", "SC", "AA", "WD", "SC", "BB", "CC", "SC", "EE", "BB", "WD", "BB", "FF", "AA", "GG", "GG", "FF", "WD", "AA", "DD", "BB", "FF", "GG", "SC", "BB", "BB", "FF", "SC", "AA", "WD", "BB", "GG", "EE", "FF", "EE", "WD", "GG", "CC", "AA", "GG", "GG"],
          ["SC", "SC", "AA", "GG", "WD", "FF", "CC", "EE", "FF", "CC", "BB", "SC", "AA", "BB", "DD", "FF", "CC", "CC", "WD", "BB", "FF", "SC", "EE", "FF", "EE", "BB", "DD", "BB", "DD", "FF", "SC", "CC", "FF", "EE", "BB", "FF", "DD", "AA", "GG", "WD", "FF", "BB", "AA", "WD", "SC", "CC", "AA", "GG", "EE", "FF"],
          ["EE", "DD", "BB", "DD", "EE", "AA", "GG", "CC", "FF", "BB", "WD", "EE", "GG", "CC", "BB", "WD", "GG", "FF", "SC", "CC", "DD", "DD", "AA", "BB", "AA", "AA", "FF", "CC", "GG", "WD", "BB", "DD", "WD", "CC", "FF", "BB", "BB", "EE", "GG", "CC", "DD", "SC", "CC", "FF", "FF", "WD", "SC", "FF", "CC", "BB"],
          ["GG", "DD", "AA", "CC", "DD", "GG", "DD", "CC", "GG", "BB", "BB", "CC", "SC", "AA", "DD", "WD", "EE", "AA", "GG", "SC", "FF", "EE", "FF", "WD", "EE", "WD", "FF", "BB", "GG", "DD", "DD", "SC", "CC", "AA", "CC", "WD", "CC", "DD", "BB", "BB", "SC", "DD", "CC", "WD", "BB", "BB", "SC", "BB", "AA", "WD"]
        ]
      },
      {
        "BaseGameReel": [
          ["EE", "DD", "BB", "SC", "DD", "GG", "CC", "SC", "CC", "CC", "SC", "WD", "DD", "GG", "EE", "AA", "AA", "BB", "FF", "BB", "GG", "GG", "GG", "GG", "EE", "BB", "EE", "WD", "FF", "AA", "BB", "FF", "WD", "AA", "DD", "EE", "EE", "WD", "AA", "FF", "SC", "EE", "DD", "GG", "SC", "GG", "EE", "SC", "AA", "EE"],
          ["AA", "CC", "GG", "AA", "GG", "FF", "WD", "WD", "GG", "WD", "CC", "WD", "EE", "FF", "AA", "WD", "DD", "AA", "CC", "BB", "GG", "WD", "DD", "GG", "FF", "GG", "EE", "DD", "EE", "AA", "BB", "EE", "BB", "FF", "GG", "BB", "FF", "BB", "FF", "GG", "FF", "CC", "WD", "SC", "FF", "EE", "BB", "WD", "DD", "SC"],
          ["AA", "WD", "EE", "DD", "AA", "GG", "DD", "FF", "DD", "WD", "WD", "BB", "CC", "SC", "BB", "GG", "BB", "SC", "GG", "SC", "GG", "EE", "SC", "GG", "SC", "SC", "EE", "DD", "WD", "CC", "WD", "BB", "EE", "FF", "FF", "WD", "EE", "WD", "DD", "CC", "EE", "WD", "FF", "AA", "EE", "BB", "WD", "CC", "EE", "FF"],
          ["DD", "WD", "SC", "GG", "SC", "GG", "EE", "FF", "CC", "BB", "SC", "DD", "AA", "FF", "CC", "EE", "WD", "DD", "BB", "FF", "DD", "GG", "GG", "SC", "BB", "FF", "EE", "SC", "CC", "CC", "SC", "EE", "AA", "FF", "AA", "WD", "WD", "BB", "WD", "DD", "GG", "EE", "EE", "CC", "CC", "GG", "FF", "DD", "GG", "GG"],
          ["EE", "AA", "GG", "GG", "FF", "AA", "SC", "FF", "SC", "GG", "AA", "FF", "WD", "SC", "BB", "WD", "CC", "GG", "EE", "SC", "BB", "SC", "WD", "SC", "DD", "DD", "FF", "SC", "BB", "FF", "BB", "AA", "SC", "GG", "EE", "AA", "GG", "FF", "FF", "SC", "SC", "BB", "BB", "SC", "GG", "GG", "DD", "WD", "CC", "EE"]
        ],
        "FreeGameReel": [
          ["WD", "WD", "WD", "FF", "SC", "FF", "SC", "EE", "WD", "SC", "EE", "AA", "AA", "SC", "DD", "BB", "EE", "DD", "GG", "WD", "EE", "AA", "WD", "CC", "CC", "GG", "FF", "DD", "FF", "SC", "DD", "BB", "WD", "EE", "WD", "GG", "GG", "CC", "GG", "BB", "SC", "AA", "FF", "DD", "FF", "DD", "EE", "AA", "CC", "SC"],
          ["FF", "FF", "EE", "WD", "WD", "DD", "BB", "CC", "WD", "AA", "SC", "DD", "BB", "DD", "BB", "DD", "DD", "BB", "SC", "CC", "EE", "GG", "EE", "BB", "SC", "WD", "FF", "SC", "GG", "WD", "EE", "WD", "CC", "EE", "GG", "GG", "GG", "AA", "CC", "FF", "GG", "AA", "EE", "DD", "CC", "GG", "GG", "BB", "EE", "AA"],
          ["SC", "SC", "AA", "CC", "EE", "DD", "SC", "SC", "SC", "DD", "SC", "FF", "EE", "BB", "EE", "WD", "AA", "BB", "GG", "EE", "FF", "AA", "GG", "CC", "EE", "CC", "EE", "DD", "EE", "CC", "AA", "GG", "BB", "DD", "DD", "WD", "EE", "CC", "SC", "GG", "GG", "SC", "DD", "FF", "WD", "SC", "WD", "WD", "AA", "BB"],
          ["EE", "GG", "CC", "GG", "EE", "DD", "GG", "EE", "AA", "AA", "WD", "EE", "EE", "CC", "GG", "EE", "SC", "WD", "SC", "EE", "BB", "CC", "WD", "BB", "FF", "DD", "WD", "SC", "CC", "EE", "DD", "EE", "DD", "BB", "SC", "AA", "WD", "AA", "EE", "DD", "BB", "GG", "BB", "BB", "SC", "WD", "SC", "FF", "FF", "BB"],
          ["GG", "EE", "BB", "FF", "GG", "DD", "SC", "EE", "DD", "EE", "EE", "EE", "WD", "FF", "FF", "CC", "DD", "SC", "FF", "FF", "SC", "DD", "EE", "DD", "BB", "FF", "CC", "DD", "SC", "AA", "AA", "SC", "DD", "SC", "AA", "CC", "CC", "DD", "DD", "SC", "GG", "DD", "BB", "DD", "AA", "BB", "BB", "SC", "GG", "WD"]
        ]
      },
      {
        "BaseGameReel": [
          ["FF", "GG", "AA", "EE", "BB", "DD", "WD", "FF", "GG", "FF", "SC", "BB", "SC", "FF", "CC", "SC", "GG", "DD", "SC", "WD", "GG", "GG", "FF", "DD", "AA", "EE", "FF", "FF", "DD", "AA", "SC", "FF", "AA", "SC", "CC", "BB", "DD", "FF", "GG", "GG", "WD", "CC", "EE", "WD", "DD", "BB", "BB", "GG", "WD", "DD"],
          ["AA", "CC", "DD", "FF", "FF", "FF", "BB", "WD", "EE", "CC", "DD", "DD", "GG", "SC", "EE", "DD", "CC", "EE", "FF", "CC", "AA", "GG", "FF", "CC", "SC", "SC", "EE", "AA", "SC", "SC", "WD", "CC", "WD", "AA", "BB", "DD", "WD", "WD", "BB", "EE", "CC", "CC", "BB", "SC", "AA", "EE", "EE", "WD", "BB", "FF"],
          ["FF", "SC", "WD", "BB", "AA", "DD", "CC", "CC", "BB", "FF", "CC", "DD", "AA", "EE", "GG", "BB", "SC", "AA", "CC", "DD", "BB", "DD", "WD", "WD", "GG", "BB", "GG", "AA", "FF", "FF", "DD", "FF", "WD", "EE", "EE", "GG", "AA", "CC", "BB", "SC", "BB", "WD", "DD", "SC", "EE", "AA", "GG", "WD", "CC", "FF"],
          ["CC", "AA", "BB", "EE", "SC", "CC", "EE", "SC", "AA", "FF", "FF", "FF", "FF", "BB", "EE", "GG", "WD", "GG", "DD", "GG", "CC", "DD", "BB", "BB", "GG", "CC", "CC", "CC", "EE", "FF", "SC", "AA", "EE", "GG", "AA", "BB", "WD", "WD", "SC", "CC", "WD", "SC", "BB", "BB", "FF", "EE", "DD", "CC", "AA", "WD"],
          ["WD", "GG", "FF", "DD", "AA", "GG", "CC", "WD", "BB", "EE", "GG", "SC", "EE", "SC", "SC", "DD", "FF", "DD", "GG", "FF", "SC", "AA", "GG", "EE", "FF", "FF", "BB", "AA", "DD", "CC", "SC", "EE", "EE", "GG", "GG", "BB", "DD", "BB", "GG", "GG", "GG", "WD", "AA", "WD", "BB", "DD", "FF", "AA", "BB", "SC"]
        ],
        "FreeGameReel": [
          ["CC", "BB", "EE", "BB", "DD", "DD", "CC", "EE", "FF", "SC", "FF", "BB", "GG", "BB", "EE", "DD", "BB", "WD", "BB", "AA", "GG", "SC", "AA", "BB", "AA", "EE", "WD", "SC", "CC", "AA", "DD", "GG", "AA", "WD", "BB", "AA", "SC", "EE", "CC", "SC", "CC", "DD", "CC", "FF", "CC", "GG", "FF", "WD", "AA", "DD"],
          ["CC", "AA", "CC", "EE", "DD", "EE", "SC", "EE", "BB", "BB", "FF", "CC", "SC", "FF", "FF", "AA", "EE", "GG", "AA", "BB", "EE", "EE", "AA", "EE", "AA", "CC", "DD", "FF", "GG", "DD", "SC", "WD", "CC", "AA", "DD", "AA", "GG", "FF", "AA", "DD", "FF", "AA", "GG", "FF", "BB", "SC", "FF", "CC", "WD", "WD"],
          ["BB", "DD", "SC", "SC", "CC", "WD", "AA", "GG", "SC", "BB", "GG", "FF", "GG", "GG", "DD", "DD", "DD", "FF", "GG", "EE", "GG", "BB", "FF", "SC", "SC", "CC", "SC", "EE", "CC", "DD", "BB", "WD", "EE", "WD", "DD", "AA", "WD", "WD", "BB", "AA", "WD", "DD", "WD", "CC", "EE", "GG", "WD", "AA", "AA", "SC"],
          ["BB", "EE", "BB", "EE", "BB", "DD", "SC", "EE", "AA", "AA", "DD", "CC", "BB", "DD", "DD", "AA", "SC", "CC", "GG", "WD", "EE", "FF", "SC", "WD", "FF", "DD", "FF", "AA", "AA", "CC", "GG", "SC", "WD", "SC", "SC", "DD", "BB", "EE", "DD", "CC", "GG", "CC", "DD", "DD", "EE", "WD", "FF", "FF", "BB", "FF"],
          ["AA", "AA", "BB", "BB", "GG", "WD", "EE", "EE", "DD", "SC", "AA", "FF", "GG", "CC", "SC", "DD", "EE", "EE", "DD", "GG", "WD", "SC", "WD", "AA", "FF", "EE", "WD", "CC", "DD", "FF", "AA", "FF", "WD", "BB", "AA", "FF", "CC", "AA", "EE", "WD", "AA", "BB", "AA", "BB", "DD", "SC", "FF", "SC", "DD", "GG"]
        ]
      },
      {
        "BaseGameReel": [
          ["DD", "FF", "BB", "WD", "FF", "AA", "CC", "SC", "SC", "EE", "EE", "EE", "AA", "AA", "FF", "EE", "DD", "GG", "DD", "AA", "BB", "GG", "WD", "FF", "AA", "EE", "SC", "WD", "WD", "BB", "WD", "CC", "GG", "AA", "BB", "BB", "EE", "DD", "WD", "WD", "WD", "AA", "SC", "WD", "GG", "CC", "EE", "FF", "AA", "GG"],
          ["FF", "DD", "WD", "CC", "DD", "WD", "WD", "CC", "EE", "FF", "BB", "EE", "SC", "BB", "WD", "AA", "DD", "CC", "GG", "CC", "FF", "EE", "FF", "WD", "WD", "CC", "EE", "FF", "GG", "GG", "FF", "BB", "AA", "WD", "SC", "WD", "BB", "CC", "GG", "DD", "AA", "CC", "AA", "WD", "FF", "FF", "GG", "BB", "CC", "FF"],
          ["AA", "WD", "FF", "CC", "AA", "FF", "EE", "WD", "EE", "GG", "WD", "BB", "BB", "DD", "DD", "EE", "GG", "WD", "BB", "WD", "GG", "FF", "AA", "AA", "BB", "WD", "FF", "FF", "FF", "DD", "BB", "CC", "CC", "CC", "AA", "SC", "CC", "EE", "GG", "EE", "FF", "AA", "AA", "AA", "EE", "SC", "CC", "SC", "EE", "GG"],
          ["EE", "AA", "DD", "SC", "AA", "BB", "FF", "GG", "AA", "SC", "WD", "DD", "BB", "GG", "CC", "CC", "SC", "GG", "EE", "EE", "DD", "CC", "SC", "DD", "CC", "WD", "CC", "WD", "CC", "GG", "AA", "WD", "GG", "FF", "EE", "SC", "AA", "WD", "WD", "EE", "AA", "WD", "EE", "AA", "SC", "FF", "FF", "GG", "AA", "WD"],
          ["EE", "BB", "FF", "EE", "AA", "DD", "GG", "DD", "WD", "EE", "EE", "AA", "SC", "SC", "EE", "CC", "SC", "CC", "GG", "BB", "BB", "GG", "DD", "CC", "EE", "AA", "GG", "SC", "DD", "GG", "WD", "BB", "EE", "BB", "SC", "DD", "SC", "EE", "BB", "SC", "DD", "AA", "FF", "FF", "FF", "BB", "GG", "DD", "AA", "CC"]
        ],
        "FreeGameReel": [
          ["DD", "CC", "DD", "SC", "WD", "BB", "EE", "CC", "BB", "SC", "BB", "CC", "AA", "CC", "FF", "EE", "AA", "SC", "GG", "CC", "BB", "BB", "GG", "DD", "CC", "DD", "FF", "WD", "GG", "EE", "FF", "WD", "SC", "SC", "CC", "EE", "BB", "EE", "DD", "WD", "SC", "DD", "BB", "FF", "EE", "FF", "WD", "DD", "AA", "WD"],
          ["DD", "SC", "FF", "DD", "BB", "WD", "GG", "GG", "AA", "BB", "WD", "FF", "SC", "BB", "FF", "AA", "SC", "AA", "GG", "BB", "CC", "SC", "SC", "GG", "BB", "DD", "GG", "DD", "AA", "AA", "AA", "GG", "CC", "CC", "SC", "DD", "BB", "FF", "FF", "EE", "WD", "EE", "CC", "CC", "CC", "AA", "DD", "GG", "EE", "FF"],
          ["DD", "DD", "AA", "GG", "CC", "WD", "CC", "DD", "GG", "DD", "WD", "FF", "DD", "WD", "BB", "FF", "FF", "DD", "AA", "EE", "CC", "EE", "GG", "BB", "GG", "EE", "FF", "FF", "GG", "SC", "GG", "SC", "BB", "BB", "AA", "BB", "BB", "CC", "CC", "BB", "WD", "CC", "AA", "EE", "FF", "BB", "SC", "WD", "WD", "CC"],
          ["CC", "FF", "CC", "CC", "GG", "BB", "EE", "WD", "FF", "SC", "WD", "EE", "FF", "GG", "SC", "DD", "FF", "DD", "FF", "AA", "SC", "EE", "GG", "BB", "WD", "FF", "FF", "BB", "AA", "AA", "BB", "BB", "GG", "SC", "SC", "BB", "AA", "WD", "CC", "BB", "AA", "CC", "EE", "FF", "AA", "DD", "AA", "AA", "WD", "WD"],
          ["EE", "DD", "AA", "WD", "DD", "EE", "SC", "EE", "GG", "DD", "WD", "EE", "EE", "EE", "DD", "FF", "GG", "FF", "CC", "CC", "SC", "FF", "GG", "BB", "FF", "WD", "SC", "DD", "DD", "BB", "AA", "DD", "WD", "WD", "AA", "GG", "CC", "AA", "FF", "DD", "SC", "WD", "AA", "GG", "FF", "SC", "CC", "GG", "SC", "BB"]
        ]
      }
    ]

if createNewparents:
    CreateInitialPopulation(parentsFolder,populationSize,symbols,reelSize,columnCount)

    initialParents = LoadInitialParents(parentsFolder,populationSize,fitnessvariable)
else:
    for data in parentsReels:
        initialParents.append(Parent(fitnessvariable,data["BaseGameReel"], data["FreeGameReel"]))

EvaluateParents(initialParents,spins,simulatorPath,folder)

start = time.perf_counter()
for mutationCount in mutationCounts:
    for replacementTpye in replacementTypes:
        gen = generations
        if(replacementTpye==ReplacementType.Generational):
            gen = generations//10
        elif (replacementTpye==ReplacementType.ElistismGenerational):
            gen = gen//8
        
        for selectionType in selectionTypes:
            simStart  = time.perf_counter()
            RunOptimization(initialParents,gen,runNumber,replacementTpye,selectionType,mutationCount)
            elapsed = time.perf_counter() - simStart
            print(f"{replacementTpye.name}_{selectionType.name} sim Time taken {elapsed}")

elapsed = time.perf_counter() - start
print(f"Total Time taken {elapsed/60}min")
