# Statistical tests (re-evaluated error, lower is better)

## Re-evaluation

Each run's final best reelset was measured again on a simulator seed the run never used (100,000,000 spins). Sources: 990 runs from final check (optimizer).

In-run final best vs re-evaluated error (median over seeds). The in-run value is the lowest of many noisy measurements, so it is biased low; the ratio shows how much.

| Mutation | Method | In-run final best | Re-evaluated | Re-evaluated / in-run |
|---|---|---|---|---|
| 3 | Elitist generational + Roulette | 1.5 | 1.494 | 1.00 |
| 3 | Elitist generational + SUS | 1.38 | 1.381 | 1.00 |
| 3 | Elitist generational + Tournament | 1.44 | 1.456 | 1.01 |
| 3 | Generational + Roulette | 1.912 | 1.924 | 1.01 |
| 3 | Generational + SUS | 1.744 | 1.789 | 1.03 |
| 3 | Generational + Tournament | 1.7 | 1.68 | 0.99 |
| 3 | Hill climbing | 1.704 | 1.75 | 1.03 |
| 3 | Simulated annealing | 1.535 | 1.571 | 1.02 |
| 3 | Steady-state + Roulette | 1.533 | 1.553 | 1.01 |
| 3 | Steady-state + SUS | 1.274 | 1.277 | 1.00 |
| 3 | Steady-state + Tournament | 1.299 | 1.301 | 1.00 |
| 5 | Elitist generational + Roulette | 1.591 | 1.6 | 1.01 |
| 5 | Elitist generational + SUS | 1.325 | 1.354 | 1.02 |
| 5 | Elitist generational + Tournament | 1.355 | 1.365 | 1.01 |
| 5 | Generational + Roulette | 1.984 | 2.009 | 1.01 |
| 5 | Generational + SUS | 1.871 | 1.902 | 1.02 |
| 5 | Generational + Tournament | 1.7 | 1.695 | 1.00 |
| 5 | Hill climbing | 1.553 | 1.539 | 0.99 |
| 5 | Simulated annealing | 1.399 | 1.419 | 1.01 |
| 5 | Steady-state + Roulette | 1.568 | 1.576 | 1.01 |
| 5 | Steady-state + SUS | 1.383 | 1.44 | 1.04 |
| 5 | Steady-state + Tournament | 1.612 | 1.639 | 1.02 |
| 10 | Elitist generational + Roulette | 1.55 | 1.544 | 1.00 |
| 10 | Elitist generational + SUS | 1.677 | 1.697 | 1.01 |
| 10 | Elitist generational + Tournament | 1.473 | 1.438 | 0.98 |
| 10 | Generational + Roulette | 2.077 | 2.08 | 1.00 |
| 10 | Generational + SUS | 2.083 | 2.109 | 1.01 |
| 10 | Generational + Tournament | 1.821 | 1.847 | 1.01 |
| 10 | Hill climbing | 1.683 | 1.716 | 1.02 |
| 10 | Simulated annealing | 1.359 | 1.354 | 1.00 |
| 10 | Steady-state + Roulette | 1.744 | 1.729 | 0.99 |
| 10 | Steady-state + SUS | 1.548 | 1.562 | 1.01 |
| 10 | Steady-state + Tournament | 1.639 | 1.637 | 1.00 |

Paired by seed. Friedman omnibus test, then two-sided Wilcoxon signed-rank tests with Holm correction within each family; alpha = 0.05. Effect size = Vargha-Delaney A12 (probability the better method reaches a lower value on a run; 0.5 = no difference).
Noise floor = 0.0876: the smallest gap two independent re-evaluated error measurements can resolve at 95% (2.77 x simulator SD at the spins used).

## Omnibus tests (Friedman)

| Family | Mutation | Seeds | Methods | chi2 | p | Kendall's W |
|---|---|---|---|---|---|---|
| strategy | 3 | 30 | 3 | 24.27 | < 0.001 | 0.40 |
| selection (Steady-state) | 3 | 30 | 3 | 3.27 | 0.195 | 0.05 |
| selection (Elitist generational) | 3 | 30 | 3 | 2.60 | 0.273 | 0.04 |
| selection (Generational) | 3 | 30 | 3 | 8.27 | 0.016 | 0.14 |
| ga_vs_baselines | 3 | 30 | 11 | 71.04 | < 0.001 | 0.24 |
| all (exploratory) | 3 | 30 | 11 | 71.04 | < 0.001 | 0.24 |
| strategy | 5 | 30 | 3 | 28.87 | < 0.001 | 0.48 |
| selection (Steady-state) | 5 | 30 | 3 | 0.87 | 0.648 | 0.01 |
| selection (Elitist generational) | 5 | 30 | 3 | 4.20 | 0.122 | 0.07 |
| selection (Generational) | 5 | 30 | 3 | 9.60 | 0.008 | 0.16 |
| ga_vs_baselines | 5 | 30 | 11 | 74.15 | < 0.001 | 0.25 |
| all (exploratory) | 5 | 30 | 11 | 74.15 | < 0.001 | 0.25 |
| strategy | 10 | 30 | 3 | 34.40 | < 0.001 | 0.57 |
| selection (Steady-state) | 10 | 30 | 3 | 1.40 | 0.497 | 0.02 |
| selection (Elitist generational) | 10 | 30 | 3 | 4.47 | 0.107 | 0.07 |
| selection (Generational) | 10 | 30 | 3 | 11.27 | 0.004 | 0.19 |
| ga_vs_baselines | 10 | 30 | 11 | 95.16 | < 0.001 | 0.32 |
| all (exploratory) | 10 | 30 | 11 | 95.16 | < 0.001 | 0.32 |

## strategy

| Mutation | Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|---|
| 3 | Steady-state | Elitist generational | 1.297 / 1.342 | no | 15/30 | 0.919 | 0.50 | negligible |
| 3 | Steady-state | Generational | 1.297 / 1.775 | yes | 27/30 | < 0.001 * | 0.85 | large |
| 3 | Elitist generational | Generational | 1.342 / 1.775 | yes | 25/30 | < 0.001 * | 0.84 | large |
| 5 | Elitist generational | Steady-state | 1.429 / 1.541 | yes | 16/30 | 0.452 | 0.57 | small |
| 5 | Steady-state | Generational | 1.541 / 1.906 | yes | 27/30 | < 0.001 * | 0.89 | large |
| 5 | Elitist generational | Generational | 1.429 / 1.906 | yes | 27/30 | < 0.001 * | 0.90 | large |
| 10 | Elitist generational | Steady-state | 1.552 / 1.603 | no | 13/30 | 0.903 | 0.52 | negligible |
| 10 | Steady-state | Generational | 1.603 / 2.038 | yes | 29/30 | < 0.001 * | 0.94 | large |
| 10 | Elitist generational | Generational | 1.552 / 2.038 | yes | 27/30 | < 0.001 * | 0.93 | large |

## selection (Steady-state)

| Mutation | Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|---|
| 3 | SUS | Roulette | 1.277 / 1.553 | yes | 20/30 | 0.616 | 0.60 | small |
| 3 | Tournament | Roulette | 1.301 / 1.553 | yes | 15/30 | 0.657 | 0.57 | small |
| 3 | SUS | Tournament | 1.277 / 1.301 | no | 18/30 | 0.657 | 0.52 | negligible |
| 5 | SUS | Roulette | 1.44 / 1.576 | yes | 17/30 | 1.000 | 0.55 | negligible |
| 5 | Tournament | Roulette | 1.639 / 1.576 | no | 17/30 | 1.000 | 0.55 | negligible |
| 5 | Tournament | SUS | 1.639 / 1.44 | no | 16/30 | 1.000 | 0.51 | negligible |
| 10 | SUS | Roulette | 1.562 / 1.729 | yes | 17/30 | 1.000 | 0.58 | small |
| 10 | Tournament | Roulette | 1.637 / 1.729 | yes | 18/30 | 1.000 | 0.55 | negligible |
| 10 | SUS | Tournament | 1.562 / 1.637 | no | 14/30 | 1.000 | 0.52 | negligible |

## selection (Elitist generational)

| Mutation | Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|---|
| 3 | SUS | Roulette | 1.381 / 1.494 | yes | 20/30 | 0.594 | 0.57 | small |
| 3 | Tournament | Roulette | 1.456 / 1.494 | no | 17/30 | 1.000 | 0.53 | negligible |
| 3 | SUS | Tournament | 1.381 / 1.456 | no | 15/30 | 1.000 | 0.54 | negligible |
| 5 | SUS | Roulette | 1.354 / 1.6 | yes | 19/30 | 0.281 | 0.64 | medium |
| 5 | Tournament | Roulette | 1.365 / 1.6 | yes | 20/30 | 0.210 | 0.64 | medium |
| 5 | SUS | Tournament | 1.354 / 1.365 | no | 14/30 | 0.952 | 0.51 | negligible |
| 10 | Roulette | SUS | 1.544 / 1.697 | yes | 18/30 | 0.584 | 0.59 | small |
| 10 | Tournament | Roulette | 1.438 / 1.544 | yes | 20/30 | 0.238 | 0.58 | small |
| 10 | Tournament | SUS | 1.438 / 1.697 | yes | 19/30 | 0.220 | 0.66 | medium |

## selection (Generational)

| Mutation | Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|---|
| 3 | SUS | Roulette | 1.789 / 1.924 | yes | 19/30 | 0.058 | 0.63 | small |
| 3 | Tournament | Roulette | 1.68 / 1.924 | yes | 21/30 | 0.010 * | 0.73 | large |
| 3 | Tournament | SUS | 1.68 / 1.789 | yes | 21/30 | 0.033 * | 0.62 | small |
| 5 | SUS | Roulette | 1.902 / 2.009 | yes | 20/30 | 0.299 | 0.58 | small |
| 5 | Tournament | Roulette | 1.695 / 2.009 | yes | 22/30 | 0.002 * | 0.75 | large |
| 5 | Tournament | SUS | 1.695 / 1.902 | yes | 20/30 | 0.037 * | 0.71 | medium |
| 10 | SUS | Roulette | 2.109 / 2.08 | no | 16/30 | 0.935 | 0.52 | negligible |
| 10 | Tournament | Roulette | 1.847 / 2.08 | yes | 22/30 | 0.002 * | 0.76 | large |
| 10 | Tournament | SUS | 1.847 / 2.109 | yes | 23/30 | 0.002 * | 0.77 | large |

## ga_vs_baselines

| Mutation | Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|---|
| 3 | Elitist generational + Roulette | Hill climbing | 1.494 / 1.75 | yes | 18/30 | 0.425 | 0.67 | medium |
| 3 | Simulated annealing | Elitist generational + Roulette | 1.571 / 1.494 | no | 15/30 | 1.000 | 0.52 | negligible |
| 3 | Elitist generational + SUS | Hill climbing | 1.381 / 1.75 | yes | 24/30 | 0.016 * | 0.75 | large |
| 3 | Elitist generational + SUS | Simulated annealing | 1.381 / 1.571 | yes | 18/30 | 1.000 | 0.55 | negligible |
| 3 | Elitist generational + Tournament | Hill climbing | 1.456 / 1.75 | yes | 22/30 | 0.154 | 0.69 | medium |
| 3 | Elitist generational + Tournament | Simulated annealing | 1.456 / 1.571 | yes | 15/30 | 1.000 | 0.50 | negligible |
| 3 | Hill climbing | Generational + Roulette | 1.75 / 1.924 | yes | 22/30 | 0.070 | 0.70 | medium |
| 3 | Simulated annealing | Generational + Roulette | 1.571 / 1.924 | yes | 22/30 | 0.006 * | 0.82 | large |
| 3 | Hill climbing | Generational + SUS | 1.75 / 1.789 | no | 17/30 | 1.000 | 0.59 | small |
| 3 | Simulated annealing | Generational + SUS | 1.571 / 1.789 | yes | 24/30 | 0.003 * | 0.74 | large |
| 3 | Generational + Tournament | Hill climbing | 1.68 / 1.75 | no | 19/30 | 1.000 | 0.54 | negligible |
| 3 | Simulated annealing | Generational + Tournament | 1.571 / 1.68 | yes | 20/30 | 0.327 | 0.64 | small |
| 3 | Steady-state + Roulette | Hill climbing | 1.553 / 1.75 | yes | 22/30 | 0.243 | 0.66 | medium |
| 3 | Steady-state + SUS | Hill climbing | 1.277 / 1.75 | yes | 26/30 | < 0.001 * | 0.76 | large |
| 3 | Steady-state + Tournament | Hill climbing | 1.301 / 1.75 | yes | 24/30 | 0.016 * | 0.72 | large |
| 3 | Simulated annealing | Steady-state + Roulette | 1.571 / 1.553 | no | 19/30 | 1.000 | 0.53 | negligible |
| 3 | Steady-state + SUS | Simulated annealing | 1.277 / 1.571 | yes | 18/30 | 1.000 | 0.56 | negligible |
| 3 | Steady-state + Tournament | Simulated annealing | 1.301 / 1.571 | yes | 16/30 | 1.000 | 0.54 | negligible |
| 5 | Hill climbing | Elitist generational + Roulette | 1.539 / 1.6 | no | 18/30 | 1.000 | 0.58 | small |
| 5 | Simulated annealing | Elitist generational + Roulette | 1.419 / 1.6 | yes | 18/30 | 1.000 | 0.63 | small |
| 5 | Elitist generational + SUS | Hill climbing | 1.354 / 1.539 | yes | 18/30 | 1.000 | 0.57 | small |
| 5 | Simulated annealing | Elitist generational + SUS | 1.419 / 1.354 | no | 17/30 | 1.000 | 0.50 | negligible |
| 5 | Elitist generational + Tournament | Hill climbing | 1.365 / 1.539 | yes | 19/30 | 1.000 | 0.56 | negligible |
| 5 | Simulated annealing | Elitist generational + Tournament | 1.419 / 1.365 | no | 16/30 | 1.000 | 0.51 | negligible |
| 5 | Hill climbing | Generational + Roulette | 1.539 / 2.009 | yes | 25/30 | < 0.001 * | 0.85 | large |
| 5 | Simulated annealing | Generational + Roulette | 1.419 / 2.009 | yes | 25/30 | < 0.001 * | 0.87 | large |
| 5 | Hill climbing | Generational + SUS | 1.539 / 1.902 | yes | 23/30 | 0.002 * | 0.82 | large |
| 5 | Simulated annealing | Generational + SUS | 1.419 / 1.902 | yes | 25/30 | < 0.001 * | 0.84 | large |
| 5 | Hill climbing | Generational + Tournament | 1.539 / 1.695 | yes | 20/30 | 0.147 | 0.65 | medium |
| 5 | Simulated annealing | Generational + Tournament | 1.419 / 1.695 | yes | 25/30 | 0.016 * | 0.71 | medium |
| 5 | Hill climbing | Steady-state + Roulette | 1.539 / 1.576 | no | 17/30 | 1.000 | 0.53 | negligible |
| 5 | Steady-state + SUS | Hill climbing | 1.44 / 1.539 | yes | 17/30 | 1.000 | 0.52 | negligible |
| 5 | Steady-state + Tournament | Hill climbing | 1.639 / 1.539 | no | 16/30 | 1.000 | 0.53 | negligible |
| 5 | Simulated annealing | Steady-state + Roulette | 1.419 / 1.576 | yes | 19/30 | 1.000 | 0.59 | small |
| 5 | Simulated annealing | Steady-state + SUS | 1.419 / 1.44 | no | 18/30 | 1.000 | 0.53 | negligible |
| 5 | Simulated annealing | Steady-state + Tournament | 1.419 / 1.639 | yes | 15/30 | 1.000 | 0.52 | negligible |
| 10 | Elitist generational + Roulette | Hill climbing | 1.544 / 1.716 | yes | 14/30 | 1.000 | 0.54 | negligible |
| 10 | Simulated annealing | Elitist generational + Roulette | 1.354 / 1.544 | yes | 20/30 | 0.769 | 0.62 | small |
| 10 | Hill climbing | Elitist generational + SUS | 1.716 / 1.697 | no | 19/30 | 1.000 | 0.54 | negligible |
| 10 | Simulated annealing | Elitist generational + SUS | 1.354 / 1.697 | yes | 19/30 | 0.461 | 0.67 | medium |
| 10 | Elitist generational + Tournament | Hill climbing | 1.438 / 1.716 | yes | 17/30 | 1.000 | 0.59 | small |
| 10 | Simulated annealing | Elitist generational + Tournament | 1.354 / 1.438 | no | 17/30 | 1.000 | 0.56 | small |
| 10 | Hill climbing | Generational + Roulette | 1.716 / 2.08 | yes | 24/30 | < 0.001 * | 0.85 | large |
| 10 | Simulated annealing | Generational + Roulette | 1.354 / 2.08 | yes | 30/30 | < 0.001 * | 0.91 | large |
| 10 | Hill climbing | Generational + SUS | 1.716 / 2.109 | yes | 25/30 | < 0.001 * | 0.86 | large |
| 10 | Simulated annealing | Generational + SUS | 1.354 / 2.109 | yes | 30/30 | < 0.001 * | 0.92 | large |
| 10 | Hill climbing | Generational + Tournament | 1.716 / 1.847 | yes | 19/30 | 0.227 | 0.67 | medium |
| 10 | Simulated annealing | Generational + Tournament | 1.354 / 1.847 | yes | 25/30 | 0.003 * | 0.80 | large |
| 10 | Hill climbing | Steady-state + Roulette | 1.716 / 1.729 | no | 14/30 | 1.000 | 0.52 | negligible |
| 10 | Steady-state + SUS | Hill climbing | 1.562 / 1.716 | yes | 13/30 | 1.000 | 0.56 | negligible |
| 10 | Steady-state + Tournament | Hill climbing | 1.637 / 1.716 | no | 15/30 | 1.000 | 0.54 | negligible |
| 10 | Simulated annealing | Steady-state + Roulette | 1.354 / 1.729 | yes | 18/30 | 0.961 | 0.65 | medium |
| 10 | Simulated annealing | Steady-state + SUS | 1.354 / 1.562 | yes | 17/30 | 1.000 | 0.59 | small |
| 10 | Simulated annealing | Steady-state + Tournament | 1.354 / 1.637 | yes | 18/30 | 0.961 | 0.60 | small |

## Claims you can make

Significant after Holm, A12 at least small, and median gap above the noise floor.

- Mutation 3: Steady-state reached a lower re-evaluated error than Generational (median 1.297 vs 1.775; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.85, large).
- Mutation 3: Elitist generational reached a lower re-evaluated error than Generational (median 1.342 vs 1.775; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.84, large).
- Mutation 3: Tournament reached a lower re-evaluated error than Roulette (median 1.68 vs 1.924; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.010; A12 = 0.73, large).
- Mutation 3: Tournament reached a lower re-evaluated error than SUS (median 1.68 vs 1.789; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.033; A12 = 0.62, small).
- Mutation 3: Elitist generational + SUS reached a lower re-evaluated error than Hill climbing (median 1.381 vs 1.75; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.016; A12 = 0.75, large).
- Mutation 3: Simulated annealing reached a lower re-evaluated error than Generational + Roulette (median 1.571 vs 1.924; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.006; A12 = 0.82, large).
- Mutation 3: Simulated annealing reached a lower re-evaluated error than Generational + SUS (median 1.571 vs 1.789; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.003; A12 = 0.74, large).
- Mutation 3: Steady-state + SUS reached a lower re-evaluated error than Hill climbing (median 1.277 vs 1.75; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.76, large).
- Mutation 3: Steady-state + Tournament reached a lower re-evaluated error than Hill climbing (median 1.301 vs 1.75; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.016; A12 = 0.72, large).
- Mutation 5: Steady-state reached a lower re-evaluated error than Generational (median 1.541 vs 1.906; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.89, large).
- Mutation 5: Elitist generational reached a lower re-evaluated error than Generational (median 1.429 vs 1.906; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.90, large).
- Mutation 5: Tournament reached a lower re-evaluated error than Roulette (median 1.695 vs 2.009; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.002; A12 = 0.75, large).
- Mutation 5: Tournament reached a lower re-evaluated error than SUS (median 1.695 vs 1.902; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.037; A12 = 0.71, medium).
- Mutation 5: Hill climbing reached a lower re-evaluated error than Generational + Roulette (median 1.539 vs 2.009; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.85, large).
- Mutation 5: Simulated annealing reached a lower re-evaluated error than Generational + Roulette (median 1.419 vs 2.009; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.87, large).
- Mutation 5: Hill climbing reached a lower re-evaluated error than Generational + SUS (median 1.539 vs 1.902; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.002; A12 = 0.82, large).
- Mutation 5: Simulated annealing reached a lower re-evaluated error than Generational + SUS (median 1.419 vs 1.902; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.84, large).
- Mutation 5: Simulated annealing reached a lower re-evaluated error than Generational + Tournament (median 1.419 vs 1.695; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.016; A12 = 0.71, medium).
- Mutation 10: Steady-state reached a lower re-evaluated error than Generational (median 1.603 vs 2.038; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.94, large).
- Mutation 10: Elitist generational reached a lower re-evaluated error than Generational (median 1.552 vs 2.038; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.93, large).
- Mutation 10: Tournament reached a lower re-evaluated error than Roulette (median 1.847 vs 2.08; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.002; A12 = 0.76, large).
- Mutation 10: Tournament reached a lower re-evaluated error than SUS (median 1.847 vs 2.109; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.002; A12 = 0.77, large).
- Mutation 10: Hill climbing reached a lower re-evaluated error than Generational + Roulette (median 1.716 vs 2.08; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.85, large).
- Mutation 10: Simulated annealing reached a lower re-evaluated error than Generational + Roulette (median 1.354 vs 2.08; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.91, large).
- Mutation 10: Hill climbing reached a lower re-evaluated error than Generational + SUS (median 1.716 vs 2.109; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.86, large).
- Mutation 10: Simulated annealing reached a lower re-evaluated error than Generational + SUS (median 1.354 vs 2.109; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.92, large).
- Mutation 10: Simulated annealing reached a lower re-evaluated error than Generational + Tournament (median 1.354 vs 1.847; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.003; A12 = 0.80, large).
