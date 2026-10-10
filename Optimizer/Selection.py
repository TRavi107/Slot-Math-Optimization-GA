import random
import math
from collections import Counter
from enum import Enum , auto

class SelectionTypes(Enum):
    TournamentSelection = auto()
    RouletteSelection = auto()
    SUS = auto()


def SUS(parents, weights, n, rng=random, shuffle=True):
    """Stochastic Universal Sampling.
 
    parents : list of Parent objects
    weights : non-negative weight per parent (bigger = more likely)
    n       : number of parents to select
    returns : list of n selected Parent objects
    """
    if len(parents) != len(weights):
        raise ValueError("parents and weights must have the same length.")
    if n <= 0:
        return []
    if any(w < 0 for w in weights):
        raise ValueError("SUS needs non-negative weights.")
    total = sum(weights)
    if total <= 0:
        raise ValueError("Sum of weights must be positive.")
 
    step = total / n                 # spacing between pointers
    ptr = rng.uniform(0, step)       # the single random spin
 
    chosen = []
    cum = weights[0]
    i = 0
    for _ in range(n):
        while ptr >= cum:            # move to the slice that owns this pointer
            i += 1
            cum += weights[i]
        chosen.append(parents[i])
        ptr += step
 
    if shuffle:
        rng.shuffle(chosen)
    return chosen
 
 
def linear_rank_weights(parents, s=2.0):
    """Baker's linear ranking for minimization of parent.fitnessValue.
 
    Largest error  -> rank 1 (worst) -> 2 - s expected copies
    Smallest error -> rank N (best)  -> s expected copies
    Ties get averaged ranks. s in [1, 2].
    """
    n = len(parents)
    if n == 1:
        return [1.0]
    errors = [p.fitnessValue for p in parents]
    order = sorted(range(n), key=lambda k: errors[k], reverse=True)  # worst first
    ranks = [0.0] * n
    pos = 0
    while pos < n:
        end = pos
        while end + 1 < n and errors[order[end + 1]] == errors[order[pos]]:
            end += 1
        avg_rank = (pos + end) / 2 + 1
        for k in range(pos, end + 1):
            ranks[order[k]] = avg_rank
        pos = end + 1
    return [(2 - s) + 2 * (s - 1) * (r - 1) / (n - 1) for r in ranks]
 
 
def boltzmann_weights(parents, T):
    """Boltzmann weights for minimization: w = exp(-fitnessValue / T),
    shifted by the best error so the best weight is exactly 1."""
    e_min = min(p.fitnessValue for p in parents)
    return [math.exp(-(p.fitnessValue - e_min) / T) for p in parents]
 
 
def select_parents(parents, n=None, method="rank", s=2.0, T=0.1, rng=random):
    """Convenience wrapper: build weights, run SUS, return selected Parents."""
    n = len(parents) if n is None else n
    if method == "rank":
        weights = linear_rank_weights(parents, s)
    elif method == "boltzmann":
        weights = boltzmann_weights(parents, T)
    else:
        raise ValueError("method must be 'rank' or 'boltzmann'")
    return SUS(parents, weights, n, rng)



def RouletteSelection(parents, size=2):
    weights = linear_rank_weights(parents, s=2)
    return random.choices(parents, weights=weights, k=size)

def tournamentSelection(parents, tournamentSize=3, winners=2, rng=random):
    k = min(tournamentSize, len(parents))
    return [min(rng.sample(parents, k), key=lambda p: p.fitnessValue)
            for _ in range(winners)]

def crossover(reelset1, reelset2):
    child = []
    for reel1, reel2 in zip(reelset1, reelset2):
        cut = random.randint(1, len(reel1) - 1)
        child.append(reel1[:cut] + reel2[cut:])
    return child

def mutate(reelset, symbols, count, rng=random):
    child = [list(reel) for reel in reelset]

    positions = [(r, i) for r in range(len(child)) for i in range(len(child[r]))]
    count = min(count, len(positions))

    for r, i in rng.sample(positions, count): 
        options = [s for s in symbols if s != child[r][i]]
        child[r][i] = rng.choice(options)

    return child