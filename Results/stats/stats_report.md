# Statistical tests (re-evaluated error, lower is better)

## Re-evaluation

Each run's final best reelset was measured again on a simulator seed the run never used (100,000,000 spins). Sources: 1440 runs from final check (optimizer).

In-run final best vs re-evaluated error (median over seeds). The in-run value is the lowest of many noisy measurements, so it is biased low; the ratio shows how much.

| Mutation | Method | In-run final best | Re-evaluated | Re-evaluated / in-run |
|---|---|---|---|---|
| 1 | Elitist generational + Roulette | 0.142 | 0.1548 | 1.09 |
| 1 | Elitist generational + SUS | 0.1301 | 0.1351 | 1.04 |
| 1 | Elitist generational + Tournament | 0.1606 | 0.1765 | 1.10 |
| 1 | Generational + Roulette | 0.2538 | 0.2515 | 0.99 |
| 1 | Generational + SUS | 0.1662 | 0.1732 | 1.04 |
| 1 | Generational + Tournament | 0.1593 | 0.169 | 1.06 |
| 1 | Hill climbing | 0.1445 | 0.1598 | 1.11 |
| 1 | Random search | 37.51 | 37.52 | 1.00 |
| 1 | Simulated annealing | 0.1683 | 0.1922 | 1.14 |
| 1 | Steady-state + Roulette | 0.1492 | 0.1628 | 1.09 |
| 1 | Steady-state + SUS | 0.1332 | 0.1404 | 1.05 |
| 1 | Steady-state + Tournament | 0.04656 | 0.07578 | 1.63 |
| 3 | Elitist generational + Roulette | 0.08075 | 0.08569 | 1.06 |
| 3 | Elitist generational + SUS | 0.1475 | 0.151 | 1.02 |
| 3 | Elitist generational + Tournament | 0.1129 | 0.1191 | 1.05 |
| 3 | Generational + Roulette | 0.3404 | 0.349 | 1.03 |
| 3 | Generational + SUS | 0.2427 | 0.2345 | 0.97 |
| 3 | Generational + Tournament | 0.1537 | 0.158 | 1.03 |
| 3 | Hill climbing | 0.11 | 0.1185 | 1.08 |
| 3 | Random search | 37.51 | 37.52 | 1.00 |
| 3 | Simulated annealing | 0.1175 | 0.1302 | 1.11 |
| 3 | Steady-state + Roulette | 0.1383 | 0.1372 | 0.99 |
| 3 | Steady-state + SUS | 0.1372 | 0.1527 | 1.11 |
| 3 | Steady-state + Tournament | 0.1207 | 0.1144 | 0.95 |
| 5 | Elitist generational + Roulette | 0.128 | 0.1323 | 1.03 |
| 5 | Elitist generational + SUS | 0.139 | 0.1476 | 1.06 |
| 5 | Elitist generational + Tournament | 0.1185 | 0.1 | 0.84 |
| 5 | Generational + Roulette | 0.4268 | 0.4445 | 1.04 |
| 5 | Generational + SUS | 0.3283 | 0.3331 | 1.01 |
| 5 | Generational + Tournament | 0.202 | 0.2092 | 1.04 |
| 5 | Hill climbing | 0.07202 | 0.08424 | 1.17 |
| 5 | Random search | 37.51 | 37.52 | 1.00 |
| 5 | Simulated annealing | 0.06486 | 0.07481 | 1.15 |
| 5 | Steady-state + Roulette | 0.1391 | 0.1502 | 1.08 |
| 5 | Steady-state + SUS | 0.09664 | 0.09062 | 0.94 |
| 5 | Steady-state + Tournament | 0.07198 | 0.08964 | 1.25 |
| 10 | Elitist generational + Roulette | 0.2685 | 0.2688 | 1.00 |
| 10 | Elitist generational + SUS | 0.2147 | 0.2215 | 1.03 |
| 10 | Elitist generational + Tournament | 0.2076 | 0.2098 | 1.01 |
| 10 | Generational + Roulette | 1.559 | 1.555 | 1.00 |
| 10 | Generational + SUS | 0.8057 | 0.83 | 1.03 |
| 10 | Generational + Tournament | 0.5202 | 0.522 | 1.00 |
| 10 | Hill climbing | 0.1096 | 0.1284 | 1.17 |
| 10 | Random search | 37.51 | 37.52 | 1.00 |
| 10 | Simulated annealing | 0.1456 | 0.1551 | 1.07 |
| 10 | Steady-state + Roulette | 0.1915 | 0.2061 | 1.08 |
| 10 | Steady-state + SUS | 0.1708 | 0.1691 | 0.99 |
| 10 | Steady-state + Tournament | 0.1373 | 0.139 | 1.01 |

Paired by seed. Friedman omnibus test, then two-sided Wilcoxon signed-rank tests with Holm correction within each family; alpha = 0.05. Effect size = Vargha-Delaney A12 (probability the better method reaches a lower value on a run; 0.5 = no difference).
Noise floor = 0.02978: the smallest gap two independent re-evaluated error measurements can resolve at 95% (2.77 x simulator SD at the spins used).

## Omnibus tests (Friedman)

| Family | Mutation | Seeds | Methods | chi2 | p | Kendall's W |
|---|---|---|---|---|---|---|
| strategy | 1 | 30 | 3 | 4.47 | 0.107 | 0.07 |
| selection (Steady-state) | 1 | 30 | 3 | 0.07 | 0.967 | 0.00 |
| selection (Elitist generational) | 1 | 30 | 3 | 4.87 | 0.088 | 0.08 |
| selection (Generational) | 1 | 30 | 3 | 9.80 | 0.007 | 0.16 |
| ga_vs_baselines | 1 | 30 | 12 | 98.94 | < 0.001 | 0.30 |
| all (exploratory) | 1 | 30 | 12 | 98.94 | < 0.001 | 0.30 |
| strategy | 3 | 30 | 3 | 14.60 | < 0.001 | 0.24 |
| selection (Steady-state) | 3 | 30 | 3 | 2.47 | 0.291 | 0.04 |
| selection (Elitist generational) | 3 | 30 | 3 | 7.27 | 0.026 | 0.12 |
| selection (Generational) | 3 | 30 | 3 | 21.07 | < 0.001 | 0.35 |
| ga_vs_baselines | 3 | 30 | 12 | 136.22 | < 0.001 | 0.41 |
| all (exploratory) | 3 | 30 | 12 | 136.22 | < 0.001 | 0.41 |
| strategy | 5 | 30 | 3 | 29.40 | < 0.001 | 0.49 |
| selection (Steady-state) | 5 | 30 | 3 | 1.27 | 0.531 | 0.02 |
| selection (Elitist generational) | 5 | 30 | 3 | 0.47 | 0.792 | 0.01 |
| selection (Generational) | 5 | 30 | 3 | 16.07 | < 0.001 | 0.27 |
| ga_vs_baselines | 5 | 30 | 12 | 172.69 | < 0.001 | 0.52 |
| all (exploratory) | 5 | 30 | 12 | 172.69 | < 0.001 | 0.52 |
| strategy | 10 | 30 | 3 | 47.40 | < 0.001 | 0.79 |
| selection (Steady-state) | 10 | 30 | 3 | 1.27 | 0.531 | 0.02 |
| selection (Elitist generational) | 10 | 30 | 3 | 4.47 | 0.107 | 0.07 |
| selection (Generational) | 10 | 30 | 3 | 18.20 | < 0.001 | 0.30 |
| ga_vs_baselines | 10 | 30 | 12 | 233.41 | < 0.001 | 0.71 |
| all (exploratory) | 10 | 30 | 12 | 233.41 | < 0.001 | 0.71 |

## strategy

| Mutation | Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|---|
| 1 | Steady-state | Elitist generational | 0.1451 / 0.1633 | no | 17/30 | 0.371 | 0.58 | small |
| 1 | Steady-state | Generational | 0.1451 / 0.1851 | yes | 20/30 | 0.044 * | 0.72 | large |
| 1 | Elitist generational | Generational | 0.1633 / 0.1851 | no | 19/30 | 0.110 | 0.67 | medium |
| 3 | Elitist generational | Steady-state | 0.1119 / 0.1443 | yes | 15/30 | 0.556 | 0.56 | negligible |
| 3 | Steady-state | Generational | 0.1443 / 0.214 | yes | 22/30 | < 0.001 * | 0.82 | large |
| 3 | Elitist generational | Generational | 0.1119 / 0.214 | yes | 25/30 | < 0.001 * | 0.86 | large |
| 5 | Steady-state | Elitist generational | 0.1442 / 0.1377 | no | 17/30 | 0.382 | 0.56 | small |
| 5 | Steady-state | Generational | 0.1442 / 0.3327 | yes | 28/30 | < 0.001 * | 0.96 | large |
| 5 | Elitist generational | Generational | 0.1377 / 0.3327 | yes | 26/30 | < 0.001 * | 0.94 | large |
| 10 | Steady-state | Elitist generational | 0.1618 / 0.2242 | yes | 21/30 | 0.007 * | 0.72 | large |
| 10 | Steady-state | Generational | 0.1618 / 0.7072 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 10 | Elitist generational | Generational | 0.2242 / 0.7072 | yes | 30/30 | < 0.001 * | 1.00 | large |

## selection (Steady-state)

| Mutation | Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|---|
| 1 | SUS | Roulette | 0.1404 / 0.1628 | no | 16/30 | 1.000 | 0.55 | negligible |
| 1 | Tournament | Roulette | 0.07578 / 0.1628 | yes | 15/30 | 1.000 | 0.57 | small |
| 1 | Tournament | SUS | 0.07578 / 0.1404 | yes | 15/30 | 1.000 | 0.54 | negligible |
| 3 | SUS | Roulette | 0.1527 / 0.1372 | no | 15/30 | 0.935 | 0.50 | negligible |
| 3 | Tournament | Roulette | 0.1144 / 0.1372 | no | 19/30 | 0.662 | 0.56 | small |
| 3 | Tournament | SUS | 0.1144 / 0.1527 | yes | 18/30 | 0.741 | 0.58 | small |
| 5 | SUS | Roulette | 0.09062 / 0.1502 | yes | 18/30 | 0.639 | 0.62 | small |
| 5 | Tournament | Roulette | 0.08964 / 0.1502 | yes | 17/30 | 0.880 | 0.59 | small |
| 5 | SUS | Tournament | 0.09062 / 0.08964 | no | 15/30 | 0.880 | 0.53 | negligible |
| 10 | SUS | Roulette | 0.1691 / 0.2061 | yes | 17/30 | 0.955 | 0.55 | negligible |
| 10 | Tournament | Roulette | 0.139 / 0.2061 | yes | 16/30 | 0.955 | 0.60 | small |
| 10 | Tournament | SUS | 0.139 / 0.1691 | yes | 19/30 | 0.955 | 0.60 | small |

## selection (Elitist generational)

| Mutation | Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|---|
| 1 | SUS | Roulette | 0.1351 / 0.1548 | no | 18/30 | 0.746 | 0.52 | negligible |
| 1 | Roulette | Tournament | 0.1548 / 0.1765 | no | 19/30 | 0.637 | 0.57 | small |
| 1 | SUS | Tournament | 0.1351 / 0.1765 | yes | 20/30 | 0.573 | 0.59 | small |
| 3 | Roulette | SUS | 0.08569 / 0.151 | yes | 22/30 | 0.210 | 0.66 | medium |
| 3 | Roulette | Tournament | 0.08569 / 0.1191 | yes | 13/30 | 0.641 | 0.55 | negligible |
| 3 | Tournament | SUS | 0.1191 / 0.151 | yes | 20/30 | 0.457 | 0.61 | small |
| 5 | Roulette | SUS | 0.1323 / 0.1476 | no | 16/30 | 1.000 | 0.52 | negligible |
| 5 | Tournament | Roulette | 0.1 / 0.1323 | yes | 13/30 | 1.000 | 0.50 | negligible |
| 5 | Tournament | SUS | 0.1 / 0.1476 | yes | 15/30 | 1.000 | 0.52 | negligible |
| 10 | SUS | Roulette | 0.2215 / 0.2688 | yes | 19/30 | 0.105 | 0.65 | medium |
| 10 | Tournament | Roulette | 0.2098 / 0.2688 | yes | 20/30 | 0.063 | 0.67 | medium |
| 10 | Tournament | SUS | 0.2098 / 0.2215 | no | 12/30 | 0.855 | 0.53 | negligible |

## selection (Generational)

| Mutation | Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|---|
| 1 | SUS | Roulette | 0.1732 / 0.2515 | yes | 23/30 | 0.008 * | 0.70 | medium |
| 1 | Tournament | Roulette | 0.169 / 0.2515 | yes | 21/30 | 0.008 * | 0.72 | large |
| 1 | Tournament | SUS | 0.169 / 0.1732 | no | 16/30 | 0.452 | 0.52 | negligible |
| 3 | SUS | Roulette | 0.2345 / 0.349 | yes | 19/30 | 0.043 * | 0.61 | small |
| 3 | Tournament | Roulette | 0.158 / 0.349 | yes | 25/30 | < 0.001 * | 0.81 | large |
| 3 | Tournament | SUS | 0.158 / 0.2345 | yes | 25/30 | < 0.001 * | 0.78 | large |
| 5 | SUS | Roulette | 0.3331 / 0.4445 | yes | 21/30 | 0.003 * | 0.72 | large |
| 5 | Tournament | Roulette | 0.2092 / 0.4445 | yes | 25/30 | < 0.001 * | 0.88 | large |
| 5 | Tournament | SUS | 0.2092 / 0.3331 | yes | 20/30 | 0.008 * | 0.74 | large |
| 10 | SUS | Roulette | 0.83 / 1.555 | yes | 21/30 | 0.004 * | 0.70 | medium |
| 10 | Tournament | Roulette | 0.522 / 1.555 | yes | 25/30 | < 0.001 * | 0.86 | large |
| 10 | Tournament | SUS | 0.522 / 0.83 | yes | 22/30 | < 0.001 * | 0.74 | large |

## ga_vs_baselines

| Mutation | Better | Worse | Median (better / worse) | Gap > noise | Wins | p (Holm) | A12 | Effect |
|---|---|---|---|---|---|---|---|---|
| 1 | Elitist generational + Roulette | Hill climbing | 0.1548 / 0.1598 | no | 16/30 | 1.000 | 0.59 | small |
| 1 | Elitist generational + Roulette | Random search | 0.1548 / 37.52 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 1 | Elitist generational + Roulette | Simulated annealing | 0.1548 / 0.1922 | yes | 19/30 | 0.908 | 0.62 | small |
| 1 | Elitist generational + SUS | Hill climbing | 0.1351 / 0.1598 | no | 18/30 | 1.000 | 0.57 | small |
| 1 | Elitist generational + SUS | Random search | 0.1351 / 37.52 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 1 | Elitist generational + SUS | Simulated annealing | 0.1351 / 0.1922 | yes | 20/30 | 0.528 | 0.66 | medium |
| 1 | Elitist generational + Tournament | Hill climbing | 0.1765 / 0.1598 | no | 19/30 | 1.000 | 0.50 | negligible |
| 1 | Elitist generational + Tournament | Random search | 0.1765 / 37.52 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 1 | Elitist generational + Tournament | Simulated annealing | 0.1765 / 0.1922 | no | 17/30 | 1.000 | 0.57 | small |
| 1 | Hill climbing | Generational + Roulette | 0.1598 / 0.2515 | yes | 19/30 | 1.000 | 0.69 | medium |
| 1 | Generational + Roulette | Random search | 0.2515 / 37.52 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 1 | Simulated annealing | Generational + Roulette | 0.1922 / 0.2515 | yes | 20/30 | 0.756 | 0.66 | medium |
| 1 | Hill climbing | Generational + SUS | 0.1598 / 0.1732 | no | 18/30 | 1.000 | 0.55 | negligible |
| 1 | Generational + SUS | Random search | 0.1732 / 37.52 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 1 | Generational + SUS | Simulated annealing | 0.1732 / 0.1922 | no | 14/30 | 1.000 | 0.51 | negligible |
| 1 | Hill climbing | Generational + Tournament | 0.1598 / 0.169 | no | 16/30 | 1.000 | 0.51 | negligible |
| 1 | Generational + Tournament | Random search | 0.169 / 37.52 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 1 | Generational + Tournament | Simulated annealing | 0.169 / 0.1922 | no | 17/30 | 1.000 | 0.54 | negligible |
| 1 | Steady-state + Roulette | Hill climbing | 0.1628 / 0.1598 | no | 16/30 | 1.000 | 0.53 | negligible |
| 1 | Steady-state + SUS | Hill climbing | 0.1404 / 0.1598 | no | 16/30 | 1.000 | 0.56 | small |
| 1 | Steady-state + Tournament | Hill climbing | 0.07578 / 0.1598 | yes | 20/30 | 1.000 | 0.61 | small |
| 1 | Steady-state + Roulette | Random search | 0.1628 / 37.52 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 1 | Steady-state + SUS | Random search | 0.1404 / 37.52 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 1 | Steady-state + Tournament | Random search | 0.07578 / 37.52 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 1 | Steady-state + Roulette | Simulated annealing | 0.1628 / 0.1922 | no | 17/30 | 1.000 | 0.56 | negligible |
| 1 | Steady-state + SUS | Simulated annealing | 0.1404 / 0.1922 | yes | 18/30 | 1.000 | 0.63 | small |
| 1 | Steady-state + Tournament | Simulated annealing | 0.07578 / 0.1922 | yes | 21/30 | 0.528 | 0.66 | medium |
| 3 | Elitist generational + Roulette | Hill climbing | 0.08569 / 0.1185 | yes | 16/30 | 1.000 | 0.52 | negligible |
| 3 | Elitist generational + Roulette | Random search | 0.08569 / 37.52 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 3 | Elitist generational + Roulette | Simulated annealing | 0.08569 / 0.1302 | yes | 19/30 | 1.000 | 0.56 | small |
| 3 | Hill climbing | Elitist generational + SUS | 0.1185 / 0.151 | yes | 22/30 | 0.879 | 0.63 | small |
| 3 | Elitist generational + SUS | Random search | 0.151 / 37.52 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 3 | Simulated annealing | Elitist generational + SUS | 0.1302 / 0.151 | no | 18/30 | 1.000 | 0.64 | small |
| 3 | Hill climbing | Elitist generational + Tournament | 0.1185 / 0.1191 | no | 16/30 | 1.000 | 0.53 | negligible |
| 3 | Elitist generational + Tournament | Random search | 0.1191 / 37.52 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 3 | Simulated annealing | Elitist generational + Tournament | 0.1302 / 0.1191 | no | 17/30 | 1.000 | 0.50 | negligible |
| 3 | Hill climbing | Generational + Roulette | 0.1185 / 0.349 | yes | 24/30 | < 0.001 * | 0.87 | large |
| 3 | Generational + Roulette | Random search | 0.349 / 37.52 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 3 | Simulated annealing | Generational + Roulette | 0.1302 / 0.349 | yes | 27/30 | < 0.001 * | 0.89 | large |
| 3 | Hill climbing | Generational + SUS | 0.1185 / 0.2345 | yes | 26/30 | < 0.001 * | 0.84 | large |
| 3 | Generational + SUS | Random search | 0.2345 / 37.52 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 3 | Simulated annealing | Generational + SUS | 0.1302 / 0.2345 | yes | 28/30 | < 0.001 * | 0.87 | large |
| 3 | Hill climbing | Generational + Tournament | 0.1185 / 0.158 | yes | 21/30 | 0.458 | 0.65 | medium |
| 3 | Generational + Tournament | Random search | 0.158 / 37.52 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 3 | Simulated annealing | Generational + Tournament | 0.1302 / 0.158 | no | 18/30 | 0.867 | 0.65 | medium |
| 3 | Hill climbing | Steady-state + Roulette | 0.1185 / 0.1372 | no | 17/30 | 1.000 | 0.60 | small |
| 3 | Hill climbing | Steady-state + SUS | 0.1185 / 0.1527 | yes | 20/30 | 1.000 | 0.61 | small |
| 3 | Hill climbing | Steady-state + Tournament | 0.1185 / 0.1144 | no | 16/30 | 1.000 | 0.53 | negligible |
| 3 | Steady-state + Roulette | Random search | 0.1372 / 37.52 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 3 | Steady-state + SUS | Random search | 0.1527 / 37.52 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 3 | Steady-state + Tournament | Random search | 0.1144 / 37.52 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 3 | Simulated annealing | Steady-state + Roulette | 0.1302 / 0.1372 | no | 19/30 | 1.000 | 0.56 | small |
| 3 | Simulated annealing | Steady-state + SUS | 0.1302 / 0.1527 | no | 18/30 | 1.000 | 0.59 | small |
| 3 | Steady-state + Tournament | Simulated annealing | 0.1144 / 0.1302 | no | 14/30 | 1.000 | 0.50 | negligible |
| 5 | Hill climbing | Elitist generational + Roulette | 0.08424 / 0.1323 | yes | 15/30 | 1.000 | 0.60 | small |
| 5 | Elitist generational + Roulette | Random search | 0.1323 / 37.52 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 5 | Simulated annealing | Elitist generational + Roulette | 0.07481 / 0.1323 | yes | 21/30 | 1.000 | 0.63 | small |
| 5 | Hill climbing | Elitist generational + SUS | 0.08424 / 0.1476 | yes | 18/30 | 1.000 | 0.63 | small |
| 5 | Elitist generational + SUS | Random search | 0.1476 / 37.52 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 5 | Simulated annealing | Elitist generational + SUS | 0.07481 / 0.1476 | yes | 17/30 | 1.000 | 0.65 | medium |
| 5 | Hill climbing | Elitist generational + Tournament | 0.08424 / 0.1 | no | 18/30 | 1.000 | 0.59 | small |
| 5 | Elitist generational + Tournament | Random search | 0.1 / 37.52 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 5 | Simulated annealing | Elitist generational + Tournament | 0.07481 / 0.1 | no | 19/30 | 1.000 | 0.61 | small |
| 5 | Hill climbing | Generational + Roulette | 0.08424 / 0.4445 | yes | 30/30 | < 0.001 * | 0.97 | large |
| 5 | Generational + Roulette | Random search | 0.4445 / 37.52 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 5 | Simulated annealing | Generational + Roulette | 0.07481 / 0.4445 | yes | 28/30 | < 0.001 * | 0.98 | large |
| 5 | Hill climbing | Generational + SUS | 0.08424 / 0.3331 | yes | 26/30 | < 0.001 * | 0.91 | large |
| 5 | Generational + SUS | Random search | 0.3331 / 37.52 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 5 | Simulated annealing | Generational + SUS | 0.07481 / 0.3331 | yes | 29/30 | < 0.001 * | 0.92 | large |
| 5 | Hill climbing | Generational + Tournament | 0.08424 / 0.2092 | yes | 24/30 | < 0.001 * | 0.80 | large |
| 5 | Generational + Tournament | Random search | 0.2092 / 37.52 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 5 | Simulated annealing | Generational + Tournament | 0.07481 / 0.2092 | yes | 25/30 | < 0.001 * | 0.82 | large |
| 5 | Hill climbing | Steady-state + Roulette | 0.08424 / 0.1502 | yes | 19/30 | 1.000 | 0.61 | small |
| 5 | Steady-state + SUS | Hill climbing | 0.09062 / 0.08424 | no | 16/30 | 1.000 | 0.52 | negligible |
| 5 | Steady-state + Tournament | Hill climbing | 0.08964 / 0.08424 | no | 16/30 | 1.000 | 0.50 | negligible |
| 5 | Steady-state + Roulette | Random search | 0.1502 / 37.52 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 5 | Steady-state + SUS | Random search | 0.09062 / 37.52 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 5 | Steady-state + Tournament | Random search | 0.08964 / 37.52 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 5 | Simulated annealing | Steady-state + Roulette | 0.07481 / 0.1502 | yes | 19/30 | 1.000 | 0.63 | small |
| 5 | Simulated annealing | Steady-state + SUS | 0.07481 / 0.09062 | no | 15/30 | 1.000 | 0.51 | negligible |
| 5 | Simulated annealing | Steady-state + Tournament | 0.07481 / 0.08964 | no | 16/30 | 1.000 | 0.53 | negligible |
| 10 | Hill climbing | Elitist generational + Roulette | 0.1284 / 0.2688 | yes | 26/30 | < 0.001 * | 0.87 | large |
| 10 | Elitist generational + Roulette | Random search | 0.2688 / 37.52 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 10 | Simulated annealing | Elitist generational + Roulette | 0.1551 / 0.2688 | yes | 25/30 | < 0.001 * | 0.82 | large |
| 10 | Hill climbing | Elitist generational + SUS | 0.1284 / 0.2215 | yes | 23/30 | 0.001 * | 0.78 | large |
| 10 | Elitist generational + SUS | Random search | 0.2215 / 37.52 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 10 | Simulated annealing | Elitist generational + SUS | 0.1551 / 0.2215 | yes | 20/30 | 0.077 | 0.72 | large |
| 10 | Hill climbing | Elitist generational + Tournament | 0.1284 / 0.2098 | yes | 19/30 | 0.057 | 0.74 | large |
| 10 | Elitist generational + Tournament | Random search | 0.2098 / 37.52 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 10 | Simulated annealing | Elitist generational + Tournament | 0.1551 / 0.2098 | yes | 20/30 | 0.139 | 0.67 | medium |
| 10 | Hill climbing | Generational + Roulette | 0.1284 / 1.555 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 10 | Generational + Roulette | Random search | 1.555 / 37.52 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 10 | Simulated annealing | Generational + Roulette | 0.1551 / 1.555 | yes | 30/30 | < 0.001 * | 0.99 | large |
| 10 | Hill climbing | Generational + SUS | 0.1284 / 0.83 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 10 | Generational + SUS | Random search | 0.83 / 37.52 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 10 | Simulated annealing | Generational + SUS | 0.1551 / 0.83 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 10 | Hill climbing | Generational + Tournament | 0.1284 / 0.522 | yes | 30/30 | < 0.001 * | 0.98 | large |
| 10 | Generational + Tournament | Random search | 0.522 / 37.52 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 10 | Simulated annealing | Generational + Tournament | 0.1551 / 0.522 | yes | 30/30 | < 0.001 * | 0.96 | large |
| 10 | Hill climbing | Steady-state + Roulette | 0.1284 / 0.2061 | yes | 20/30 | 0.070 | 0.71 | medium |
| 10 | Hill climbing | Steady-state + SUS | 0.1284 / 0.1691 | yes | 21/30 | 0.039 * | 0.70 | medium |
| 10 | Hill climbing | Steady-state + Tournament | 0.1284 / 0.139 | no | 19/30 | 0.382 | 0.59 | small |
| 10 | Steady-state + Roulette | Random search | 0.2061 / 37.52 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 10 | Steady-state + SUS | Random search | 0.1691 / 37.52 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 10 | Steady-state + Tournament | Random search | 0.139 / 37.52 | yes | 30/30 | < 0.001 * | 1.00 | large |
| 10 | Simulated annealing | Steady-state + Roulette | 0.1551 / 0.2061 | yes | 17/30 | 0.267 | 0.64 | small |
| 10 | Simulated annealing | Steady-state + SUS | 0.1551 / 0.1691 | no | 19/30 | 0.267 | 0.58 | small |
| 10 | Simulated annealing | Steady-state + Tournament | 0.1551 / 0.139 | no | 16/30 | 0.792 | 0.50 | negligible |

## Claims you can make

Significant after Holm, A12 at least small, and median gap above the noise floor.

- Mutation 1: Steady-state reached a lower re-evaluated error than Generational (median 0.1451 vs 0.1851; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.044; A12 = 0.72, large).
- Mutation 1: SUS reached a lower re-evaluated error than Roulette (median 0.1732 vs 0.2515; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.008; A12 = 0.70, medium).
- Mutation 1: Tournament reached a lower re-evaluated error than Roulette (median 0.169 vs 0.2515; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.008; A12 = 0.72, large).
- Mutation 1: Elitist generational + Roulette reached a lower re-evaluated error than Random search (median 0.1548 vs 37.52; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 1: Elitist generational + SUS reached a lower re-evaluated error than Random search (median 0.1351 vs 37.52; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 1: Elitist generational + Tournament reached a lower re-evaluated error than Random search (median 0.1765 vs 37.52; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 1: Generational + Roulette reached a lower re-evaluated error than Random search (median 0.2515 vs 37.52; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 1: Generational + SUS reached a lower re-evaluated error than Random search (median 0.1732 vs 37.52; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 1: Generational + Tournament reached a lower re-evaluated error than Random search (median 0.169 vs 37.52; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 1: Steady-state + Roulette reached a lower re-evaluated error than Random search (median 0.1628 vs 37.52; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 1: Steady-state + SUS reached a lower re-evaluated error than Random search (median 0.1404 vs 37.52; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 1: Steady-state + Tournament reached a lower re-evaluated error than Random search (median 0.07578 vs 37.52; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 3: Steady-state reached a lower re-evaluated error than Generational (median 0.1443 vs 0.214; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.82, large).
- Mutation 3: Elitist generational reached a lower re-evaluated error than Generational (median 0.1119 vs 0.214; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.86, large).
- Mutation 3: SUS reached a lower re-evaluated error than Roulette (median 0.2345 vs 0.349; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.043; A12 = 0.61, small).
- Mutation 3: Tournament reached a lower re-evaluated error than Roulette (median 0.158 vs 0.349; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.81, large).
- Mutation 3: Tournament reached a lower re-evaluated error than SUS (median 0.158 vs 0.2345; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.78, large).
- Mutation 3: Elitist generational + Roulette reached a lower re-evaluated error than Random search (median 0.08569 vs 37.52; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 3: Elitist generational + SUS reached a lower re-evaluated error than Random search (median 0.151 vs 37.52; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 3: Elitist generational + Tournament reached a lower re-evaluated error than Random search (median 0.1191 vs 37.52; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 3: Hill climbing reached a lower re-evaluated error than Generational + Roulette (median 0.1185 vs 0.349; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.87, large).
- Mutation 3: Generational + Roulette reached a lower re-evaluated error than Random search (median 0.349 vs 37.52; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 3: Simulated annealing reached a lower re-evaluated error than Generational + Roulette (median 0.1302 vs 0.349; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.89, large).
- Mutation 3: Hill climbing reached a lower re-evaluated error than Generational + SUS (median 0.1185 vs 0.2345; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.84, large).
- Mutation 3: Generational + SUS reached a lower re-evaluated error than Random search (median 0.2345 vs 37.52; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 3: Simulated annealing reached a lower re-evaluated error than Generational + SUS (median 0.1302 vs 0.2345; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.87, large).
- Mutation 3: Generational + Tournament reached a lower re-evaluated error than Random search (median 0.158 vs 37.52; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 3: Steady-state + Roulette reached a lower re-evaluated error than Random search (median 0.1372 vs 37.52; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 3: Steady-state + SUS reached a lower re-evaluated error than Random search (median 0.1527 vs 37.52; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 3: Steady-state + Tournament reached a lower re-evaluated error than Random search (median 0.1144 vs 37.52; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 5: Steady-state reached a lower re-evaluated error than Generational (median 0.1442 vs 0.3327; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.96, large).
- Mutation 5: Elitist generational reached a lower re-evaluated error than Generational (median 0.1377 vs 0.3327; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.94, large).
- Mutation 5: SUS reached a lower re-evaluated error than Roulette (median 0.3331 vs 0.4445; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.003; A12 = 0.72, large).
- Mutation 5: Tournament reached a lower re-evaluated error than Roulette (median 0.2092 vs 0.4445; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.88, large).
- Mutation 5: Tournament reached a lower re-evaluated error than SUS (median 0.2092 vs 0.3331; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.008; A12 = 0.74, large).
- Mutation 5: Elitist generational + Roulette reached a lower re-evaluated error than Random search (median 0.1323 vs 37.52; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 5: Elitist generational + SUS reached a lower re-evaluated error than Random search (median 0.1476 vs 37.52; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 5: Elitist generational + Tournament reached a lower re-evaluated error than Random search (median 0.1 vs 37.52; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 5: Hill climbing reached a lower re-evaluated error than Generational + Roulette (median 0.08424 vs 0.4445; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.97, large).
- Mutation 5: Generational + Roulette reached a lower re-evaluated error than Random search (median 0.4445 vs 37.52; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 5: Simulated annealing reached a lower re-evaluated error than Generational + Roulette (median 0.07481 vs 0.4445; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.98, large).
- Mutation 5: Hill climbing reached a lower re-evaluated error than Generational + SUS (median 0.08424 vs 0.3331; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.91, large).
- Mutation 5: Generational + SUS reached a lower re-evaluated error than Random search (median 0.3331 vs 37.52; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 5: Simulated annealing reached a lower re-evaluated error than Generational + SUS (median 0.07481 vs 0.3331; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.92, large).
- Mutation 5: Hill climbing reached a lower re-evaluated error than Generational + Tournament (median 0.08424 vs 0.2092; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.80, large).
- Mutation 5: Generational + Tournament reached a lower re-evaluated error than Random search (median 0.2092 vs 37.52; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 5: Simulated annealing reached a lower re-evaluated error than Generational + Tournament (median 0.07481 vs 0.2092; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.82, large).
- Mutation 5: Steady-state + Roulette reached a lower re-evaluated error than Random search (median 0.1502 vs 37.52; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 5: Steady-state + SUS reached a lower re-evaluated error than Random search (median 0.09062 vs 37.52; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 5: Steady-state + Tournament reached a lower re-evaluated error than Random search (median 0.08964 vs 37.52; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 10: Steady-state reached a lower re-evaluated error than Elitist generational (median 0.1618 vs 0.2242; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.007; A12 = 0.72, large).
- Mutation 10: Steady-state reached a lower re-evaluated error than Generational (median 0.1618 vs 0.7072; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 10: Elitist generational reached a lower re-evaluated error than Generational (median 0.2242 vs 0.7072; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 10: SUS reached a lower re-evaluated error than Roulette (median 0.83 vs 1.555; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.004; A12 = 0.70, medium).
- Mutation 10: Tournament reached a lower re-evaluated error than Roulette (median 0.522 vs 1.555; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.86, large).
- Mutation 10: Tournament reached a lower re-evaluated error than SUS (median 0.522 vs 0.83; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.74, large).
- Mutation 10: Hill climbing reached a lower re-evaluated error than Elitist generational + Roulette (median 0.1284 vs 0.2688; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.87, large).
- Mutation 10: Elitist generational + Roulette reached a lower re-evaluated error than Random search (median 0.2688 vs 37.52; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 10: Simulated annealing reached a lower re-evaluated error than Elitist generational + Roulette (median 0.1551 vs 0.2688; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.82, large).
- Mutation 10: Hill climbing reached a lower re-evaluated error than Elitist generational + SUS (median 0.1284 vs 0.2215; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.001; A12 = 0.78, large).
- Mutation 10: Elitist generational + SUS reached a lower re-evaluated error than Random search (median 0.2215 vs 37.52; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 10: Elitist generational + Tournament reached a lower re-evaluated error than Random search (median 0.2098 vs 37.52; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 10: Hill climbing reached a lower re-evaluated error than Generational + Roulette (median 0.1284 vs 1.555; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 10: Generational + Roulette reached a lower re-evaluated error than Random search (median 1.555 vs 37.52; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 10: Simulated annealing reached a lower re-evaluated error than Generational + Roulette (median 0.1551 vs 1.555; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.99, large).
- Mutation 10: Hill climbing reached a lower re-evaluated error than Generational + SUS (median 0.1284 vs 0.83; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 10: Generational + SUS reached a lower re-evaluated error than Random search (median 0.83 vs 37.52; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 10: Simulated annealing reached a lower re-evaluated error than Generational + SUS (median 0.1551 vs 0.83; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 10: Hill climbing reached a lower re-evaluated error than Generational + Tournament (median 0.1284 vs 0.522; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.98, large).
- Mutation 10: Generational + Tournament reached a lower re-evaluated error than Random search (median 0.522 vs 37.52; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 10: Simulated annealing reached a lower re-evaluated error than Generational + Tournament (median 0.1551 vs 0.522; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 0.96, large).
- Mutation 10: Hill climbing reached a lower re-evaluated error than Steady-state + SUS (median 0.1284 vs 0.1691; Wilcoxon signed-rank, n = 30 seeds, p_Holm = 0.039; A12 = 0.70, medium).
- Mutation 10: Steady-state + Roulette reached a lower re-evaluated error than Random search (median 0.2061 vs 37.52; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 10: Steady-state + SUS reached a lower re-evaluated error than Random search (median 0.1691 vs 37.52; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
- Mutation 10: Steady-state + Tournament reached a lower re-evaluated error than Random search (median 0.139 vs 37.52; Wilcoxon signed-rank, n = 30 seeds, p_Holm < 0.001; A12 = 1.00, large).
