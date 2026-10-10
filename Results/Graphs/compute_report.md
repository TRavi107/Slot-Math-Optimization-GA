# Computing cost (BaseGame stage)

Every simulator call the optimizer made was timed (wall time as the optimizer pays it, including starting the simulator and reading its output). The optimizer stores the total time per method and run, so time per evaluation is total time / evaluations.

## Machines

| Id | CPU | Cores / logical CPUs | Threads used | Memory | OS | Compiler | Build | Python |
|---|---|---|---|---|---|---|---|---|
| d996e89bd3 | AMD Ryzen 5 5500U with Radeon Graphics | 6 / 12 | 1 | 5.6 GB | Linux 7.0.0-38-generic | GCC 15.2.0 | Release | 3.14.4 |

## Time per evaluation

Every evaluation simulates 1,000,000 spins (base game only). Differences between methods come from the reelsets they propose: reelsets that trigger more free games play more spins.

| Method | Runs | Evaluations | Seconds per evaluation | Fastest run | Slowest run |
|---|---|---|---|---|---|
| Steady-state + Tournament | 4 | 200 | 0.216 s | 0.187 s | 0.232 s |
| Steady-state + Roulette | 4 | 200 | 0.220 s | 0.214 s | 0.237 s |
| Steady-state + SUS | 4 | 200 | 0.225 s | 0.215 s | 0.231 s |
| Elitist generational + Tournament | 4 | 192 | 0.219 s | 0.207 s | 0.229 s |
| Elitist generational + Roulette | 4 | 192 | 0.229 s | 0.223 s | 0.233 s |
| Elitist generational + SUS | 4 | 192 | 0.227 s | 0.209 s | 0.240 s |
| Generational + Tournament | 4 | 200 | 0.230 s | 0.221 s | 0.240 s |
| Generational + Roulette | 4 | 200 | 0.232 s | 0.223 s | 0.242 s |
| Generational + SUS | 4 | 200 | 0.230 s | 0.226 s | 0.236 s |
| Baseline: Hill climbing (1+1)-EA | 4 | 200 | 0.219 s | 0.190 s | 0.252 s |
| Baseline: Simulated annealing | 4 | 200 | 0.216 s | 0.192 s | 0.235 s |
| Baseline: Random search | 2 | 100 | 0.237 s | 0.233 s | 0.240 s |
| **All** | 46 | 2,276 | **0.224 s** | 0.187 s | 0.252 s |

That is about 4.5M spins per second on 1 thread (4.47M per thread); 4 ms of each call is outside the spinning (starting the simulator, reading the reelset, writing the JSON).

> **Thread use:** 1,000,000 spins are 1 jobs of 1M, so at most 1 of the 9 threads this machine would use are busy. More cores do not make an evaluation at this spin count faster; more spins per evaluation would come almost free up to 9M.

## Time per run

One run = one method on one seed: 50 evaluations, plus the final check of its best reelset. Overhead is the optimizer's own work (selection, files, saving results).

| Method | Runs | Wall time | Search | Final check | Overhead |
|---|---|---|---|---|---|
| Steady-state + Tournament | 4 | 12 s | 11 s | 1.04 s | 0.10 s (0.8%) |
| Steady-state + Roulette | 4 | 13 s | 11 s | 1.63 s | 0.10 s (0.7%) |
| Steady-state + SUS | 4 | 13 s | 11 s | 1.49 s | 0.10 s (0.7%) |
| Elitist generational + Tournament | 4 | 12 s | 11 s | 2.01 s | 0.08 s (0.7%) |
| Elitist generational + Roulette | 4 | 13 s | 11 s | 2.07 s | 0.08 s (0.6%) |
| Elitist generational + SUS | 4 | 12 s | 11 s | 1.69 s | 0.08 s (0.7%) |
| Generational + Tournament | 4 | 14 s | 12 s | 2.27 s | 0.08 s (0.6%) |
| Generational + Roulette | 4 | 14 s | 12 s | 2.64 s | 0.09 s (0.6%) |
| Generational + SUS | 4 | 14 s | 11 s | 2.00 s | 0.09 s (0.6%) |
| Baseline: Hill climbing (1+1)-EA | 4 | 12 s | 11 s | 1.55 s | 0.09 s (0.7%) |
| Baseline: Simulated annealing | 4 | 12 s | 11 s | 1.65 s | 0.09 s (0.7%) |
| Baseline: Random search | 2 | 16 s | 12 s | 3.83 s | 0.08 s (0.5%) |

A whole BaseGame stage of one seed (all 23 methods, initial population included) took 5.1 min (median over 2 seeds).

## Whole study (every stage in the file)

Simulation = time spent in simulator calls; CPU time = simulator time × threads it used; wall time = the stages' own clocks (includes the optimizer's work).

| Stage | Seeds | Runs | Simulator calls | Simulation | CPU time | Wall time |
|---|---|---|---|---|---|---|
| BaseGame | 2 | 46 | 2,322 | 10.0 min | 21.8 min | 10.2 min |
| FreeGame | 2 | 46 | 2,322 | 33.8 min | 32.3 min | 33.9 min |
| **Total** | | **92** | **4,644** | **43.8 min** | **54.1 min** | **44.1 min** |

Random search is run once per seed and saved under every mutation count; the copies are not counted.

## Choosing the settings

### Spins per evaluation (run.spins = 1,000,000)

Noise: fitness SD of one evaluation is 0.034 at 10M spins (BaseGame, simulator noise study) and falls as 1/√spins. The noise floor is the smallest fitness difference two evaluations can resolve (2.77 SD, 95%). Cost: seconds per evaluation from the model in 10_compute_cost.png, measured at the run's spins.

| Spins | Seconds per evaluation | One run (50 evaluations) | This stage's 46 runs | Fitness SD | Noise floor |
|---|---|---|---|---|---|
| **1M** | 0.23 s | 11 s | 8.7 min | 0.1075 | **0.2978** |
| 2M | 0.23 s | 11 s | 8.7 min | 0.0760 | 0.2106 |
| 5M | 0.23 s | 11 s | 8.7 min | 0.0481 | 0.1332 |
| 10M | 0.45 s | 23 s | 17.3 min | 0.0340 | 0.0942 |
| 20M | 0.68 s | 34 s | 25.9 min | 0.0240 | 0.0666 |
| 40M | 1.12 s | 56 s | 43.0 min | 0.0170 | 0.0471 |
| 100M | 2.69 s | 2.2 min | 103.1 min | 0.0108 | 0.0298 |

- **Fewer spins** (0.1M): 1.0× faster, but the noise floor rises to 0.942.
- **More spins** (4M): the floor halves to 0.149, but every run takes 1.0× as long (11 s → 11 s), and these 46 runs 8.7 min → 8.7 min. That time buys more seeds instead, which the statistical tests need more.
- At 1M the noise floor is 0.298 against a best median final error of 19.097. The final check (finalCheckSpins) then measures each best reelset precisely once.

### Evaluation budget (run.generations = 50)

Median best-so-far error (mutation 5) at each quarter of the budget, and what the last quarter bought. Noise floor at 1M spins: 0.298. One quarter of a run costs 2.81 s of simulation.

| Method | Seeds | @12 | @25 | @38 | @50 | Last-quarter gain | Above noise floor |
|---|---|---|---|---|---|---|---|
| GA: Steady-state + Tournament | 2 | 34.6 | 27.5 | 22.5 | 19.1 | 3.37 | yes |
| Hill climbing (1+1)-EA | 2 | 72.2 | 55.7 | 44.7 | 33.8 | 10.9 | yes |
| Simulated annealing | 2 | 80.8 | 41.8 | 34.3 | 29.5 | 4.74 | yes |
| Random search | 2 | 89.7 | 88.4 | 73.2 | 62.3 | 10.9 | yes |

- The best GA configuration still improved by 3.37 in the last 12 evaluations, more than the noise floor: 50 is a compute limit, not a converged search. Say so in the paper, and report the budget as the cost of one run (11 s here).
- In-run errors are the best of many noisy evaluations, so they are biased low (Stats.py re-evaluates them); the shape of the curve, not its last value, is what matters here.

### Population size (run.populationSize = 10)

At a fixed evaluation budget, the population size barely changes the cost: it adds the start population's evaluations once per run. What it changes is how the budget is spent.

| Population | Start population | Share of run | Generations: Steady-state | Elitist | Generational |
|---|---|---|---|---|---|
| 4 | 0.90 s | 7.4% | 50 | 25 | 12 |
| 6 | 1.35 s | 10.7% | 50 | 12 | 8 |
| **10** | 2.24 s | 16.7% | 50 | 6 | 5 |
| 20 | 4.49 s | 28.6% | 50 | 2 | 2 |
| 30 | 6.73 s | 37.5% | 50 | 1 | 1 |
| 50 | 11 s | 50.0% | 50 | 1 | 1 |

- With 10, the start population costs 16.7% of a run (2.24 s), and Generational replacement still gets 5 generations (6 for Elitist). At 50 it would get only 1, too few to converge, and buying back 100 generations would take 18.7 min per run instead of 3.7 min.
- Smaller populations (4-6) save 10.0% of a run or less but leave little diversity for crossover. The cost does not decide between 6, 10 and 20; a small sensitivity sweep (checklist, priority 3) would.
