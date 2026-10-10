import random
import json
import os
import re
import json, subprocess, tempfile, os

from Parents import Parent, UpdateParentVars, VariableType, findBest

def Evaluate(spin_count, reelset_path, exe, run_only_base=False):
    fd, out_path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    try:
        proc = subprocess.run(
            [
                exe,
                str(spin_count),
                reelset_path,
                "true" if run_only_base else "false",   # argv[3]
                out_path,                               # argv[4]
            ],
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            timeout=3600,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                f"myapp failed ({proc.returncode}):\n{proc.stdout}{proc.stderr}"
            )
        with open(out_path, encoding="utf-8") as f:
            return json.load(f)
    finally:
        os.remove(out_path)

def _compact(text):
    pattern = r'\[\s*((?:"[^"\n]*"|-?\d[\d.eE+-]*)(?:,\s*(?:"[^"\n]*"|-?\d[\d.eE+-]*))*)\s*\]'
    return re.sub(pattern,
                  lambda m: "[" + re.sub(r",\s+", ", ", m.group(1)) + "]",
                  text)

def save_sim_results(startingParents, results, best_parent, replacement_type, selection_type,
                     filepath, mutation, seed):
    data = {}
    if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
        with open(filepath, "r") as f:
            data = json.load(f)

    seed_key = f"seed_{seed}"
    mutation_key = f"mutation_{mutation}"
    combo_key = f"{replacement_type.name}_{selection_type.name}"

    seed_entry = data.setdefault(seed_key, {})

    # initial population is the same for every mutation count under a seed,
    # so only write it once
    if "initial_population" not in seed_entry:
        seed_entry["initial_population"] = [
            {
                "BaseGameReel": p.baseReelSet,
                "FreeGameReel": p.freeReelSet,
            }
            for p in startingParents
        ]

    mutation_entry = seed_entry.setdefault("results", {}).setdefault(mutation_key, {})

    mutation_entry[combo_key] = {
        "results": [[float(fit), float(dist)] for fit, dist in results],
        "reelset": {
            "BaseGameReel": best_parent.baseReelSet,
            "FreeGameReel": best_parent.freeReelSet,
        },
    }

    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    tmp = filepath + ".tmp"
    with open(tmp, "w") as f:
        f.write(_compact(json.dumps(data, indent=2)))
    os.replace(tmp, filepath)
    return f"{seed_key}/{mutation_key}/{combo_key}"

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

def CreateInitialPopulation(filepath, populationSize,symbols ,reelSize ,columnCount):
    for i in range(populationSize):
        base = generate_reelset(symbols, reelSize, columnCount)
        free = generate_reelset(symbols, reelSize, columnCount)
        save_reelset_file(base, free, f"{filepath}/parent{i}.json")

def LoadInitialParents(parentPath,populationSize,fitnessvariable):
    parents = []
    for i in range(populationSize):
        with open(f"{parentPath}/parent{i}.json") as f:
            data = json.load(f)
        # [0] unwraps the extra list level, so baseReelSet[0] is reel 0
        parents.append(Parent(fitnessvariable,data["BaseGameReel"][0], data["FreeGameReel"][0]))
    return parents

def EvaluateAndSaveParents(parent, spin, simulatorPath, savepath, runBaseOnly):
    save_reelset_file(parent.baseReelSet, parent.freeReelSet, savepath)
    output = Evaluate(spin, savepath, simulatorPath,runBaseOnly)
    UpdateParentVars(parent, output)

def EvaluateParents(parents, spins, simulatorPath, folder,runBaseOnly):
    for i, p in enumerate(parents):
        path = f"{folder}/parent{i}.json"
        save_reelset_file(p.baseReelSet, p.freeReelSet, path)
        output = Evaluate(spins, path, simulatorPath,runBaseOnly)
        UpdateParentVars(p, output)
        print(f"parent{i}: fitness {p.fitnessValue:.4f}, rtp {output['totalRTP'] * 100:.2f} %")