# Statistical tests (re-evaluated error, lower is better)

## Re-evaluation

Each run's final best reelset was measured again on a simulator seed the run never used (100,000,000 spins). Sources: 1440 runs from final check (optimizer).

In-run final best vs re-evaluated error (median over seeds). The in-run value is the lowest of many noisy measurements, so it is biased low; the ratio shows how much.

| Mutation | Method | In-run final best | Re-evaluated | Re-evaluated / in-run |
|---|---|---|---|---|
| 1 | Elitist generational + Roulette | 1.938 | 1.94 | 1.00 |
| 1 | Elitist generational + SUS | 1.799 | 1.828 | 1.02 |
| 1 | Elitist generational + Tournament | 1.983 | 2.021 | 1.02 |
| 1 | Generational + Roulette | 2.12 | 2.069 | 0.98 |
| 1 | Generational + SUS | 1.865 | 1.885 | 1.01 |
| 1 | Generational + Tournament | 1.992 | 2.01 | 1.01 |
| 1 | Hill climbing | 1.924 | 1.988 | 1.03 |
| 1 | Random search | 62.71 | 62.84 | 1.00 |
| 1 | Simulated annealing | 1.893 | 1.926 | 1.02 |
| 1 | Steady-state + Roulette | 1.938 | 2.008 | 1.04 |
| 1 | Steady-state + SUS | 2.021 | 2.072 | 1.03 |
| 1 | Steady-state + Tournament | 1.997 | 2.032 | 1.02 |
| 3 | Elitist generational + Roulette | 1.354 | 1.363 | 1.01 |
| 3 | Elitist generational + SUS | 1.479 | 1.479 | 1.00 |
| 3 | Elitist generational + Tournament | 1.398 | 1.423 | 1.02 |
| 3 | Generational + Roulette | 1.924 | 1.907 | 0.99 |
| 3 | Generational + SUS | 1.743 | 1.729 | 0.99 |
| 3 | Generational + Tournament | 1.684 | 1.706 | 1.01 |
| 3 | Hill climbing | 1.748 | 1.78 | 1.02 |
| 3 | Random search | 62.71 | 62.84 | 1.00 |
| 3 | Simulated annealing | 1.481 | 1.532 | 1.03 |
| 3 | Steady-state + Roulette | 1.344 | 1.356 | 1.01 |
| 3 | Steady-state + SUS | 1.275 | 1.262 | 0.99 |
| 3 | Steady-state + Tournament | 1.218 | 1.303 | 1.07 |
| 5 | Elitist generational + Roulette | 1.432 | 1.474 | 1.03 |
| 5 | Elitist generational + SUS | 1.407 | 1.431 | 1.02 |
| 5 | Elitist generational + Tournament | 1.176 | 1.174 | 1.00 |
| 5 | Generational + Roulette | 1.991 | 2.001 | 1.01 |
| 5 | Generational + SUS | 1.9 | 1.9 | 1.00 |
| 5 | Generational + Tournament | 1.881 | 1.87 | 0.99 |
| 5 | Hill climbing | 1.594 | 1.559 | 0.98 |
| 5 | Random search | 62.71 | 62.84 | 1.00 |
| 5 | Simulated annealing | 1.281 | 1.277 | 1.00 |
| 5 | Steady-state + Roulette | 1.7 | 1.718 | 1.01 |
| 5 | Steady-state + SUS | 1.456 | 1.489 | 1.02 |
| 5 | Steady-state + Tournament | 1.327 | 1.347 | 1.02 |
| 10 | Elitist generational + Roulette | 1.561 | 1.574 | 1.01 |
| 10 | Elitist generational + SUS | 1.717 | 1.73 | 1.01 |
| 10 | Elitist generational + Tournament | 1.604 | 1.601 | 1.00 |
| 10 | Generational + Roulette | 2.05 | 2.059 | 1.00 |
| 10 | Generational + SUS | 1.965 | 1.952 | 0.99 |
| 10 | Generational + Tournament | 1.955 | 1.99 | 1.02 |
| 10 | Hill climbing | 1.546 | 1.527 | 0.99 |
| 10 | Random search | 62.71 | 62.84 | 1.00 |
| 10 | Simulated annealing | 1.49 | 1.494 | 1.00 |
| 10 | Steady-state + Roulette | 1.737 | 1.766 | 1.02 |
| 10 | Steady-state + SUS | 1.575 | 1.593 | 1.01 |
| 10 | Steady-state + Tournament | 1.763 | 1.797 | 1.02 |

Paired by seed. Friedman omnibus test, then two-sided Wilcoxon signed-rank tests with Holm correction within each family; alpha = 0.05. Effect size = Vargha-Delaney A12 (probability the better method reaches a lower value on a run; 0.5 = no difference).
Noise floor = 0.0876: the smallest gap two independent re-evaluated error measurements can resolve at 95% (2.77 x simulator SD at the spins used).

## Omnibus tests (Friedman)

| Family | Mutation | Seeds | Methods | chi2 | p | Kendall's W |
|---|---|---|---|---|---|---|
| strategy | 1 | 30 | 3 | 10.47 | 0.005 | 0.17 |
| selection (Steady-state) | 1 | 30 | 3 | 3.80 | 0.150 | 0.06 |
| selection (Elitist generational) | 1 | 30 | 3 | 5.27 | 0.072 | 0.09 |
| selection (Generational) | 1 | 30 | 3 | 6.47 | 0.039 | 0.11 |
| ga_vs_baselines | 1 | 30 | 12 | 90.76 | < 0.001 | 0.28 |
| all (exploratory) | 1 | 30 | 12 | 90.76 | < 0.001 | 0.28 |
| strategy | 3 | 30 | 3 | 24.27 | < 0.001 | 0.40 |
| selection (Steady-state) | 3 | 30 | 3 | 2.07 | 0.356 | 0.03 |
| selection (Elitist generational) | 3 | 30 | 3 | 0.60 | 0.741 | 0.01 |
| selection (Generational) | 3 | 30 | 3 | 3.80 | 0.150 | 0.06 |
| ga_vs_baselines | 3 | 30 | 12 | 133.62 | < 0.001 | 0.40 |
| all (exploratory) | 3 | 30 | 12 | 133.62 | < 0.001 | 0.40 |
| strategy | 5 | 30 | 3 | 35.00 | < 0.001 | 0.58 |
| selection (Steady-state) | 5 | 30 | 3 | 1.67 | 0.435 | 0.03 |
| selection (Elitist generational) | 5 | 30 | 3 | 4.27 | 0.118 | 0.07 |
| selection (Generational) | 5 | 30 | 3 | 6.47 | 0.039 | 0.11 |
| ga_vs_baselines | 5 | 30 | 12 | 138.18 | < 0.001 | 0.42 |
| all (exploratory) | 5 | 30 | 12 | 138.18 | < 0.001 | 0.42 |
| strategy | 10 | 30 | 3 | 24.47 | < 0.001 | 0.41 |
| selection (Steady-state) | 10 | 30 | 3 | 0.07 | 0.967 | 0.00 |
| selection (Elitist generational) | 10 | 30 | 3 | 1.27 | 0.531 | 0.02 |
| selection (Generational) | 10 | 30 | 3 | 2.40 | 0.301 | 0.04 |
| ga_vs_baselines | 10 | 30 | 12 | 128.11 | < 0.001 | 0.39 |
| all (exploratory) | 10 | 30 | 12 | 128.11 | < 0.001 | 0.39 |

## strategy

| Mutation | Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|---|
| 1 | Elitist generational | Steady-state | 1.903 / 2.071 | yes | 23/30 | 0.030 * | 0.65 | medium |
| 1 | Generational | Steady-state | 1.997 / 2.071 | no | 20/30 | 0.354 | 0.57 | small |
| 1 | Elitist generational | Generational | 1.903 / 1.997 | yes | 19/30 | 0.354 | 0.62 | small |
| 3 | Steady-state | Elitist generational | 1.288 / 1.442 | yes | 15/30 | 0.100 | 0.62 | small |
| 3 | Steady-state | Generational | 1.288 / 1.761 | yes | 27/30 | < 0.001 * | 0.89 | large |
| 3 | Elitist generational | Generational | 1.442 / 1.761 | yes | 25/30 | < 0.001 * | 0.80 | large |
| 5 | Elitist generational | Steady-state | 1.289 / 1.568 | yes | 21/30 | 0.009 * | 0.65 | medium |
| 5 | Steady-state | Generational | 1.568 / 1.949 | yes | 26/30 | < 0.001 * | 0.82 | large |
| 5 | Elitist generational | Generational | 1.289 / 1.949 | yes | 29/30 | < 0.001 * | 0.94 | large |
| 10 | Elitist generational | Steady-state | 1.673 / 1.72 | no | 13/30 | 0.715 | 0.53 | negligible |
| 10 | Steady-state | Generational | 1.72 / 1.999 | yes | 26/30 | < 0.001 * | 0.83 | large |
| 10 | Elitist generational | Generational | 1.673 / 1.999 | yes | 26/30 | < 0.001 * | 0.85 | large |

## selection (Steady-state)

| Mutation | Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|---|
| 1 | Roulette | SUS | 2.008 / 2.072 | no | 20/30 | 1.000 | 0.55 | negligible |
| 1 | Roulette | Tournament | 2.008 / 2.032 | no | 18/30 | 1.000 | 0.54 | negligible |
| 1 | Tournament | SUS | 2.032 / 2.072 | no | 17/30 | 1.000 | 0.53 | negligible |
| 3 | SUS | Roulette | 1.262 / 1.356 | yes | 18/30 | 1.000 | 0.55 | negligible |
| 3 | Tournament | Roulette | 1.303 / 1.356 | no | 17/30 | 1.000 | 0.55 | negligible |
| 3 | Tournament | SUS | 1.303 / 1.262 | no | 19/30 | 1.000 | 0.53 | negligible |
| 5 | SUS | Roulette | 1.489 / 1.718 | yes | 17/30 | 0.720 | 0.57 | small |
| 5 | Tournament | Roulette | 1.347 / 1.718 | yes | 18/30 | 0.276 | 0.61 | small |
| 5 | Tournament | SUS | 1.347 / 1.489 | yes | 17/30 | 0.720 | 0.57 | small |
| 10 | SUS | Roulette | 1.593 / 1.766 | yes | 14/30 | 1.000 | 0.56 | negligible |
| 10 | Tournament | Roulette | 1.797 / 1.766 | no | 15/30 | 1.000 | 0.53 | negligible |
| 10 | SUS | Tournament | 1.593 / 1.797 | yes | 16/30 | 1.000 | 0.52 | negligible |

## selection (Elitist generational)

| Mutation | Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|---|
| 1 | SUS | Roulette | 1.828 / 1.94 | yes | 20/30 | 0.259 | 0.64 | medium |
| 1 | Roulette | Tournament | 1.94 / 2.021 | no | 17/30 | 0.839 | 0.53 | negligible |
| 1 | SUS | Tournament | 1.828 / 2.021 | yes | 20/30 | 0.034 * | 0.64 | medium |
| 3 | Roulette | SUS | 1.363 / 1.479 | yes | 17/30 | 1.000 | 0.54 | negligible |
| 3 | Roulette | Tournament | 1.363 / 1.423 | no | 16/30 | 1.000 | 0.53 | negligible |
| 3 | Tournament | SUS | 1.423 / 1.479 | no | 16/30 | 1.000 | 0.52 | negligible |
| 5 | SUS | Roulette | 1.431 / 1.474 | no | 18/30 | 0.612 | 0.53 | negligible |
| 5 | Tournament | Roulette | 1.174 / 1.474 | yes | 20/30 | 0.173 | 0.62 | small |
| 5 | Tournament | SUS | 1.174 / 1.431 | yes | 18/30 | 0.396 | 0.58 | small |
| 10 | Roulette | SUS | 1.574 / 1.73 | yes | 18/30 | 0.980 | 0.56 | small |
| 10 | Tournament | Roulette | 1.601 / 1.574 | no | 15/30 | 0.980 | 0.54 | negligible |
| 10 | Tournament | SUS | 1.601 / 1.73 | yes | 17/30 | 0.438 | 0.61 | small |

## selection (Generational)

| Mutation | Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|---|
| 1 | SUS | Roulette | 1.885 / 2.069 | yes | 23/30 | 0.001 * | 0.69 | medium |
| 1 | Tournament | Roulette | 2.01 / 2.069 | no | 18/30 | 0.368 | 0.63 | small |
| 1 | SUS | Tournament | 1.885 / 2.01 | yes | 15/30 | 0.368 | 0.57 | small |
| 3 | SUS | Roulette | 1.729 / 1.907 | yes | 17/30 | 0.173 | 0.66 | medium |
| 3 | Tournament | Roulette | 1.706 / 1.907 | yes | 21/30 | 0.173 | 0.65 | medium |
| 3 | Tournament | SUS | 1.706 / 1.729 | no | 16/30 | 0.670 | 0.52 | negligible |
| 5 | SUS | Roulette | 1.9 / 2.001 | yes | 19/30 | 0.127 | 0.66 | medium |
| 5 | Tournament | Roulette | 1.87 / 2.001 | yes | 22/30 | 0.013 * | 0.69 | medium |
| 5 | Tournament | SUS | 1.87 / 1.9 | no | 16/30 | 0.808 | 0.52 | negligible |
| 10 | SUS | Roulette | 1.952 / 2.059 | yes | 17/30 | 0.617 | 0.58 | small |
| 10 | Tournament | Roulette | 1.99 / 2.059 | no | 19/30 | 0.173 | 0.63 | small |
| 10 | Tournament | SUS | 1.99 / 1.952 | no | 17/30 | 0.617 | 0.54 | negligible |

## ga_vs_baselines

| Mutation | Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|---|
| 1 | Elitist generational + Roulette | Hill climbing | 1.94 / 1.988 | no | 21/30 | 1.000 | 0.57 | small |
| 1 | Elitist generational + Roulette | Random search | 1.94 / 62.84 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 1 | Simulated annealing | Elitist generational + Roulette | 1.926 / 1.94 | no | 15/30 | 1.000 | 0.53 | negligible |
| 1 | Elitist generational + SUS | Hill climbing | 1.828 / 1.988 | yes | 21/30 | 0.278 | 0.69 | medium |
| 1 | Elitist generational + SUS | Random search | 1.828 / 62.84 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 1 | Elitist generational + SUS | Simulated annealing | 1.828 / 1.926 | yes | 15/30 | 1.000 | 0.59 | small |
| 1 | Elitist generational + Tournament | Hill climbing | 2.021 / 1.988 | no | 15/30 | 1.000 | 0.55 | negligible |
| 1 | Elitist generational + Tournament | Random search | 2.021 / 62.84 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 1 | Simulated annealing | Elitist generational + Tournament | 1.926 / 2.021 | yes | 17/30 | 1.000 | 0.53 | negligible |
| 1 | Hill climbing | Generational + Roulette | 1.988 / 2.069 | no | 15/30 | 1.000 | 0.52 | negligible |
| 1 | Generational + Roulette | Random search | 2.069 / 62.84 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 1 | Simulated annealing | Generational + Roulette | 1.926 / 2.069 | yes | 16/30 | 1.000 | 0.62 | small |
| 1 | Generational + SUS | Hill climbing | 1.885 / 1.988 | yes | 18/30 | 1.000 | 0.63 | small |
| 1 | Generational + SUS | Random search | 1.885 / 62.84 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 1 | Generational + SUS | Simulated annealing | 1.885 / 1.926 | no | 15/30 | 1.000 | 0.54 | negligible |
| 1 | Generational + Tournament | Hill climbing | 2.01 / 1.988 | no | 19/30 | 1.000 | 0.56 | small |
| 1 | Generational + Tournament | Random search | 2.01 / 62.84 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 1 | Simulated annealing | Generational + Tournament | 1.926 / 2.01 | no | 15/30 | 1.000 | 0.53 | negligible |
| 1 | Steady-state + Roulette | Hill climbing | 2.008 / 1.988 | no | 18/30 | 1.000 | 0.55 | negligible |
| 1 | Hill climbing | Steady-state + SUS | 1.988 / 2.072 | no | 15/30 | 1.000 | 0.51 | negligible |
| 1 | Steady-state + Tournament | Hill climbing | 2.032 / 1.988 | no | 17/30 | 1.000 | 0.53 | negligible |
| 1 | Steady-state + Roulette | Random search | 2.008 / 62.84 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 1 | Steady-state + SUS | Random search | 2.072 / 62.84 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 1 | Steady-state + Tournament | Random search | 2.032 / 62.84 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 1 | Simulated annealing | Steady-state + Roulette | 1.926 / 2.008 | no | 15/30 | 1.000 | 0.53 | negligible |
| 1 | Simulated annealing | Steady-state + SUS | 1.926 / 2.072 | yes | 19/30 | 1.000 | 0.59 | small |
| 1 | Simulated annealing | Steady-state + Tournament | 1.926 / 2.032 | yes | 17/30 | 1.000 | 0.56 | small |
| 3 | Elitist generational + Roulette | Hill climbing | 1.363 / 1.78 | yes | 22/30 | 0.001 * | 0.77 | large |
| 3 | Elitist generational + Roulette | Random search | 1.363 / 62.84 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 3 | Elitist generational + Roulette | Simulated annealing | 1.363 / 1.532 | yes | 16/30 | 1.000 | 0.58 | small |
| 3 | Elitist generational + SUS | Hill climbing | 1.479 / 1.78 | yes | 22/30 | 0.015 * | 0.72 | large |
| 3 | Elitist generational + SUS | Random search | 1.479 / 62.84 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 3 | Elitist generational + SUS | Simulated annealing | 1.479 / 1.532 | no | 18/30 | 1.000 | 0.53 | negligible |
| 3 | Elitist generational + Tournament | Hill climbing | 1.423 / 1.78 | yes | 21/30 | 0.036 * | 0.73 | large |
| 3 | Elitist generational + Tournament | Random search | 1.423 / 62.84 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 3 | Elitist generational + Tournament | Simulated annealing | 1.423 / 1.532 | yes | 14/30 | 1.000 | 0.56 | negligible |
| 3 | Hill climbing | Generational + Roulette | 1.78 / 1.907 | yes | 19/30 | 1.000 | 0.61 | small |
| 3 | Generational + Roulette | Random search | 1.907 / 62.84 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 3 | Simulated annealing | Generational + Roulette | 1.532 / 1.907 | yes | 24/30 | 0.001 * | 0.80 | large |
| 3 | Generational + SUS | Hill climbing | 1.729 / 1.78 | no | 16/30 | 1.000 | 0.54 | negligible |
| 3 | Generational + SUS | Random search | 1.729 / 62.84 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 3 | Simulated annealing | Generational + SUS | 1.532 / 1.729 | yes | 22/30 | 0.048 * | 0.67 | medium |
| 3 | Generational + Tournament | Hill climbing | 1.706 / 1.78 | no | 16/30 | 1.000 | 0.56 | small |
| 3 | Generational + Tournament | Random search | 1.706 / 62.84 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 3 | Simulated annealing | Generational + Tournament | 1.532 / 1.706 | yes | 19/30 | 0.803 | 0.64 | small |
| 3 | Steady-state + Roulette | Hill climbing | 1.356 / 1.78 | yes | 23/30 | 0.004 * | 0.80 | large |
| 3 | Steady-state + SUS | Hill climbing | 1.262 / 1.78 | yes | 27/30 | < 0.001 * | 0.83 | large |
| 3 | Steady-state + Tournament | Hill climbing | 1.303 / 1.78 | yes | 25/30 | < 0.001 * | 0.77 | large |
| 3 | Steady-state + Roulette | Random search | 1.356 / 62.84 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 3 | Steady-state + SUS | Random search | 1.262 / 62.84 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 3 | Steady-state + Tournament | Random search | 1.303 / 62.84 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 3 | Steady-state + Roulette | Simulated annealing | 1.356 / 1.532 | yes | 18/30 | 1.000 | 0.62 | small |
| 3 | Steady-state + SUS | Simulated annealing | 1.262 / 1.532 | yes | 22/30 | 0.723 | 0.66 | medium |
| 3 | Steady-state + Tournament | Simulated annealing | 1.303 / 1.532 | yes | 20/30 | 0.549 | 0.63 | small |
| 5 | Hill climbing | Elitist generational + Roulette | 1.559 / 1.474 | no | 13/30 | 1.000 | 0.52 | negligible |
| 5 | Elitist generational + Roulette | Random search | 1.474 / 62.84 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 5 | Simulated annealing | Elitist generational + Roulette | 1.277 / 1.474 | yes | 17/30 | 1.000 | 0.60 | small |
| 5 | Elitist generational + SUS | Hill climbing | 1.431 / 1.559 | yes | 16/30 | 1.000 | 0.52 | negligible |
| 5 | Elitist generational + SUS | Random search | 1.431 / 62.84 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 5 | Simulated annealing | Elitist generational + SUS | 1.277 / 1.431 | yes | 17/30 | 1.000 | 0.55 | negligible |
| 5 | Elitist generational + Tournament | Hill climbing | 1.174 / 1.559 | yes | 16/30 | 1.000 | 0.58 | small |
| 5 | Elitist generational + Tournament | Random search | 1.174 / 62.84 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 5 | Elitist generational + Tournament | Simulated annealing | 1.174 / 1.277 | yes | 19/30 | 1.000 | 0.54 | negligible |
| 5 | Hill climbing | Generational + Roulette | 1.559 / 2.001 | yes | 27/30 | < 0.001 * | 0.90 | large |
| 5 | Generational + Roulette | Random search | 2.001 / 62.84 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 5 | Simulated annealing | Generational + Roulette | 1.277 / 2.001 | yes | 27/30 | < 0.001 * | 0.90 | large |
| 5 | Hill climbing | Generational + SUS | 1.559 / 1.9 | yes | 22/30 | 0.024 * | 0.77 | large |
| 5 | Generational + SUS | Random search | 1.9 / 62.84 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 5 | Simulated annealing | Generational + SUS | 1.277 / 1.9 | yes | 23/30 | 0.011 * | 0.80 | large |
| 5 | Hill climbing | Generational + Tournament | 1.559 / 1.87 | yes | 24/30 | 0.006 * | 0.80 | large |
| 5 | Generational + Tournament | Random search | 1.87 / 62.84 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 5 | Simulated annealing | Generational + Tournament | 1.277 / 1.87 | yes | 25/30 | < 0.001 * | 0.81 | large |
| 5 | Hill climbing | Steady-state + Roulette | 1.559 / 1.718 | yes | 16/30 | 1.000 | 0.61 | small |
| 5 | Hill climbing | Steady-state + SUS | 1.559 / 1.489 | no | 15/30 | 1.000 | 0.54 | negligible |
| 5 | Steady-state + Tournament | Hill climbing | 1.347 / 1.559 | yes | 15/30 | 1.000 | 0.53 | negligible |
| 5 | Steady-state + Roulette | Random search | 1.718 / 62.84 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 5 | Steady-state + SUS | Random search | 1.489 / 62.84 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 5 | Steady-state + Tournament | Random search | 1.347 / 62.84 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 5 | Simulated annealing | Steady-state + Roulette | 1.277 / 1.718 | yes | 19/30 | 1.000 | 0.65 | medium |
| 5 | Simulated annealing | Steady-state + SUS | 1.277 / 1.489 | yes | 17/30 | 1.000 | 0.61 | small |
| 5 | Simulated annealing | Steady-state + Tournament | 1.277 / 1.347 | no | 16/30 | 1.000 | 0.54 | negligible |
| 10 | Hill climbing | Elitist generational + Roulette | 1.527 / 1.574 | no | 20/30 | 0.359 | 0.62 | small |
| 10 | Elitist generational + Roulette | Random search | 1.574 / 62.84 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 10 | Simulated annealing | Elitist generational + Roulette | 1.494 / 1.574 | no | 19/30 | 0.177 | 0.62 | small |
| 10 | Hill climbing | Elitist generational + SUS | 1.527 / 1.73 | yes | 21/30 | 0.098 | 0.67 | medium |
| 10 | Elitist generational + SUS | Random search | 1.73 / 62.84 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 10 | Simulated annealing | Elitist generational + SUS | 1.494 / 1.73 | yes | 20/30 | 0.175 | 0.67 | medium |
| 10 | Hill climbing | Elitist generational + Tournament | 1.527 / 1.601 | no | 13/30 | 0.637 | 0.58 | small |
| 10 | Elitist generational + Tournament | Random search | 1.601 / 62.84 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 10 | Simulated annealing | Elitist generational + Tournament | 1.494 / 1.601 | yes | 17/30 | 0.595 | 0.60 | small |
| 10 | Hill climbing | Generational + Roulette | 1.527 / 2.059 | yes | 27/30 | < 0.001 * | 0.85 | large |
| 10 | Generational + Roulette | Random search | 2.059 / 62.84 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 10 | Simulated annealing | Generational + Roulette | 1.494 / 2.059 | yes | 27/30 | < 0.001 * | 0.85 | large |
| 10 | Hill climbing | Generational + SUS | 1.527 / 1.952 | yes | 23/30 | < 0.001 * | 0.81 | large |
| 10 | Generational + SUS | Random search | 1.952 / 62.84 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 10 | Simulated annealing | Generational + SUS | 1.494 / 1.952 | yes | 24/30 | 0.003 * | 0.81 | large |
| 10 | Hill climbing | Generational + Tournament | 1.527 / 1.99 | yes | 24/30 | < 0.001 * | 0.82 | large |
| 10 | Generational + Tournament | Random search | 1.99 / 62.84 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 10 | Simulated annealing | Generational + Tournament | 1.494 / 1.99 | yes | 22/30 | 0.004 * | 0.81 | large |
| 10 | Hill climbing | Steady-state + Roulette | 1.527 / 1.766 | yes | 19/30 | 0.467 | 0.66 | medium |
| 10 | Hill climbing | Steady-state + SUS | 1.527 / 1.593 | no | 16/30 | 0.637 | 0.61 | small |
| 10 | Hill climbing | Steady-state + Tournament | 1.527 / 1.797 | yes | 18/30 | 0.595 | 0.64 | medium |
| 10 | Steady-state + Roulette | Random search | 1.766 / 62.84 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 10 | Steady-state + SUS | Random search | 1.593 / 62.84 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 10 | Steady-state + Tournament | Random search | 1.797 / 62.84 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 10 | Simulated annealing | Steady-state + Roulette | 1.494 / 1.766 | yes | 22/30 | 0.117 | 0.67 | medium |
| 10 | Simulated annealing | Steady-state + SUS | 1.494 / 1.593 | yes | 18/30 | 0.595 | 0.61 | small |
| 10 | Simulated annealing | Steady-state + Tournament | 1.494 / 1.797 | yes | 19/30 | 0.467 | 0.62 | small |

## Claims you can make

Significant after Holm, A12 at least small, and median gap above the noise floor.

- Mutation 1: Elitist generational reached a lower re-evaluated error than Steady-state (median 1.903 vs 2.071; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.030; A12 = 0.65, medium).
- Mutation 1: SUS reached a lower re-evaluated error than Tournament (median 1.828 vs 2.021; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.034; A12 = 0.64, medium).
- Mutation 1: SUS reached a lower re-evaluated error than Roulette (median 1.885 vs 2.069; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.001; A12 = 0.69, medium).
- Mutation 1: Elitist generational + Roulette reached a lower re-evaluated error than Random search (median 1.94 vs 62.84; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 1: Elitist generational + SUS reached a lower re-evaluated error than Random search (median 1.828 vs 62.84; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 1: Elitist generational + Tournament reached a lower re-evaluated error than Random search (median 2.021 vs 62.84; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 1: Generational + Roulette reached a lower re-evaluated error than Random search (median 2.069 vs 62.84; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 1: Generational + SUS reached a lower re-evaluated error than Random search (median 1.885 vs 62.84; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 1: Generational + Tournament reached a lower re-evaluated error than Random search (median 2.01 vs 62.84; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 1: Steady-state + Roulette reached a lower re-evaluated error than Random search (median 2.008 vs 62.84; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 1: Steady-state + SUS reached a lower re-evaluated error than Random search (median 2.072 vs 62.84; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 1: Steady-state + Tournament reached a lower re-evaluated error than Random search (median 2.032 vs 62.84; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 3: Steady-state reached a lower re-evaluated error than Generational (median 1.288 vs 1.761; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.89, large).
- Mutation 3: Elitist generational reached a lower re-evaluated error than Generational (median 1.442 vs 1.761; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.80, large).
- Mutation 3: Elitist generational + Roulette reached a lower re-evaluated error than Hill climbing (median 1.363 vs 1.78; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.001; A12 = 0.77, large).
- Mutation 3: Elitist generational + Roulette reached a lower re-evaluated error than Random search (median 1.363 vs 62.84; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 3: Elitist generational + SUS reached a lower re-evaluated error than Hill climbing (median 1.479 vs 1.78; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.015; A12 = 0.72, large).
- Mutation 3: Elitist generational + SUS reached a lower re-evaluated error than Random search (median 1.479 vs 62.84; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 3: Elitist generational + Tournament reached a lower re-evaluated error than Hill climbing (median 1.423 vs 1.78; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.036; A12 = 0.73, large).
- Mutation 3: Elitist generational + Tournament reached a lower re-evaluated error than Random search (median 1.423 vs 62.84; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 3: Generational + Roulette reached a lower re-evaluated error than Random search (median 1.907 vs 62.84; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 3: Simulated annealing reached a lower re-evaluated error than Generational + Roulette (median 1.532 vs 1.907; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.001; A12 = 0.80, large).
- Mutation 3: Generational + SUS reached a lower re-evaluated error than Random search (median 1.729 vs 62.84; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 3: Simulated annealing reached a lower re-evaluated error than Generational + SUS (median 1.532 vs 1.729; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.048; A12 = 0.67, medium).
- Mutation 3: Generational + Tournament reached a lower re-evaluated error than Random search (median 1.706 vs 62.84; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 3: Steady-state + Roulette reached a lower re-evaluated error than Hill climbing (median 1.356 vs 1.78; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.004; A12 = 0.80, large).
- Mutation 3: Steady-state + SUS reached a lower re-evaluated error than Hill climbing (median 1.262 vs 1.78; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.83, large).
- Mutation 3: Steady-state + Tournament reached a lower re-evaluated error than Hill climbing (median 1.303 vs 1.78; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.77, large).
- Mutation 3: Steady-state + Roulette reached a lower re-evaluated error than Random search (median 1.356 vs 62.84; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 3: Steady-state + SUS reached a lower re-evaluated error than Random search (median 1.262 vs 62.84; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 3: Steady-state + Tournament reached a lower re-evaluated error than Random search (median 1.303 vs 62.84; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 5: Elitist generational reached a lower re-evaluated error than Steady-state (median 1.289 vs 1.568; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.009; A12 = 0.65, medium).
- Mutation 5: Steady-state reached a lower re-evaluated error than Generational (median 1.568 vs 1.949; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.82, large).
- Mutation 5: Elitist generational reached a lower re-evaluated error than Generational (median 1.289 vs 1.949; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.94, large).
- Mutation 5: Tournament reached a lower re-evaluated error than Roulette (median 1.87 vs 2.001; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.013; A12 = 0.69, medium).
- Mutation 5: Elitist generational + Roulette reached a lower re-evaluated error than Random search (median 1.474 vs 62.84; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 5: Elitist generational + SUS reached a lower re-evaluated error than Random search (median 1.431 vs 62.84; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 5: Elitist generational + Tournament reached a lower re-evaluated error than Random search (median 1.174 vs 62.84; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 5: Hill climbing reached a lower re-evaluated error than Generational + Roulette (median 1.559 vs 2.001; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.90, large).
- Mutation 5: Generational + Roulette reached a lower re-evaluated error than Random search (median 2.001 vs 62.84; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 5: Simulated annealing reached a lower re-evaluated error than Generational + Roulette (median 1.277 vs 2.001; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.90, large).
- Mutation 5: Hill climbing reached a lower re-evaluated error than Generational + SUS (median 1.559 vs 1.9; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.024; A12 = 0.77, large).
- Mutation 5: Generational + SUS reached a lower re-evaluated error than Random search (median 1.9 vs 62.84; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 5: Simulated annealing reached a lower re-evaluated error than Generational + SUS (median 1.277 vs 1.9; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.011; A12 = 0.80, large).
- Mutation 5: Hill climbing reached a lower re-evaluated error than Generational + Tournament (median 1.559 vs 1.87; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.006; A12 = 0.80, large).
- Mutation 5: Generational + Tournament reached a lower re-evaluated error than Random search (median 1.87 vs 62.84; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 5: Simulated annealing reached a lower re-evaluated error than Generational + Tournament (median 1.277 vs 1.87; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.81, large).
- Mutation 5: Steady-state + Roulette reached a lower re-evaluated error than Random search (median 1.718 vs 62.84; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 5: Steady-state + SUS reached a lower re-evaluated error than Random search (median 1.489 vs 62.84; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 5: Steady-state + Tournament reached a lower re-evaluated error than Random search (median 1.347 vs 62.84; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 10: Steady-state reached a lower re-evaluated error than Generational (median 1.72 vs 1.999; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.83, large).
- Mutation 10: Elitist generational reached a lower re-evaluated error than Generational (median 1.673 vs 1.999; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.85, large).
- Mutation 10: Elitist generational + Roulette reached a lower re-evaluated error than Random search (median 1.574 vs 62.84; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 10: Elitist generational + SUS reached a lower re-evaluated error than Random search (median 1.73 vs 62.84; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 10: Elitist generational + Tournament reached a lower re-evaluated error than Random search (median 1.601 vs 62.84; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 10: Hill climbing reached a lower re-evaluated error than Generational + Roulette (median 1.527 vs 2.059; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.85, large).
- Mutation 10: Generational + Roulette reached a lower re-evaluated error than Random search (median 2.059 vs 62.84; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 10: Simulated annealing reached a lower re-evaluated error than Generational + Roulette (median 1.494 vs 2.059; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.85, large).
- Mutation 10: Hill climbing reached a lower re-evaluated error than Generational + SUS (median 1.527 vs 1.952; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.81, large).
- Mutation 10: Generational + SUS reached a lower re-evaluated error than Random search (median 1.952 vs 62.84; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 10: Simulated annealing reached a lower re-evaluated error than Generational + SUS (median 1.494 vs 1.952; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.003; A12 = 0.81, large).
- Mutation 10: Hill climbing reached a lower re-evaluated error than Generational + Tournament (median 1.527 vs 1.99; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.82, large).
- Mutation 10: Generational + Tournament reached a lower re-evaluated error than Random search (median 1.99 vs 62.84; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 10: Simulated annealing reached a lower re-evaluated error than Generational + Tournament (median 1.494 vs 1.99; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.004; A12 = 0.81, large).
- Mutation 10: Steady-state + Roulette reached a lower re-evaluated error than Random search (median 1.766 vs 62.84; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 10: Steady-state + SUS reached a lower re-evaluated error than Random search (median 1.593 vs 62.84; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 10: Steady-state + Tournament reached a lower re-evaluated error than Random search (median 1.797 vs 62.84; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
