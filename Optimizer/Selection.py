import random

def tournamentSelection(parents, tournamentSize=3, winners=2):
    # pick 3 random parents (no repeats)
    k = min(tournamentSize, len(parents))
    contenders = random.sample(parents, k)

    # best = fitness closest to 1
    contenders.sort(key=lambda p: p.fitnessValue)

    # best two from the 3

    return contenders[:winners]

def crossover(reelset1, reelset2):
    """
    Child reel set: for each reel, first half from parent 1,
    second half from parent 2.
    """
    child = []
    for reel1, reel2 in zip(reelset1, reelset2):
        mid = len(reel1) // 2
        child.append(reel1[:mid] + reel2[mid:])
    
    return child

def mutate(reelset, symbols, count, rng=random):
    """
    Return a copy of `reelset` with `count` randomly chosen positions
    changed to a different symbol. The original is not modified.
    """
    child = [list(reel) for reel in reelset]          # copy so parents stay untouched

    positions = [(r, i) for r in range(len(child)) for i in range(len(child[r]))]
    count = min(count, len(positions))

    for r, i in rng.sample(positions, count):         # distinct positions, no repeats
        options = [s for s in symbols if s != child[r][i]]
        child[r][i] = rng.choice(options)             # guaranteed to differ from the old symbol

    return child