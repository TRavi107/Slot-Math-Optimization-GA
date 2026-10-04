import random
import json
import os

from Parents import VariableType, findBest

def generate_reelset_col(symbols, reelSize, rng=random):
    if not symbols:
        raise ValueError("symbols list is empty")
    result = list(symbols) + [rng.choice(symbols) for _ in range(reelSize - len(symbols))]
    rng.shuffle(result)
    return result[:reelSize]

def generate_reelset(symbols, reelSize, colSize, rng=random):
    return [generate_reelset_col(symbols, reelSize, rng) for _ in range(colSize)]



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

def make_pairs(pool):
    """Pair neighbours: (0,1), (2,3), ... An odd leftover is returned alone."""
    pairs = [(pool[k], pool[k + 1]) for k in range(0, len(pool) - 1, 2)]
    leftover = pool[-1] if len(pool) % 2 else None
    return pairs, leftover

