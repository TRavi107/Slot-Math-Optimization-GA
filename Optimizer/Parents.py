from enum import Enum,auto
import copy

class Parent:
    baseReelSet = []
    freeReelSet = []
    fitnessVariable = []
    fitnessValue = 0;

    def __init__(self,fitnessVariable:list [FitnessVariable], baseReelSet=None, freeReelSet=None):
        self.fitnessVariable = copy.deepcopy(fitnessVariable)
        self.baseReelSet = baseReelSet
        self.freeReelSet = freeReelSet
        self.fitnessValue = float("inf")   # unevaluated = worst possible

    def CalcuteFitness(self):
        self.fitnessValue = 0
        for var in self.fitnessVariable:
            error = abs(var.currentValue-var.targetValue)/var.targetValue
            self.fitnessValue += error*var.weight

        return self.fitnessValue

    def updateFitnessVariable(self,varName: VariableType,currentValue):
        fitnessVar = self.find_by_name(varName)
        if(fitnessVar ==None):
            print(f"{varName} not found")
            return

        fitnessVar.currentValue = currentValue

    def printData(self):
        for varibale in self.fitnessVariable:
            print(f"{varibale.varName.name} : {varibale.currentValue}")

    def find_by_name(self, name: VariableType) -> FitnessVariable | None:
        return next((v for v in self.fitnessVariable if v.varName is name), None)

def findBest(parents):       return min(parents, key=lambda p: p.fitnessValue)
def findWorst(parents):      return max(parents, key=lambda p: p.fitnessValue)
def findWorstIndex(parents): return max(range(len(parents)), key=lambda i: parents[i].fitnessValue)
def findBestIndex(parents): return min(range(len(parents)), key=lambda i: parents[i].fitnessValue)

def UpdateParentVars(parent, output):
    parent.updateFitnessVariable(VariableType.baseRTP,output['baseRTP'])
    parent.updateFitnessVariable(VariableType.baseHitRate,output['baseHitRate'])
    # parent.updateFitnessVariable(VariableType.freeRTP,output['freeRTP'])
    # parent.updateFitnessVariable(VariableType.freeHitRate,output['freeHitRate'])
    # parent.updateFitnessVariable(VariableType.freeRetriggerRate,output['freeReTriggerRate'])
    parent.updateFitnessVariable(VariableType.freeTriggerRate,output['freeTriggerRate'])
    parent.CalcuteFitness()

class FitnessVariable:
    varName = None
    currentValue = 0
    targetValue = 0
    weight = 1.0
    def __init__(self, varName:VariableType, currentValue,targetValue,weight):
        self.varName = varName
        self.currentValue = currentValue
        self.targetValue = targetValue
        self.weight = weight

class VariableType(Enum):
    baseRTP = auto()
    freeRTP = auto()
    baseHitRate = auto()
    freeHitRate = auto()
    freeTriggerRate = auto()
    freeRetriggerRate = auto()

class GameMode(Enum):
    BaseGame = auto()
    FreeGame = auto()
