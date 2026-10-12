# Computing cost (BaseGame stage)

Every simulator call the optimizer made was timed (wall time as the optimizer pays it, including starting the simulator and reading its output). The optimizer stores the total time per method and run, so time per evaluation is total time / evaluations.

## Machines

| Id | CPU | Cores / logical CPUs | Threads used | Memory | OS | Compiler | Build | Python |
|---|---|---|---|---|---|---|---|---|
| 716fd7bca4 | AMD EPYC 9R14 | 64 / 64 | 10 | 123.1 GB | Linux 7.0.0-1006-aws | GCC 15.2.0 | Release | 3.14.4 |

## Time per evaluation

Every evaluation simulates 10,000,000 spins (base game only). Differences between methods come from the reelsets they propose: reelsets that trigger more free games play more spins.

| Method | Runs | Evaluations | Seconds per evaluation | Fastest run | Slowest run |
|---|---|---|---|---|---|
| Steady-state + Tournament | 120 | 120,000 | 0.150 s | 0.138 s | 0.166 s |
| Steady-state + Roulette | 120 | 120,000 | 0.151 s | 0.139 s | 0.170 s |
| Steady-state + SUS | 120 | 120,000 | 0.151 s | 0.138 s | 0.169 s |
| Elitist generational + Tournament | 120 | 120,000 | 0.152 s | 0.142 s | 0.171 s |
| Elitist generational + Roulette | 120 | 120,000 | 0.154 s | 0.141 s | 0.170 s |
| Elitist generational + SUS | 120 | 120,000 | 0.152 s | 0.136 s | 0.173 s |
| Generational + Tournament | 120 | 120,000 | 0.156 s | 0.139 s | 0.183 s |
| Generational + Roulette | 120 | 120,000 | 0.165 s | 0.145 s | 0.208 s |
| Generational + SUS | 120 | 120,000 | 0.158 s | 0.139 s | 0.177 s |
| Baseline: Hill climbing (1+1)-EA | 120 | 120,000 | 0.150 s | 0.136 s | 0.171 s |
| Baseline: Simulated annealing | 120 | 120,000 | 0.153 s | 0.139 s | 0.176 s |
| Baseline: Random search | 30 | 30,000 | 0.221 s | 0.217 s | 0.229 s |
| **All** | 1350 | 1,350,000 | **0.155 s** | 0.136 s | 0.229 s |

That is about 66.4M spins per second on 10 threads (6.64M per thread); 3 ms of each call is outside the spinning (starting the simulator, reading the reelset, writing the JSON).

> **Thread use:** 10,000,000 spins are 10 jobs of 1M, so at most 10 of the 51 threads this machine would use are busy. More cores do not make an evaluation at this spin count faster; more spins per evaluation would come almost free up to 51M.

## Time per run

One run = one method on one seed: 1000 evaluations, plus the final check of its best reelset. Overhead is the optimizer's own work (selection, files, saving results).

| Method | Runs | Wall time | Search | Final check | Overhead |
|---|---|---|---|---|---|
| Steady-state + Tournament | 120 | 2.5 min | 2.5 min | 1.34 s | 0.59 s (0.4%) |
| Steady-state + Roulette | 120 | 2.6 min | 2.5 min | 1.33 s | 0.60 s (0.4%) |
| Steady-state + SUS | 120 | 2.5 min | 2.5 min | 1.34 s | 0.61 s (0.4%) |
| Elitist generational + Tournament | 120 | 2.5 min | 2.5 min | 1.33 s | 0.55 s (0.4%) |
| Elitist generational + Roulette | 120 | 2.6 min | 2.6 min | 1.34 s | 0.55 s (0.4%) |
| Elitist generational + SUS | 120 | 2.6 min | 2.5 min | 1.33 s | 0.55 s (0.4%) |
| Generational + Tournament | 120 | 2.6 min | 2.6 min | 1.33 s | 0.54 s (0.3%) |
| Generational + Roulette | 120 | 2.8 min | 2.7 min | 1.33 s | 0.54 s (0.3%) |
| Generational + SUS | 120 | 2.7 min | 2.6 min | 1.35 s | 0.55 s (0.3%) |
| Baseline: Hill climbing (1+1)-EA | 120 | 2.5 min | 2.5 min | 1.36 s | 0.56 s (0.4%) |
| Baseline: Simulated annealing | 120 | 2.6 min | 2.5 min | 1.33 s | 0.57 s (0.4%) |
| Baseline: Random search | 30 | 3.7 min | 3.7 min | 1.85 s | 0.52 s (0.2%) |

A whole BaseGame stage of one seed (all 45 methods, initial population included) took 118.1 min (median over 30 seeds).

## Whole study (every stage in the file)

Simulation = time spent in simulator calls; CPU time = simulator time × threads it used; wall time = the stages' own clocks (includes the optimizer's work).

| Stage | Seeds | Runs | Simulator calls | Simulation | CPU time | Wall time |
|---|---|---|---|---|---|---|
| BaseGame | 30 | 1350 | 1,351,350 | 58.8 h | 578.3 h | 59.0 h |
| FreeGame | 30 | 1350 | 1,351,350 | 24.1 h | 219.7 h | 24.4 h |
| **Total** | | **2700** | **2,702,700** | **82.9 h** | **797.9 h** | **83.4 h** |

Random search is run once per seed and saved under every mutation count; the copies are not counted.

## Choosing the settings

### Spins per evaluation (run.spins = 10,000,000)

Noise: fitness SD of one evaluation is 0.034 at 10M spins (BaseGame, simulator noise study) and falls as 1/√spins. The noise floor is the smallest fitness difference two evaluations can resolve (2.77 SD, 95%). Cost: seconds per evaluation from the model in 10_compute_cost.png, measured at the run's spins.

| Spins | Seconds per evaluation | One run (1000 evaluations) | This stage's 1350 runs | Fitness SD | Noise floor |
|---|---|---|---|---|---|
| 1M | 0.15 s | 2.6 min | 57.5 h | 0.1075 | 0.2978 |
| 2M | 0.15 s | 2.6 min | 57.5 h | 0.0760 | 0.2106 |
| 5M | 0.15 s | 2.6 min | 57.5 h | 0.0481 | 0.1332 |
| **10M** | 0.15 s | 2.6 min | 57.5 h | 0.0340 | **0.0942** |
| 20M | 0.15 s | 2.6 min | 57.5 h | 0.0240 | 0.0666 |
| 40M | 0.15 s | 2.6 min | 57.5 h | 0.0170 | 0.0471 |
| 100M | 0.30 s | 5.1 min | 114.0 h | 0.0108 | 0.0298 |

- **Fewer spins** (1M): 1.0× faster, but the noise floor rises to 0.298, above the 0.072 median final error of the best GA configuration: the search could no longer tell its late improvements from noise.
- **More spins** (40M): the floor halves to 0.047, but every run takes 1.0× as long (2.6 min → 2.6 min), and these 1350 runs 57.5 h → 57.5 h. That time buys more seeds instead, which the statistical tests need more.
- At 10M the noise floor is 0.094 against a best median final error of 0.072. The final check (finalCheckSpins) then measures each best reelset precisely once.

### Evaluation budget (run.generations = 1000)

Median best-so-far error (mutation 5) at each quarter of the budget, and what the last quarter bought. Noise floor at 10M spins: 0.094. One quarter of a run costs 39 s of simulation.

| Method | Seeds | @250 | @500 | @750 | @1000 | Last-quarter gain | Above noise floor |
|---|---|---|---|---|---|---|---|
| GA: Steady-state + Tournament | 30 | 0.612 | 0.137 | 0.112 | 0.072 | 0.0397 | no |
| Hill climbing (1+1)-EA | 30 | 0.272 | 0.111 | 0.0745 | 0.072 | 0.00245 | no |
| Simulated annealing | 30 | 0.673 | 0.154 | 0.124 | 0.0649 | 0.0594 | no |
| Random search | 30 | 44.5 | 39.8 | 38.9 | 37.5 | 1.34 | yes |

- In the last 250 evaluations the best GA configuration improved by only 0.0397, below the noise floor of 0.094: extra evaluations would mostly re-measure noise. Doubling the budget would double every run (2.6 min → 5.2 min) and this stage (58.3 h → 116.5 h).
- In-run errors are the best of many noisy evaluations, so they are biased low (Stats.py re-evaluates them); the shape of the curve, not its last value, is what matters here.

### Population size (run.populationSize = 10)

At a fixed evaluation budget, the population size barely changes the cost: it adds the start population's evaluations once per run. What it changes is how the budget is spent.

| Population | Start population | Share of run | Generations: Steady-state | Elitist | Generational |
|---|---|---|---|---|---|
| 4 | 0.62 s | 0.4% | 1000 | 500 | 250 |
| 6 | 0.93 s | 0.6% | 1000 | 250 | 166 |
| **10** | 1.55 s | 1.0% | 1000 | 125 | 100 |
| 20 | 3.11 s | 2.0% | 1000 | 55 | 50 |
| 30 | 4.66 s | 2.9% | 1000 | 35 | 33 |
| 50 | 7.77 s | 4.8% | 1000 | 20 | 20 |

- With 10, the start population costs 1.0% of a run (1.55 s), and Generational replacement still gets 100 generations (125 for Elitist). At 50 it would get only 20, too few to converge, and buying back 100 generations would take 12.9 min per run instead of 2.6 min.
- Smaller populations (4-6) save 0.6% of a run or less but leave little diversity for crossover. The cost does not decide between 6, 10 and 20; a small sensitivity sweep (checklist, priority 3) would.
