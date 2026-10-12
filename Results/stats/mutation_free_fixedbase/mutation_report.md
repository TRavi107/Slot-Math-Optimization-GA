# Mutation-count tests (FreeGame, re-evaluated error, lower is better)

990 runs, 30 seeds, mutation counts [3, 5, 10], scores from the stored 100,000,000-spin final checks. Random search is left out (it ignores the mutation count).

Paired by seed. Friedman, then two-sided Wilcoxon signed-rank with Holm correction inside each family; alpha = 0.05. A12 = probability the better setting ends lower on a run (0.5 = no difference). Noise floor = 0.0876.

## Best mutation count per method (median error at each count)

| Method | m=3 | m=5 | m=10 | Best | Friedman p | Kendall's W |
|---|---|---|---|---|---|---|
| Steady-state + SUS | **1.277** | 1.44 | 1.562 | m=3 | 0.048 | 0.10 |
| Steady-state + Tournament | **1.301** | 1.639 | 1.637 | m=3 | 0.150 | 0.06 |
| Simulated annealing | 1.571 | 1.419 | **1.354** | m=10 | 0.875 | 0.00 |
| Elitist generational + SUS | 1.381 | **1.354** | 1.697 | m=5 | 0.039 | 0.11 |
| Elitist generational + Tournament | 1.456 | **1.365** | 1.438 | m=5 | 0.648 | 0.01 |
| Elitist generational + Roulette | **1.494** | 1.6 | 1.544 | m=3 | 0.301 | 0.04 |
| Hill climbing | 1.75 | **1.539** | 1.716 | m=5 | 0.195 | 0.05 |
| Steady-state + Roulette | **1.553** | 1.576 | 1.729 | m=3 | 0.082 | 0.08 |
| Generational + Tournament | **1.68** | 1.695 | 1.847 | m=3 | 0.107 | 0.07 |
| Generational + SUS | **1.789** | 1.902 | 2.109 | m=3 | 0.001 | 0.22 |
| Generational + Roulette | **1.924** | 2.009 | 2.08 | m=3 | 0.118 | 0.07 |

Friedman p below alpha = the method's result depends on the mutation count. Kendall's W: 0.1 small, 0.3 moderate, 0.5+ strong.

## Pairwise: mutation counts within each method

## Elitist generational + Roulette

| Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|
| m=3 | m=5 | 1.494 / 1.6 | yes | 20/30 | 0.396 | 0.59 | small |
| m=3 | m=10 | 1.494 / 1.544 | no | 16/30 | 0.343 | 0.60 | small |
| m=10 | m=5 | 1.544 / 1.6 | no | 16/30 | 0.670 | 0.51 | negligible |

## Elitist generational + SUS

| Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|
| m=3 | m=5 | 1.381 / 1.354 | no | 17/30 | 0.612 | 0.54 | negligible |
| m=3 | m=10 | 1.381 / 1.697 | yes | 21/30 | 0.006 * | 0.73 | large |
| m=5 | m=10 | 1.354 / 1.697 | yes | 20/30 | 0.017 * | 0.72 | large |

## Elitist generational + Tournament

| Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|
| m=5 | m=3 | 1.365 / 1.456 | yes | 16/30 | 0.952 | 0.50 | negligible |
| m=3 | m=10 | 1.456 / 1.438 | no | 17/30 | 0.532 | 0.58 | small |
| m=5 | m=10 | 1.365 / 1.438 | no | 17/30 | 0.532 | 0.59 | small |

## Generational + Roulette

| Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|
| m=3 | m=5 | 1.924 / 2.009 | no | 18/30 | 0.839 | 0.54 | negligible |
| m=3 | m=10 | 1.924 / 2.08 | yes | 20/30 | 0.128 | 0.64 | medium |
| m=5 | m=10 | 2.009 / 2.08 | no | 18/30 | 0.368 | 0.59 | small |

## Generational + SUS

| Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|
| m=3 | m=5 | 1.789 / 1.902 | yes | 20/30 | 0.084 | 0.61 | small |
| m=3 | m=10 | 1.789 / 2.109 | yes | 23/30 | < 0.001 * | 0.78 | large |
| m=5 | m=10 | 1.902 / 2.109 | yes | 22/30 | 0.023 * | 0.69 | medium |

## Generational + Tournament

| Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|
| m=3 | m=5 | 1.68 / 1.695 | no | 17/30 | 0.670 | 0.52 | negligible |
| m=3 | m=10 | 1.68 / 1.847 | yes | 20/30 | 0.049 * | 0.66 | medium |
| m=5 | m=10 | 1.695 / 1.847 | yes | 19/30 | 0.099 | 0.64 | medium |

## Hill climbing

| Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|
| m=5 | m=3 | 1.539 / 1.75 | yes | 19/30 | 0.288 | 0.65 | medium |
| m=10 | m=3 | 1.716 / 1.75 | no | 18/30 | 0.288 | 0.55 | negligible |
| m=5 | m=10 | 1.539 / 1.716 | yes | 18/30 | 0.288 | 0.59 | small |

## Simulated annealing

| Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|
| m=5 | m=3 | 1.419 / 1.571 | yes | 16/30 | 1.000 | 0.52 | negligible |
| m=3 | m=10 | 1.571 / 1.354 | no | 16/30 | 1.000 | 0.51 | negligible |
| m=5 | m=10 | 1.419 / 1.354 | no | 16/30 | 1.000 | 0.54 | negligible |

## Steady-state + Roulette

| Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|
| m=3 | m=5 | 1.553 / 1.576 | no | 14/30 | 0.700 | 0.53 | negligible |
| m=3 | m=10 | 1.553 / 1.729 | yes | 21/30 | 0.230 | 0.64 | small |
| m=5 | m=10 | 1.576 / 1.729 | yes | 19/30 | 0.598 | 0.60 | small |

## Steady-state + SUS

| Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|
| m=3 | m=5 | 1.277 / 1.44 | yes | 18/30 | 0.341 | 0.59 | small |
| m=3 | m=10 | 1.277 / 1.562 | yes | 21/30 | 0.026 * | 0.69 | medium |
| m=5 | m=10 | 1.44 / 1.562 | yes | 19/30 | 0.341 | 0.59 | small |

## Steady-state + Tournament

| Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|
| m=3 | m=5 | 1.301 / 1.639 | yes | 18/30 | 0.490 | 0.54 | negligible |
| m=3 | m=10 | 1.301 / 1.637 | yes | 19/30 | 0.104 | 0.66 | medium |
| m=5 | m=10 | 1.639 / 1.637 | no | 19/30 | 0.238 | 0.60 | small |

## Each method at its best mutation count: GA vs baselines

| Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|
| Elitist generational + Roulette (m=3) | Hill climbing (m=5) | 1.494 / 1.539 | no | 15/30 | 1.000 | 0.53 | negligible |
| Elitist generational + Roulette (m=3) | Simulated annealing (m=10) | 1.494 / 1.354 | no | 16/30 | 1.000 | 0.50 | negligible |
| Elitist generational + SUS (m=5) | Hill climbing (m=5) | 1.354 / 1.539 | yes | 18/30 | 1.000 | 0.57 | small |
| Elitist generational + SUS (m=5) | Simulated annealing (m=10) | 1.354 / 1.354 | no | 14/30 | 1.000 | 0.54 | negligible |
| Elitist generational + Tournament (m=5) | Hill climbing (m=5) | 1.365 / 1.539 | yes | 19/30 | 1.000 | 0.56 | negligible |
| Elitist generational + Tournament (m=5) | Simulated annealing (m=10) | 1.365 / 1.354 | no | 16/30 | 1.000 | 0.53 | negligible |
| Hill climbing (m=5) | Generational + Roulette (m=3) | 1.539 / 1.924 | yes | 25/30 | < 0.001 * | 0.83 | large |
| Simulated annealing (m=10) | Generational + Roulette (m=3) | 1.354 / 1.924 | yes | 26/30 | < 0.001 * | 0.84 | large |
| Hill climbing (m=5) | Generational + SUS (m=3) | 1.539 / 1.789 | yes | 22/30 | 0.003 * | 0.73 | large |
| Simulated annealing (m=10) | Generational + SUS (m=3) | 1.354 / 1.789 | yes | 24/30 | 0.005 * | 0.78 | large |
| Hill climbing (m=5) | Generational + Tournament (m=3) | 1.539 / 1.68 | yes | 18/30 | 1.000 | 0.61 | small |
| Simulated annealing (m=10) | Generational + Tournament (m=3) | 1.354 / 1.68 | yes | 19/30 | 1.000 | 0.65 | medium |
| Steady-state + Roulette (m=3) | Hill climbing (m=5) | 1.553 / 1.539 | no | 16/30 | 1.000 | 0.50 | negligible |
| Steady-state + SUS (m=3) | Hill climbing (m=5) | 1.277 / 1.539 | yes | 20/30 | 1.000 | 0.61 | small |
| Steady-state + Tournament (m=3) | Hill climbing (m=5) | 1.301 / 1.539 | yes | 19/30 | 1.000 | 0.58 | small |
| Simulated annealing (m=10) | Steady-state + Roulette (m=3) | 1.354 / 1.553 | yes | 16/30 | 1.000 | 0.53 | negligible |
| Steady-state + SUS (m=3) | Simulated annealing (m=10) | 1.277 / 1.354 | no | 20/30 | 1.000 | 0.59 | small |
| Steady-state + Tournament (m=3) | Simulated annealing (m=10) | 1.301 / 1.354 | no | 16/30 | 1.000 | 0.56 | small |

Each method's best count was chosen on the same seeds it is tested on (slightly optimistic for every method).

## Claims you can make

Significant after Holm, A12 at least small, and median gap above the noise floor.

- Elitist generational + SUS: m=3 reached a lower re-evaluated error than m=10 (median 1.381 vs 1.697; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.006; A12 = 0.73, large).
- Elitist generational + SUS: m=5 reached a lower re-evaluated error than m=10 (median 1.354 vs 1.697; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.017; A12 = 0.72, large).
- Generational + SUS: m=3 reached a lower re-evaluated error than m=10 (median 1.789 vs 2.109; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.78, large).
- Generational + SUS: m=5 reached a lower re-evaluated error than m=10 (median 1.902 vs 2.109; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.023; A12 = 0.69, medium).
- Generational + Tournament: m=3 reached a lower re-evaluated error than m=10 (median 1.68 vs 1.847; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.049; A12 = 0.66, medium).
- Steady-state + SUS: m=3 reached a lower re-evaluated error than m=10 (median 1.277 vs 1.562; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.026; A12 = 0.69, medium).
- At each method's best mutation count: Hill climbing (m=5) reached a lower re-evaluated error than Generational + Roulette (m=3) (median 1.539 vs 1.924; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.83, large).
- At each method's best mutation count: Simulated annealing (m=10) reached a lower re-evaluated error than Generational + Roulette (m=3) (median 1.354 vs 1.924; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.84, large).
- At each method's best mutation count: Hill climbing (m=5) reached a lower re-evaluated error than Generational + SUS (m=3) (median 1.539 vs 1.789; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.003; A12 = 0.73, large).
- At each method's best mutation count: Simulated annealing (m=10) reached a lower re-evaluated error than Generational + SUS (m=3) (median 1.354 vs 1.789; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.005; A12 = 0.78, large).
