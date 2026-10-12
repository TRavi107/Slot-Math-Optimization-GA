# Mutation-count tests (BaseGame, re-evaluated error, lower is better)

1320 runs, 30 seeds, mutation counts [1, 3, 5, 10], scores from the stored 100,000,000-spin final checks. Random search is left out (it ignores the mutation count).

Paired by seed. Friedman, then two-sided Wilcoxon signed-rank with Holm correction inside each family; alpha = 0.05. A12 = probability the better setting ends lower on a run (0.5 = no difference). Noise floor = 0.02978.

## Best mutation count per method (median error at each count)

| Method | m=1 | m=3 | m=5 | m=10 | Best | Friedman p | Kendall's W |
|---|---|---|---|---|---|---|---|
| Simulated annealing | 0.1922 | 0.1302 | **0.07481** | 0.1551 | m=5 | 0.015 | 0.12 |
| Steady-state + Tournament | **0.07578** | 0.1144 | 0.08964 | 0.139 | m=1 | 0.106 | 0.07 |
| Hill climbing | 0.1598 | 0.1185 | **0.08424** | 0.1284 | m=5 | 0.152 | 0.06 |
| Elitist generational + Roulette | 0.1548 | **0.08569** | 0.1323 | 0.2688 | m=3 | < 0.001 | 0.37 |
| Steady-state + SUS | 0.1404 | 0.1527 | **0.09062** | 0.1691 | m=5 | 0.027 | 0.10 |
| Elitist generational + Tournament | 0.1765 | 0.1191 | **0.1** | 0.2098 | m=5 | 0.024 | 0.10 |
| Elitist generational + SUS | **0.1351** | 0.151 | 0.1476 | 0.2215 | m=1 | < 0.001 | 0.19 |
| Steady-state + Roulette | 0.1628 | **0.1372** | 0.1502 | 0.2061 | m=3 | 0.069 | 0.08 |
| Generational + Tournament | 0.169 | **0.158** | 0.2092 | 0.522 | m=3 | < 0.001 | 0.53 |
| Generational + SUS | **0.1732** | 0.2345 | 0.3331 | 0.83 | m=1 | < 0.001 | 0.61 |
| Generational + Roulette | **0.2515** | 0.349 | 0.4445 | 1.555 | m=1 | < 0.001 | 0.49 |

Friedman p below alpha = the method's result depends on the mutation count. Kendall's W: 0.1 small, 0.3 moderate, 0.5+ strong.

## Pairwise: mutation counts within each method

## Elitist generational + Roulette

| Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|
| m=3 | m=1 | 0.08569 / 0.1548 | yes | 20/30 | 0.456 | 0.58 | small |
| m=5 | m=1 | 0.1323 / 0.1548 | no | 17/30 | 0.792 | 0.51 | negligible |
| m=1 | m=10 | 0.1548 / 0.2688 | yes | 24/30 | < 0.001 * | 0.82 | large |
| m=3 | m=5 | 0.08569 / 0.1323 | yes | 18/30 | 0.579 | 0.60 | small |
| m=3 | m=10 | 0.08569 / 0.2688 | yes | 29/30 | < 0.001 * | 0.89 | large |
| m=5 | m=10 | 0.1323 / 0.2688 | yes | 25/30 | < 0.001 * | 0.88 | large |

## Elitist generational + SUS

| Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|
| m=1 | m=3 | 0.1351 / 0.151 | no | 16/30 | 1.000 | 0.57 | small |
| m=1 | m=5 | 0.1351 / 0.1476 | no | 17/30 | 1.000 | 0.54 | negligible |
| m=1 | m=10 | 0.1351 / 0.2215 | yes | 25/30 | < 0.001 * | 0.74 | large |
| m=5 | m=3 | 0.1476 / 0.151 | no | 16/30 | 1.000 | 0.53 | negligible |
| m=3 | m=10 | 0.151 / 0.2215 | yes | 22/30 | 0.020 * | 0.74 | large |
| m=5 | m=10 | 0.1476 / 0.2215 | yes | 23/30 | 0.020 * | 0.74 | large |

## Elitist generational + Tournament

| Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|
| m=3 | m=1 | 0.1191 / 0.1765 | yes | 17/30 | 0.307 | 0.61 | small |
| m=5 | m=1 | 0.1 / 0.1765 | yes | 17/30 | 0.411 | 0.58 | small |
| m=1 | m=10 | 0.1765 / 0.2098 | yes | 18/30 | 0.343 | 0.63 | small |
| m=3 | m=5 | 0.1191 / 0.1 | no | 15/30 | 0.543 | 0.54 | negligible |
| m=3 | m=10 | 0.1191 / 0.2098 | yes | 25/30 | 0.002 * | 0.75 | large |
| m=5 | m=10 | 0.1 / 0.2098 | yes | 19/30 | 0.087 | 0.72 | large |

## Generational + Roulette

| Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|
| m=1 | m=3 | 0.2515 / 0.349 | yes | 19/30 | 0.746 | 0.53 | negligible |
| m=1 | m=5 | 0.2515 / 0.4445 | yes | 20/30 | 0.037 * | 0.72 | large |
| m=1 | m=10 | 0.2515 / 1.555 | yes | 29/30 | < 0.001 * | 0.94 | large |
| m=3 | m=5 | 0.349 / 0.4445 | yes | 21/30 | 0.016 * | 0.71 | medium |
| m=3 | m=10 | 0.349 / 1.555 | yes | 28/30 | < 0.001 * | 0.95 | large |
| m=5 | m=10 | 0.4445 / 1.555 | yes | 26/30 | < 0.001 * | 0.86 | large |

## Generational + SUS

| Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|
| m=1 | m=3 | 0.1732 / 0.2345 | yes | 21/30 | 0.006 * | 0.71 | medium |
| m=1 | m=5 | 0.1732 / 0.3331 | yes | 25/30 | < 0.001 * | 0.81 | large |
| m=1 | m=10 | 0.1732 / 0.83 | yes | 29/30 | < 0.001 * | 0.99 | large |
| m=3 | m=5 | 0.2345 / 0.3331 | yes | 19/30 | 0.084 | 0.66 | medium |
| m=3 | m=10 | 0.2345 / 0.83 | yes | 30/30 | < 0.001 * | 0.96 | large |
| m=5 | m=10 | 0.3331 / 0.83 | yes | 27/30 | < 0.001 * | 0.93 | large |

## Generational + Tournament

| Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|
| m=3 | m=1 | 0.158 / 0.169 | no | 14/30 | 0.984 | 0.54 | negligible |
| m=1 | m=5 | 0.169 / 0.2092 | yes | 21/30 | 0.115 | 0.62 | small |
| m=1 | m=10 | 0.169 / 0.522 | yes | 29/30 | < 0.001 * | 0.94 | large |
| m=3 | m=5 | 0.158 / 0.2092 | yes | 19/30 | 0.088 | 0.67 | medium |
| m=3 | m=10 | 0.158 / 0.522 | yes | 28/30 | < 0.001 * | 0.96 | large |
| m=5 | m=10 | 0.2092 / 0.522 | yes | 29/30 | < 0.001 * | 0.90 | large |

## Hill climbing

| Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|
| m=3 | m=1 | 0.1185 / 0.1598 | yes | 19/30 | 0.621 | 0.64 | medium |
| m=5 | m=1 | 0.08424 / 0.1598 | yes | 20/30 | 0.099 | 0.62 | small |
| m=10 | m=1 | 0.1284 / 0.1598 | yes | 16/30 | 0.621 | 0.57 | small |
| m=3 | m=5 | 0.1185 / 0.08424 | no | 17/30 | 1.000 | 0.51 | negligible |
| m=3 | m=10 | 0.1185 / 0.1284 | no | 17/30 | 1.000 | 0.57 | small |
| m=5 | m=10 | 0.08424 / 0.1284 | yes | 20/30 | 0.662 | 0.60 | small |

## Simulated annealing

| Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|
| m=3 | m=1 | 0.1302 / 0.1922 | yes | 19/30 | 0.032 * | 0.69 | medium |
| m=5 | m=1 | 0.07481 / 0.1922 | yes | 22/30 | 0.032 * | 0.72 | large |
| m=10 | m=1 | 0.1551 / 0.1922 | yes | 19/30 | 0.473 | 0.59 | small |
| m=5 | m=3 | 0.07481 / 0.1302 | yes | 16/30 | 0.473 | 0.56 | small |
| m=3 | m=10 | 0.1302 / 0.1551 | no | 21/30 | 0.372 | 0.65 | medium |
| m=5 | m=10 | 0.07481 / 0.1551 | yes | 20/30 | 0.032 * | 0.69 | medium |

## Steady-state + Roulette

| Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|
| m=3 | m=1 | 0.1372 / 0.1628 | no | 16/30 | 0.980 | 0.54 | negligible |
| m=5 | m=1 | 0.1502 / 0.1628 | no | 18/30 | 0.980 | 0.56 | small |
| m=1 | m=10 | 0.1628 / 0.2061 | yes | 15/30 | 1.000 | 0.57 | small |
| m=5 | m=3 | 0.1502 / 0.1372 | no | 17/30 | 1.000 | 0.51 | negligible |
| m=3 | m=10 | 0.1372 / 0.2061 | yes | 21/30 | 0.202 | 0.67 | medium |
| m=5 | m=10 | 0.1502 / 0.2061 | yes | 22/30 | 0.010 * | 0.73 | large |

## Steady-state + SUS

| Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|
| m=1 | m=3 | 0.1404 / 0.1527 | no | 16/30 | 1.000 | 0.52 | negligible |
| m=5 | m=1 | 0.09062 / 0.1404 | yes | 18/30 | 0.328 | 0.59 | small |
| m=1 | m=10 | 0.1404 / 0.1691 | no | 19/30 | 0.280 | 0.63 | small |
| m=5 | m=3 | 0.09062 / 0.1527 | yes | 20/30 | 0.328 | 0.64 | medium |
| m=3 | m=10 | 0.1527 / 0.1691 | no | 19/30 | 0.098 | 0.64 | medium |
| m=5 | m=10 | 0.09062 / 0.1691 | yes | 22/30 | 0.011 * | 0.77 | large |

## Steady-state + Tournament

| Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|
| m=1 | m=3 | 0.07578 / 0.1144 | yes | 15/30 | 1.000 | 0.51 | negligible |
| m=1 | m=5 | 0.07578 / 0.08964 | no | 14/30 | 1.000 | 0.50 | negligible |
| m=1 | m=10 | 0.07578 / 0.139 | yes | 20/30 | 0.657 | 0.63 | small |
| m=5 | m=3 | 0.08964 / 0.1144 | no | 15/30 | 1.000 | 0.52 | negligible |
| m=3 | m=10 | 0.1144 / 0.139 | no | 19/30 | 0.288 | 0.63 | small |
| m=5 | m=10 | 0.08964 / 0.139 | yes | 21/30 | 0.176 | 0.65 | medium |

## Each method at its best mutation count: GA vs baselines

| Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|
| Elitist generational + Roulette (m=3) | Hill climbing (m=5) | 0.08569 / 0.08424 | no | 15/30 | 1.000 | 0.52 | negligible |
| Simulated annealing (m=5) | Elitist generational + Roulette (m=3) | 0.07481 / 0.08569 | no | 18/30 | 1.000 | 0.50 | negligible |
| Hill climbing (m=5) | Elitist generational + SUS (m=1) | 0.08424 / 0.1351 | yes | 16/30 | 1.000 | 0.57 | small |
| Simulated annealing (m=5) | Elitist generational + SUS (m=1) | 0.07481 / 0.1351 | yes | 19/30 | 1.000 | 0.60 | small |
| Hill climbing (m=5) | Elitist generational + Tournament (m=5) | 0.08424 / 0.1 | no | 18/30 | 1.000 | 0.59 | small |
| Simulated annealing (m=5) | Elitist generational + Tournament (m=5) | 0.07481 / 0.1 | no | 19/30 | 1.000 | 0.61 | small |
| Hill climbing (m=5) | Generational + Roulette (m=1) | 0.08424 / 0.2515 | yes | 25/30 | < 0.001 * | 0.85 | large |
| Simulated annealing (m=5) | Generational + Roulette (m=1) | 0.07481 / 0.2515 | yes | 26/30 | < 0.001 * | 0.86 | large |
| Hill climbing (m=5) | Generational + SUS (m=1) | 0.08424 / 0.1732 | yes | 21/30 | 0.065 | 0.75 | large |
| Simulated annealing (m=5) | Generational + SUS (m=1) | 0.07481 / 0.1732 | yes | 22/30 | 0.009 * | 0.75 | large |
| Hill climbing (m=5) | Generational + Tournament (m=3) | 0.08424 / 0.158 | yes | 23/30 | 0.100 | 0.70 | medium |
| Simulated annealing (m=5) | Generational + Tournament (m=3) | 0.07481 / 0.158 | yes | 22/30 | 0.106 | 0.71 | large |
| Hill climbing (m=5) | Steady-state + Roulette (m=3) | 0.08424 / 0.1372 | yes | 17/30 | 1.000 | 0.61 | small |
| Steady-state + SUS (m=5) | Hill climbing (m=5) | 0.09062 / 0.08424 | no | 16/30 | 1.000 | 0.52 | negligible |
| Hill climbing (m=5) | Steady-state + Tournament (m=1) | 0.08424 / 0.07578 | no | 12/30 | 1.000 | 0.50 | negligible |
| Simulated annealing (m=5) | Steady-state + Roulette (m=3) | 0.07481 / 0.1372 | yes | 20/30 | 1.000 | 0.63 | small |
| Simulated annealing (m=5) | Steady-state + SUS (m=5) | 0.07481 / 0.09062 | no | 15/30 | 1.000 | 0.51 | negligible |
| Simulated annealing (m=5) | Steady-state + Tournament (m=1) | 0.07481 / 0.07578 | no | 15/30 | 1.000 | 0.53 | negligible |

Each method's best count was chosen on the same seeds it is tested on (slightly optimistic for every method).

## Claims you can make

Significant after Holm, A12 at least small, and median gap above the noise floor.

- Elitist generational + Roulette: m=1 reached a lower re-evaluated error than m=10 (median 0.1548 vs 0.2688; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.82, large).
- Elitist generational + Roulette: m=3 reached a lower re-evaluated error than m=10 (median 0.08569 vs 0.2688; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.89, large).
- Elitist generational + Roulette: m=5 reached a lower re-evaluated error than m=10 (median 0.1323 vs 0.2688; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.88, large).
- Elitist generational + SUS: m=1 reached a lower re-evaluated error than m=10 (median 0.1351 vs 0.2215; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.74, large).
- Elitist generational + SUS: m=3 reached a lower re-evaluated error than m=10 (median 0.151 vs 0.2215; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.020; A12 = 0.74, large).
- Elitist generational + SUS: m=5 reached a lower re-evaluated error than m=10 (median 0.1476 vs 0.2215; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.020; A12 = 0.74, large).
- Elitist generational + Tournament: m=3 reached a lower re-evaluated error than m=10 (median 0.1191 vs 0.2098; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.002; A12 = 0.75, large).
- Generational + Roulette: m=1 reached a lower re-evaluated error than m=5 (median 0.2515 vs 0.4445; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.037; A12 = 0.72, large).
- Generational + Roulette: m=1 reached a lower re-evaluated error than m=10 (median 0.2515 vs 1.555; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.94, large).
- Generational + Roulette: m=3 reached a lower re-evaluated error than m=5 (median 0.349 vs 0.4445; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.016; A12 = 0.71, medium).
- Generational + Roulette: m=3 reached a lower re-evaluated error than m=10 (median 0.349 vs 1.555; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.95, large).
- Generational + Roulette: m=5 reached a lower re-evaluated error than m=10 (median 0.4445 vs 1.555; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.86, large).
- Generational + SUS: m=1 reached a lower re-evaluated error than m=3 (median 0.1732 vs 0.2345; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.006; A12 = 0.71, medium).
- Generational + SUS: m=1 reached a lower re-evaluated error than m=5 (median 0.1732 vs 0.3331; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.81, large).
- Generational + SUS: m=1 reached a lower re-evaluated error than m=10 (median 0.1732 vs 0.83; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.99, large).
- Generational + SUS: m=3 reached a lower re-evaluated error than m=10 (median 0.2345 vs 0.83; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.96, large).
- Generational + SUS: m=5 reached a lower re-evaluated error than m=10 (median 0.3331 vs 0.83; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.93, large).
- Generational + Tournament: m=1 reached a lower re-evaluated error than m=10 (median 0.169 vs 0.522; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.94, large).
- Generational + Tournament: m=3 reached a lower re-evaluated error than m=10 (median 0.158 vs 0.522; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.96, large).
- Generational + Tournament: m=5 reached a lower re-evaluated error than m=10 (median 0.2092 vs 0.522; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.90, large).
- Simulated annealing: m=3 reached a lower re-evaluated error than m=1 (median 0.1302 vs 0.1922; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.032; A12 = 0.69, medium).
- Simulated annealing: m=5 reached a lower re-evaluated error than m=1 (median 0.07481 vs 0.1922; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.032; A12 = 0.72, large).
- Simulated annealing: m=5 reached a lower re-evaluated error than m=10 (median 0.07481 vs 0.1551; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.032; A12 = 0.69, medium).
- Steady-state + Roulette: m=5 reached a lower re-evaluated error than m=10 (median 0.1502 vs 0.2061; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.010; A12 = 0.73, large).
- Steady-state + SUS: m=5 reached a lower re-evaluated error than m=10 (median 0.09062 vs 0.1691; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.011; A12 = 0.77, large).
- At each method's best mutation count: Hill climbing (m=5) reached a lower re-evaluated error than Generational + Roulette (m=1) (median 0.08424 vs 0.2515; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.85, large).
- At each method's best mutation count: Simulated annealing (m=5) reached a lower re-evaluated error than Generational + Roulette (m=1) (median 0.07481 vs 0.2515; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.86, large).
- At each method's best mutation count: Simulated annealing (m=5) reached a lower re-evaluated error than Generational + SUS (m=1) (median 0.07481 vs 0.1732; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.009; A12 = 0.75, large).
