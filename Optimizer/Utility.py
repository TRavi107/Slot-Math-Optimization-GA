import random
import json
import os

from Parents import VariableType

def generate_reelset_col(symbols, reelSize, seed=None):
    """
    Return a list of length `size` built from `symbols`,
    adding randomly chosen symbols from the list if it's too short.
    """
    rng = random.Random(seed)
    result = list(symbols)

    if not result:
        raise ValueError("symbols list is empty")

    # Pad with random picks until we reach the target size
    while len(result) < reelSize:
        result.append(rng.choice(symbols))

    # If the list is already longer than size, trim it
    return result[:reelSize]

def generate_reelset(symbols, reelSize,colSize, seed=None):
    """
    Return a list of length `size` built from `symbols`,
    adding randomly chosen symbols from the list if it's too short.
    """
    rng = random.Random(seed)
    result = []

    if not symbols:
        raise ValueError("symbols list is empty")

    # Pad with random picks until we reach the target size
    while len(result) < colSize:
        result.append(generate_reelset_col(symbols,reelSize))

    # If the list is already longer than size, trim it
    return result[:colSize]



def format_parents(datas, indent=4):
    """Format a list of reel sets with one reel per line."""
    pad = " " * indent
    sets = []
    for reelset in datas:
        reels = ",\n".join(f"{pad * 3}{json.dumps(reel)}" for reel in reelset)
        sets.append(f"{pad * 2}[\n{reels}\n{pad * 2}]")
    return f"[\n" + ",\n".join(sets) + f"\n{pad}]"


def save_reels(key_name, value, path="parents.json"):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)   # creates ReelSets/ if missing

    pad = " " * 2
    text = (
        "{\n"
        f'{pad}"{key_name}": {format_parents(value, 2)},\n'
        f'{pad}"FreeGameReel": {format_parents(value, 2)}\n'
        "}\n"
    )
    json.loads(text)
    with open(path, "w") as f:
        f.write(text)

def save_reelset_file(base_reelset, free_reelset, path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    def block(reelset):
        reels = ",\n".join(f"      {json.dumps(reel)}" for reel in reelset)
        return f"[\n    [\n{reels}\n    ]\n  ]"

    text = (
        "{\n"
        f'  "BaseGameReel": {block(base_reelset)},\n'
        f'  "FreeGameReel": {block(free_reelset)}\n'
        "}\n"
    )
    json.loads(text)  # sanity check
    with open(path, "w") as f:
        f.write(text)

def UpdateParentVars(parent, output):
    parent.updateFitnessVariable(VariableType.baseRTP,output['baseRTP'])
    parent.updateFitnessVariable(VariableType.baseHitRate,output['baseHitRate'])
    parent.updateFitnessVariable(VariableType.freeRTP,output['freeRTP'])
    parent.updateFitnessVariable(VariableType.freeHitRate,output['freeHitRate'])
    parent.updateFitnessVariable(VariableType.freeTriggerRate,output['freeTriggerRate'])
    parent.CalcuteFitness()



