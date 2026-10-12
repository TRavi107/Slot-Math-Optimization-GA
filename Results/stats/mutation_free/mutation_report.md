# Mutation-count tests (FreeGame, re-evaluated error, lower is better)

1320 runs, 30 seeds, mutation counts [1, 3, 5, 10], scores from the stored 100,000,000-spin final checks. Random search is left out (it ignores the mutation count).

Paired by seed. Friedman, then two-sided Wilcoxon signed-rank with Holm correction inside each family; alpha = 0.05. A12 = probability the better setting ends lower on a run (0.5 = no difference). Noise floor = 0.0876.

## Best mutation count per method (median error at each count)

| Method | m=1 | m=3 | m=5 | m=10 | Best | Friedman p | Kendall's W |
|---|---|---|---|---|---|---|---|
| Elitist generational + Tournament | 2.021 | 1.423 | **1.174** | 1.601 | m=5 | < 0.001 | 0.36 |
| Steady-state + SUS | 2.072 | **1.262** | 1.489 | 1.593 | m=3 | < 0.001 | 0.36 |
| Simulated annealing | 1.926 | 1.532 | **1.277** | 1.494 | m=5 | < 0.001 | 0.19 |
| Steady-state + Tournament | 2.032 | **1.303** | 1.347 | 1.797 | m=3 | < 0.001 | 0.36 |
| Steady-state + Roulette | 2.008 | **1.356** | 1.718 | 1.766 | m=3 | < 0.001 | 0.26 |
| Elitist generational + Roulette | 1.94 | **1.363** | 1.474 | 1.574 | m=3 | 0.002 | 0.17 |
| Elitist generational + SUS | 1.828 | 1.479 | **1.431** | 1.73 | m=5 | 0.050 | 0.09 |
| Hill climbing | 1.988 | 1.78 | 1.559 | **1.527** | m=10 | < 0.001 | 0.35 |
| Generational + Tournament | 2.01 | **1.706** | 1.87 | 1.99 | m=3 | 0.051 | 0.09 |
| Generational + SUS | 1.885 | **1.729** | 1.9 | 1.952 | m=3 | 0.042 | 0.09 |
| Generational + Roulette | 2.069 | **1.907** | 2.001 | 2.059 | m=3 | 0.047 | 0.09 |

Friedman p below alpha = the method's result depends on the mutation count. Kendall's W: 0.1 small, 0.3 moderate, 0.5+ strong.

## Pairwise: mutation counts within each method

## Elitist generational + Roulette

| Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|
| m=3 | m=1 | 1.363 / 1.94 | yes | 21/30 | < 0.001 * | 0.86 | large |
| m=5 | m=1 | 1.474 / 1.94 | yes | 23/30 | < 0.001 * | 0.83 | large |
| m=10 | m=1 | 1.574 / 1.94 | yes | 21/30 | 0.040 * | 0.72 | large |
| m=3 | m=5 | 1.363 / 1.474 | yes | 18/30 | 0.428 | 0.55 | negligible |
| m=3 | m=10 | 1.363 / 1.574 | yes | 22/30 | 0.040 * | 0.69 | medium |
| m=5 | m=10 | 1.474 / 1.574 | yes | 19/30 | 0.121 | 0.63 | small |

## Elitist generational + SUS

| Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|
| m=3 | m=1 | 1.479 / 1.828 | yes | 21/30 | 0.015 * | 0.74 | large |
| m=5 | m=1 | 1.431 / 1.828 | yes | 19/30 | 0.062 | 0.73 | large |
| m=10 | m=1 | 1.73 / 1.828 | yes | 18/30 | 0.856 | 0.58 | small |
| m=5 | m=3 | 1.431 / 1.479 | no | 16/30 | 0.856 | 0.51 | negligible |
| m=3 | m=10 | 1.479 / 1.73 | yes | 18/30 | 0.062 | 0.70 | medium |
| m=5 | m=10 | 1.431 / 1.73 | yes | 21/30 | 0.016 * | 0.69 | medium |

## Elitist generational + Tournament

| Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|
| m=3 | m=1 | 1.423 / 2.021 | yes | 27/30 | < 0.001 * | 0.85 | large |
| m=5 | m=1 | 1.174 / 2.021 | yes | 25/30 | < 0.001 * | 0.87 | large |
| m=10 | m=1 | 1.601 / 2.021 | yes | 26/30 | < 0.001 * | 0.79 | large |
| m=5 | m=3 | 1.174 / 1.423 | yes | 21/30 | 0.171 | 0.57 | small |
| m=3 | m=10 | 1.423 / 1.601 | yes | 19/30 | 0.065 | 0.61 | small |
| m=5 | m=10 | 1.174 / 1.601 | yes | 19/30 | 0.012 * | 0.68 | medium |

## Generational + Roulette

| Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|
| m=3 | m=1 | 1.907 / 2.069 | yes | 22/30 | 0.011 * | 0.69 | medium |
| m=5 | m=1 | 2.001 / 2.069 | no | 17/30 | 0.573 | 0.59 | small |
| m=10 | m=1 | 2.059 / 2.069 | no | 19/30 | 0.786 | 0.55 | negligible |
| m=3 | m=5 | 1.907 / 2.001 | yes | 20/30 | 0.419 | 0.61 | small |
| m=3 | m=10 | 1.907 / 2.059 | yes | 18/30 | 0.333 | 0.64 | small |
| m=5 | m=10 | 2.001 / 2.059 | no | 16/30 | 0.786 | 0.55 | negligible |

## Generational + SUS

| Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|
| m=3 | m=1 | 1.729 / 1.885 | yes | 17/30 | 0.682 | 0.62 | small |
| m=5 | m=1 | 1.9 / 1.885 | no | 16/30 | 0.786 | 0.52 | negligible |
| m=1 | m=10 | 1.885 / 1.952 | no | 19/30 | 0.786 | 0.56 | small |
| m=3 | m=5 | 1.729 / 1.9 | yes | 18/30 | 0.786 | 0.59 | small |
| m=3 | m=10 | 1.729 / 1.952 | yes | 22/30 | 0.056 | 0.70 | medium |
| m=5 | m=10 | 1.9 / 1.952 | no | 20/30 | 0.402 | 0.60 | small |

## Generational + Tournament

| Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|
| m=3 | m=1 | 1.706 / 2.01 | yes | 21/30 | 0.049 * | 0.69 | medium |
| m=5 | m=1 | 1.87 / 2.01 | yes | 21/30 | 0.117 | 0.65 | medium |
| m=10 | m=1 | 1.99 / 2.01 | no | 16/30 | 0.598 | 0.55 | negligible |
| m=3 | m=5 | 1.706 / 1.87 | yes | 19/30 | 0.552 | 0.59 | small |
| m=3 | m=10 | 1.706 / 1.99 | yes | 18/30 | 0.231 | 0.66 | medium |
| m=5 | m=10 | 1.87 / 1.99 | yes | 18/30 | 0.598 | 0.62 | small |

## Hill climbing

| Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|
| m=3 | m=1 | 1.78 / 1.988 | yes | 22/30 | 0.020 * | 0.70 | medium |
| m=5 | m=1 | 1.559 / 1.988 | yes | 27/30 | < 0.001 * | 0.86 | large |
| m=10 | m=1 | 1.527 / 1.988 | yes | 27/30 | < 0.001 * | 0.83 | large |
| m=5 | m=3 | 1.559 / 1.78 | yes | 21/30 | 0.015 * | 0.75 | large |
| m=10 | m=3 | 1.527 / 1.78 | yes | 19/30 | 0.020 * | 0.69 | medium |
| m=5 | m=10 | 1.559 / 1.527 | no | 17/30 | 0.543 | 0.53 | negligible |

## Simulated annealing

| Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|
| m=3 | m=1 | 1.532 / 1.926 | yes | 20/30 | 0.010 * | 0.74 | large |
| m=5 | m=1 | 1.277 / 1.926 | yes | 24/30 | < 0.001 * | 0.79 | large |
| m=10 | m=1 | 1.494 / 1.926 | yes | 23/30 | 0.002 * | 0.76 | large |
| m=5 | m=3 | 1.277 / 1.532 | yes | 21/30 | 0.241 | 0.59 | small |
| m=10 | m=3 | 1.494 / 1.532 | no | 16/30 | 0.641 | 0.52 | negligible |
| m=5 | m=10 | 1.277 / 1.494 | yes | 19/30 | 0.579 | 0.58 | small |

## Steady-state + Roulette

| Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|
| m=3 | m=1 | 1.356 / 2.008 | yes | 27/30 | < 0.001 * | 0.85 | large |
| m=5 | m=1 | 1.718 / 2.008 | yes | 23/30 | < 0.001 * | 0.72 | large |
| m=10 | m=1 | 1.766 / 2.008 | yes | 22/30 | 0.011 * | 0.68 | medium |
| m=3 | m=5 | 1.356 / 1.718 | yes | 17/30 | 0.368 | 0.66 | medium |
| m=3 | m=10 | 1.356 / 1.766 | yes | 21/30 | 0.010 * | 0.75 | large |
| m=5 | m=10 | 1.718 / 1.766 | no | 16/30 | 0.368 | 0.56 | small |

## Steady-state + SUS

| Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|
| m=3 | m=1 | 1.262 / 2.072 | yes | 28/30 | < 0.001 * | 0.93 | large |
| m=5 | m=1 | 1.489 / 2.072 | yes | 24/30 | < 0.001 * | 0.86 | large |
| m=10 | m=1 | 1.593 / 2.072 | yes | 23/30 | < 0.001 * | 0.80 | large |
| m=3 | m=5 | 1.262 / 1.489 | yes | 18/30 | 0.201 | 0.63 | small |
| m=3 | m=10 | 1.262 / 1.593 | yes | 23/30 | 0.003 * | 0.74 | large |
| m=5 | m=10 | 1.489 / 1.593 | yes | 20/30 | 0.201 | 0.61 | small |

## Steady-state + Tournament

| Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|
| m=3 | m=1 | 1.303 / 2.032 | yes | 27/30 | < 0.001 * | 0.89 | large |
| m=5 | m=1 | 1.347 / 2.032 | yes | 26/30 | < 0.001 * | 0.85 | large |
| m=10 | m=1 | 1.797 / 2.032 | yes | 22/30 | < 0.001 * | 0.76 | large |
| m=3 | m=5 | 1.303 / 1.347 | no | 16/30 | 0.490 | 0.55 | negligible |
| m=3 | m=10 | 1.303 / 1.797 | yes | 23/30 | 0.009 * | 0.72 | large |
| m=5 | m=10 | 1.347 / 1.797 | yes | 20/30 | 0.069 | 0.66 | medium |

## Each method at its best mutation count: GA vs baselines

| Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|
| Elitist generational + Roulette (m=3) | Hill climbing (m=10) | 1.363 / 1.527 | yes | 17/30 | 1.000 | 0.54 | negligible |
| Simulated annealing (m=5) | Elitist generational + Roulette (m=3) | 1.277 / 1.363 | no | 16/30 | 1.000 | 0.55 | negligible |
| Elitist generational + SUS (m=5) | Hill climbing (m=10) | 1.431 / 1.527 | yes | 15/30 | 1.000 | 0.53 | negligible |
| Simulated annealing (m=5) | Elitist generational + SUS (m=5) | 1.277 / 1.431 | yes | 17/30 | 1.000 | 0.55 | negligible |
| Elitist generational + Tournament (m=5) | Hill climbing (m=10) | 1.174 / 1.527 | yes | 20/30 | 1.000 | 0.62 | small |
| Elitist generational + Tournament (m=5) | Simulated annealing (m=5) | 1.174 / 1.277 | yes | 19/30 | 1.000 | 0.54 | negligible |
| Hill climbing (m=10) | Generational + Roulette (m=3) | 1.527 / 1.907 | yes | 23/30 | 0.001 * | 0.79 | large |
| Simulated annealing (m=5) | Generational + Roulette (m=3) | 1.277 / 1.907 | yes | 26/30 | < 0.001 * | 0.84 | large |
| Hill climbing (m=10) | Generational + SUS (m=3) | 1.527 / 1.729 | yes | 18/30 | 0.292 | 0.68 | medium |
| Simulated annealing (m=5) | Generational + SUS (m=3) | 1.277 / 1.729 | yes | 25/30 | 0.001 * | 0.75 | large |
| Hill climbing (m=10) | Generational + Tournament (m=3) | 1.527 / 1.706 | yes | 18/30 | 0.964 | 0.64 | medium |
| Simulated annealing (m=5) | Generational + Tournament (m=3) | 1.277 / 1.706 | yes | 20/30 | 0.232 | 0.70 | medium |
| Steady-state + Roulette (m=3) | Hill climbing (m=10) | 1.356 / 1.527 | yes | 17/30 | 1.000 | 0.57 | small |
| Steady-state + SUS (m=3) | Hill climbing (m=10) | 1.262 / 1.527 | yes | 18/30 | 1.000 | 0.62 | small |
| Steady-state + Tournament (m=3) | Hill climbing (m=10) | 1.303 / 1.527 | yes | 18/30 | 0.909 | 0.62 | small |
| Simulated annealing (m=5) | Steady-state + Roulette (m=3) | 1.277 / 1.356 | no | 13/30 | 1.000 | 0.52 | negligible |
| Steady-state + SUS (m=3) | Simulated annealing (m=5) | 1.262 / 1.277 | no | 15/30 | 1.000 | 0.52 | negligible |
| Steady-state + Tournament (m=3) | Simulated annealing (m=5) | 1.303 / 1.277 | no | 14/30 | 1.000 | 0.53 | negligible |

Each method's best count was chosen on the same seeds it is tested on (slightly optimistic for every method).

## Claims you can make

Significant after Holm, A12 at least small, and median gap above the noise floor.

- Elitist generational + Roulette: m=3 reached a lower re-evaluated error than m=1 (median 1.363 vs 1.94; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.86, large).
- Elitist generational + Roulette: m=5 reached a lower re-evaluated error than m=1 (median 1.474 vs 1.94; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.83, large).
- Elitist generational + Roulette: m=10 reached a lower re-evaluated error than m=1 (median 1.574 vs 1.94; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.040; A12 = 0.72, large).
- Elitist generational + Roulette: m=3 reached a lower re-evaluated error than m=10 (median 1.363 vs 1.574; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.040; A12 = 0.69, medium).
- Elitist generational + SUS: m=3 reached a lower re-evaluated error than m=1 (median 1.479 vs 1.828; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.015; A12 = 0.74, large).
- Elitist generational + SUS: m=5 reached a lower re-evaluated error than m=10 (median 1.431 vs 1.73; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.016; A12 = 0.69, medium).
- Elitist generational + Tournament: m=3 reached a lower re-evaluated error than m=1 (median 1.423 vs 2.021; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.85, large).
- Elitist generational + Tournament: m=5 reached a lower re-evaluated error than m=1 (median 1.174 vs 2.021; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.87, large).
- Elitist generational + Tournament: m=10 reached a lower re-evaluated error than m=1 (median 1.601 vs 2.021; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.79, large).
- Elitist generational + Tournament: m=5 reached a lower re-evaluated error than m=10 (median 1.174 vs 1.601; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.012; A12 = 0.68, medium).
- Generational + Roulette: m=3 reached a lower re-evaluated error than m=1 (median 1.907 vs 2.069; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.011; A12 = 0.69, medium).
- Generational + Tournament: m=3 reached a lower re-evaluated error than m=1 (median 1.706 vs 2.01; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.049; A12 = 0.69, medium).
- Hill climbing: m=3 reached a lower re-evaluated error than m=1 (median 1.78 vs 1.988; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.020; A12 = 0.70, medium).
- Hill climbing: m=5 reached a lower re-evaluated error than m=1 (median 1.559 vs 1.988; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.86, large).
- Hill climbing: m=10 reached a lower re-evaluated error than m=1 (median 1.527 vs 1.988; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.83, large).
- Hill climbing: m=5 reached a lower re-evaluated error than m=3 (median 1.559 vs 1.78; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.015; A12 = 0.75, large).
- Hill climbing: m=10 reached a lower re-evaluated error than m=3 (median 1.527 vs 1.78; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.020; A12 = 0.69, medium).
- Simulated annealing: m=3 reached a lower re-evaluated error than m=1 (median 1.532 vs 1.926; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.010; A12 = 0.74, large).
- Simulated annealing: m=5 reached a lower re-evaluated error than m=1 (median 1.277 vs 1.926; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.79, large).
- Simulated annealing: m=10 reached a lower re-evaluated error than m=1 (median 1.494 vs 1.926; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.002; A12 = 0.76, large).
- Steady-state + Roulette: m=3 reached a lower re-evaluated error than m=1 (median 1.356 vs 2.008; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.85, large).
- Steady-state + Roulette: m=5 reached a lower re-evaluated error than m=1 (median 1.718 vs 2.008; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.72, large).
- Steady-state + Roulette: m=10 reached a lower re-evaluated error than m=1 (median 1.766 vs 2.008; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.011; A12 = 0.68, medium).
- Steady-state + Roulette: m=3 reached a lower re-evaluated error than m=10 (median 1.356 vs 1.766; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.010; A12 = 0.75, large).
- Steady-state + SUS: m=3 reached a lower re-evaluated error than m=1 (median 1.262 vs 2.072; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.93, large).
- Steady-state + SUS: m=5 reached a lower re-evaluated error than m=1 (median 1.489 vs 2.072; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.86, large).
- Steady-state + SUS: m=10 reached a lower re-evaluated error than m=1 (median 1.593 vs 2.072; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.80, large).
- Steady-state + SUS: m=3 reached a lower re-evaluated error than m=10 (median 1.262 vs 1.593; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.003; A12 = 0.74, large).
- Steady-state + Tournament: m=3 reached a lower re-evaluated error than m=1 (median 1.303 vs 2.032; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.89, large).
- Steady-state + Tournament: m=5 reached a lower re-evaluated error than m=1 (median 1.347 vs 2.032; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.85, large).
- Steady-state + Tournament: m=10 reached a lower re-evaluated error than m=1 (median 1.797 vs 2.032; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.76, large).
- Steady-state + Tournament: m=3 reached a lower re-evaluated error than m=10 (median 1.303 vs 1.797; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.009; A12 = 0.72, large).
- At each method's best mutation count: Hill climbing (m=10) reached a lower re-evaluated error than Generational + Roulette (m=3) (median 1.527 vs 1.907; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.001; A12 = 0.79, large).
- At each method's best mutation count: Simulated annealing (m=5) reached a lower re-evaluated error than Generational + Roulette (m=3) (median 1.277 vs 1.907; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.84, large).
- At each method's best mutation count: Simulated annealing (m=5) reached a lower re-evaluated error than Generational + SUS (m=3) (median 1.277 vs 1.729; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.001; A12 = 0.75, large).
