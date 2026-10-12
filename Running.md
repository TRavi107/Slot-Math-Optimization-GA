# Running the project

This guide takes you from a fresh computer to the full set of results and charts in the
[README](README.md). It is in three parts:

- **Part A — Set up the environment** (sections 1–4): get the simulator (download it, or
  build it), install Python and the packages, point the config at the simulator, and run a
  two-minute test.
- **Part B — Run the experiments** (sections 5–8): one machine, many seeds in parallel, an
  AWS spot instance, and the fixed-base free-game check.
- **Part C — Analyse the results** (sections 9–10): statistics, noise study and charts, then
  the exact order that reproduces the paper.

Run **every command from the project root** (the folder that holds `GA-config.yaml`,
`Optimizer/` and `Simulator/`). Paths in the config are relative to that folder.

| Script                              | What it does                                                         | Section |
| ----------------------------------- | -------------------------------------------------------------------- | ------- |
| `Optimizer/main.py`                 | Runs the optimizer (GA + baselines) for the run numbers in a config  | 5       |
| `Optimizer/run_parallel.py`         | Runs many run numbers at once, with S3 upload and resume             | 6       |
| `Setup_spot.sh`, `Spot_watch.sh`    | Set up an AWS spot instance; save results if it is reclaimed         | 7       |
| `Optimizer/prepare_fixedBase.py`    | Sets up the fixed-base free-game experiment                          | 8       |
| `Optimizer/Stats/Stats.py`          | Statistical tests between methods (per mutation count)               | 9.1     |
| `Optimizer/Stats/MutationsStats.py` | Tests between mutation counts; each method at its best count         | 9.2     |
| `Optimizer/Stats/NoiseStudy.py`     | Re-simulates the best reelsets many times to measure simulator noise | 9.3     |
| `Optimizer/Stats/Compare.py`        | Draws charts 1–14 and the computing-cost report                      | 9.4     |
| `Optimizer/Stats/ExtraGraphs.py`    | Draws charts 15–17 (noise, head-to-head, overview)                   | 9.5     |

---

# Part A — Set up the environment

## 1. What you need

| Tool                    | Version                                                                | Needed for                                             |
| ----------------------- | ---------------------------------------------------------------------- | ------------------------------------------------------ |
| Python                  | 3.10 or newer                                                          | everything (the optimizer and the analysis are Python) |
| C++ compiler with C++20 | GCC 11+ (Linux), Visual Studio 2022 (Windows), Apple Clang 15+ (macOS) | **only** if you build the simulator yourself           |
| CMake                   | 3.20 or newer                                                          | **only** if you build the simulator yourself           |
| Git                     | any                                                                    | cloning the repository                                 |

There are two ways to get the simulator, the C++ program that plays the slot game:

- **Option A — download a ready-made simulator.** No C++ tools needed; Python is all you
  install. Best for reviewers who just want to run or check the experiments.
- **Option B — build it yourself.** Needed if you change any game rule in `Simulator/src`,
  if no download exists for your system (macOS), or if the Linux download does not start
  on your distribution.

First, get the code:

```bash
git clone <repo-url> Slot-Math-Optimization-GA
cd Slot-Math-Optimization-GA
```

## 2. Get the simulator

### Option A — download it (no C++ needed)

1. Open the repository's **Releases** page (on GitHub: _Releases_ in the right-hand
   sidebar, or add `/releases` to the repository URL).
2. Under the latest release, open **Assets** and download the file for your system:

   | System                          | File                        |
   | ------------------------------- | --------------------------- |
   | Windows 10/11, 64-bit           | `simulator-windows-x64.exe` |
   | Linux (Debian / Ubuntu), 64-bit | `simulator-linux-x64`       |

3. Create a `build` folder in the project root, move the file into it and rename it to
   `simulator` (`simulator.exe` on Windows).
4. Linux only, allow it to run:

   ```bash
   chmod +x build/simulator
   ```

   Windows only: if SmartScreen warns about an unknown app the first time, click
   **More info → Run anyway**.

Then install Python (section 3) and test the simulator (section 2, _Check the simulator_).

Things to know about the download:

- **The game rules are compiled into it.** Paytable, paylines, matrix size and free-spin
  rules in `Simulator/src` are fixed at release time. Change any C++ file and you must
  build it yourself (option B).
- **Linux:** built on Debian / Ubuntu. On another distribution an error like
  `GLIBC_2.xx not found` means it was built on a newer Linux than yours: build it yourself.
- **Results are identical** to a self-built simulator from the same source: the random
  stream depends only on the seed, never on the compiler or the thread count.

### Option B — build it yourself

Install the tools for your system, then run the two build commands below.

**Ubuntu / Debian**

```bash
sudo apt update
sudo apt install build-essential cmake git python3 python3-venv python3-pip
```

**Fedora**

```bash
sudo dnf install gcc-c++ make cmake git python3 python3-pip
```

**Arch / Manjaro**

```bash
sudo pacman -S base-devel cmake git python python-pip
```

**macOS** (tested less than Linux; no ready-made download)

```bash
xcode-select --install                 # Apple's compiler and command-line tools
brew install cmake python@3.12         # needs Homebrew: https://brew.sh
```

**Windows 10/11**

1. Install **Visual Studio 2022 Build Tools** with the **"Desktop development with C++"**
   workload (this includes CMake): <https://visualstudio.microsoft.com/downloads/>, under
   _Tools for Visual Studio → Build Tools_.
2. Install **Python 3.10+** from <https://www.python.org/downloads/> and tick
   **"Add python.exe to PATH"** in the installer.

   Or, in PowerShell with `winget`:

   ```powershell
   winget install Microsoft.VisualStudio.2022.BuildTools --override "--add Microsoft.VisualStudio.Workload.VCTools --includeRecommended --passive"
   winget install Kitware.CMake
   winget install Python.Python.3.12
   winget install Git.Git
   ```

3. Run the build commands from the **"Developer PowerShell for VS 2022"** (Start menu), so
   the compiler is found.

**Build (every system)**, from the project root:

```bash
cmake -S Simulator -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release -j
```

Always build **Release**: a Debug build is many times slower, and the optimizer calls the
simulator over a million times in the full study. The program ends up at:

| System                  | Simulator path                |
| ----------------------- | ----------------------------- |
| Linux, macOS            | `build/simulator`             |
| Windows (Visual Studio) | `build/Release/simulator.exe` |

Rebuild after every change to the C++ code; the optimizer always runs whatever is in `build/`.

### Check the simulator

```bash
# Linux / macOS
./build/simulator 1000000 Simulator/src/reelset.json true  check.json 1        # base game only, seed 1
./build/simulator 1000    Simulator/src/reelset.json sessions check2.json 1 80 # 1000 free-game sessions, trigger 1 in 80

# Windows (path: build\simulator.exe if downloaded, build\Release\simulator.exe if built)
build\simulator.exe 1000000 Simulator\src\reelset.json true check.json 1
```

You should see a table of symbol statistics and a line starting with `RTP:`, and
`check.json` should appear. Delete the check files afterwards.

The full command line, which the optimizer builds for you:

```
simulator <spins> <reelset.json> <mode> <out.json> <seed> [triggerRate]
    mode   true      base game only (free games are counted, not played)
           false     full game
           sessions  play free-game sessions directly; needs triggerRate (1 in X)
```

`SIM_THREADS=<n>` fixes the number of threads. It changes speed only, never results.

## 3. Set up Python

Use a virtual environment (a private package folder for this project).

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r Requirements.txt
```

**Windows (PowerShell)**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r Requirements.txt
```

If PowerShell says running scripts is disabled, run
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once and try again.

The prompt now starts with `(.venv)`. **Every new terminal needs the `activate` line
again**; `pip install` is needed once. For the S3 features of section 6–7 also run
`pip install boto3`.

## 4. Point the config at the simulator, then run a quick test

Open `GA-config.yaml` and set `simulatorPath` (forward slashes, even on Windows):

```yaml
paths:
  simulatorPath: build/simulator # Linux / macOS, downloaded or built
  # simulatorPath: build/simulator.exe            # Windows, downloaded
  # simulatorPath: build/Release/simulator.exe    # Windows, built yourself
```

A wrong path stops the optimizer at once with `CONFIG ERROR: Simulator not found at '...'`.

**Quick test (a few minutes).** Copy the config (`cp GA-config.yaml quick-test.yaml`;
Windows: `copy GA-config.yaml quick-test.yaml`) and change in the copy:

```yaml
run:
  runNumbers: [999] # keeps the test apart from real runs
  generations: 20
  spins: 100_000
  finalCheckSpins: 0
experiments:
  mutationCounts: [5]
```

```bash
python Optimizer/main.py quick-test.yaml
```

If it finishes and `Results/results.json` gains a `seed_999` entry, the setup works. Delete
that entry (or the file, if it was new) before real runs.

### What the config controls

All settings live in `GA-config.yaml`; every line is commented. The study used:

| Setting                        | Value                                                             | Meaning                                                                    |
| ------------------------------ | ----------------------------------------------------------------- | -------------------------------------------------------------------------- |
| `run.runNumbers`               | `"1-30"`                                                          | 30 independent runs; each number is that run's master random seed          |
| `run.gameMode`                 | `Both`                                                            | base-game stage, then free-game stage, for every run number                |
| `run.generations`              | `1000`                                                            | evaluation budget per method and run (baselines get the same)              |
| `run.populationSize`           | `10`                                                              | reelsets in the GA population                                              |
| `run.spins`                    | `10_000_000`                                                      | spins per evaluation during the search                                     |
| `run.finalCheckSpins`          | `100_000_000`                                                     | re-check of each method's best reelset, on an unused seed                  |
| `freeGame.evaluation`          | `sessions`                                                        | free stage plays free-game sessions directly (same statistics, ~5x faster) |
| `experiments.replacementTypes` | `Generational, SteadyState, ElistismGenerational`                 |                                                                            |
| `experiments.selectionTypes`   | `RouletteSelection, TournamentSelection, SUS`                     |                                                                            |
| `experiments.mutationCounts`   | `[1, 3, 5, 10]`                                                   | stops changed per child, out of all 250                                    |
| `baselines.methods`            | `RandomSearch, HillClimbing, SimulatedAnnealing`                  |                                                                            |
| `fitnessVariables.BaseGame`    | RTP 0.57 (w 10), hit rate 1 in 3 (w 6), trigger 1 in 80 (w 3)     |                                                                            |
| `fitnessVariables.FreeGame`    | RTP 0.38 (w 10), hit rate 1 in 2.7 (w 6), retrigger 1 in 60 (w 3) |                                                                            |

**Same run number + same config = identical results**, on any machine and thread count.
Mistakes in the config are reported in one line before anything runs, e.g.
`CONFIG ERROR: run.spins must be a whole number, got '10m'`. YAML needs spaces, never tabs.

---

# Part B — Run the experiments

## 5. On one machine: `main.py`

```bash
python Optimizer/main.py GA-config.yaml
```

Runs every combination (3 replacements × 3 selections × 4 mutation counts, plus the
baselines) for every run number, one after another. Results go to `Results/results.json`:
`seed_<n>` for the base stage, `seed_<n>_free` for the free stage. One base stage of one
seed took about 2 hours on 10 threads, and the two stages of all 30 seeds add up to about 83
hours (roughly 14 hours elapsed with 6 runs in parallel, section 6). One machine running
`main.py` is fine for a seed or two; use section 6 for all 30.

The console shows one line per generation (`Gen 1: child 98.12 | replaced 3 ...`) and at the
end of each experiment the final check of its best reelset. Fitness is an error score:
lower is better, 0 is a perfect match.

## 6. Many seeds in parallel: `run_parallel.py` (Linux)

```bash
python Optimizer/run_parallel.py launch GA-config.yaml --runs 1-30 --workers 6 --threads 10
python Optimizer/run_parallel.py status GA-config.yaml --runs 1-30
python Optimizer/run_parallel.py merge  GA-config.yaml --runs 1-30
```

- Each run gets its own folder `Parallel/run_<n>/` (config, log, results). `merge` copies them
  into `paths.resultFile` and keeps a timestamped backup of the old file.
- `--workers × --threads` should not exceed the CPU count (64 cores: 6 × 10).
- Runs with a `DONE` marker are skipped, so after an interruption run `launch` again.
- **New experiment?** Move the old folder away first (`mv Parallel Parallel_old`), or every
  run with a `DONE` marker is skipped.

Progress of each running seed (`total` = experiments per run: 96 for the main sweep over its
two stages, 33 for the fixed-base sweep):

```bash
total=96
for d in Parallel/run_*/; do r=$(basename "$d"); if [ -f "$d/DONE" ]; then echo "$r: DONE"; continue; fi
  echo "$r: experiment $(grep -c '^>> ' "$d/log.txt")/$total - $(grep '^>> ' "$d/log.txt" | tail -1 | cut -c1-70)"; done | sort -V
```

**With S3** (needed on spot instances, section 7):

```bash
python Optimizer/run_parallel.py pull   GA-config.yaml --runs 1-30 --s3 s3://<bucket>/<prefix>
python Optimizer/run_parallel.py launch GA-config.yaml --runs 1-30 --workers 6 --threads 10 --s3 s3://<bucket>/<prefix>
python Optimizer/run_parallel.py merge  GA-config.yaml --runs 1-30 --s3 s3://<bucket>/<prefix>
```

Each finished run uploads to `<prefix>/Parallel/run_<n>/`; `merge` uploads the combined file.
**Use a new prefix for every experiment**, or `pull` fetches another experiment's runs.

## 7. On an AWS spot instance: `Setup_spot.sh`, `Spot_watch.sh`

1. Launch Ubuntu 24.04 on the same instance type for every experiment (the study used
   **c7a.16xlarge**: AMD EPYC 9R14, 64 cores), with an IAM role that can use the bucket and a
   30 GB disk.
2. On the instance:

   ```bash
   git clone <repo-url> ~/Slot-Math-Optimization-GA && cd ~/Slot-Math-Optimization-GA
   bash Setup_spot.sh ~/Slot-Math-Optimization-GA <bucket>   # tools, Release build, .venv, S3 check
   source .venv/bin/activate
   aws s3 cp s3://<bucket>/sweep1/results.json Results/results.json   # only if the experiment needs earlier results
   ```

3. Start the sweep inside `tmux` (survives SSH disconnects) and the interruption watcher in a
   second window:

   ```bash
   tmux new -s sweep
   python Optimizer/run_parallel.py pull   <config> --runs 1-30 --s3 s3://<bucket>/<prefix>
   python Optimizer/run_parallel.py launch <config> --runs 1-30 --workers 6 --threads 10 --s3 s3://<bucket>/<prefix>
   # Ctrl-b c (new window):
   bash Spot_watch.sh ~/Slot-Math-Optimization-GA s3://<bucket>/<prefix>
   # Ctrl-b d to detach; tmux attach -t sweep to come back
   ```

4. If AWS reclaims the instance: on a new one repeat steps 1–2, then `pull` and `launch`.
   Finished runs come from S3; interrupted runs restart with the same seeds and give the same
   results.
5. When done: `merge`, run the analysis (Part C), copy `Results/` to S3, **terminate the
   instance** (it bills by the second).

## 8. Fixed-base free-game check: `prepare_fixedBase.py`

In `Both` mode every free-game run uses the base reels _its own_ method found, so free-game
results could partly reflect base-game luck. This check re-runs the free stage with **one**
base reelset for every method and seed.

```bash
python Optimizer/prepare_fixedBase.py GA-config.yaml
mv Parallel Parallel_sweep1                                   # if a Parallel/ folder exists
python Optimizer/run_parallel.py launch GA-config-fixedbase.yaml --runs 1-30 --workers 6 --threads 10 --s3 s3://<bucket>/fixedbase
python Optimizer/run_parallel.py merge  GA-config-fixedbase.yaml --runs 1-30 --s3 s3://<bucket>/fixedbase
```

`prepare_fixedBase.py` changes nothing that exists. It writes
`Optimizer/ReelSets/fixed_base.json` (default: the lowest final-check base fitness; pick
another with `--base seed_k/mutation_m/Combo`), `Results/results_fixedbase.json` (base
entries only) and `GA-config-fixedbase.yaml` (FreeGame, manual base, mutation 3/5/10, hill
climbing + simulated annealing; change with `--mutations`, `--baselines`).

Verify that every run used the fixed base (expect 990/990, trigger rates near the fixed base's):

```bash
python - <<'EOF'
import json
fx = json.load(open("Optimizer/ReelSets/fixed_base.json"))["BaseGameReel"]
u = lambda r: r[0] if r and isinstance(r[0][0], list) else r
d = json.load(open("Results/results_fixedbase.json"))
runs = [e for k, s in d.items() if k.endswith("_free") for c in s["results"].values() for e in c.values()]
print(sum(u(e["reelset"]["BaseGameReel"]) == u(fx) for e in runs), "/", len(runs), "use the fixed base")
t = [e["bestSpin"]["simOutput"]["freeTriggerRate"] for e in runs]
print(f"trigger rate in final checks: {min(t):.2f} - {max(t):.2f}")
EOF
```

---

# Part C — Analyse the results

The analysis scripts only read result files, except `NoiseStudy.py` (and `Stats.py` when a
run has no final check), which call the simulator. All of them run on Windows too.

## 9.1 `Stats.py` — methods against each other

```bash
python Optimizer/Stats/Stats.py Results/results.json --stage base --reeval stored --out Results/stats
python Optimizer/Stats/Stats.py Results/results.json --stage free --reeval stored --out Results/stats/FreeGame
python Optimizer/Stats/Stats.py Results/results_fixedbase.json --stage free --reeval stored --out Results/stats/FreeGame_fixedbase
```

- Per mutation count: Friedman test, then paired Wilcoxon signed-rank tests with Holm
  correction, Vargha–Delaney A12 effect size and a noise-floor check. Families: replacement
  strategy, selection within each strategy, GA vs baselines.
- `--reeval stored` uses each run's 100M-spin final check and stops if one is missing.
  Without it (`auto`) missing checks are simulated here; run that as
  `PYTHONPATH=Optimizer python Optimizer/Stats/Stats.py ...`.
- `--reeval off` tests the in-run values (biased low; quick look only).
- `--metric evals` tests evaluations to reach error 0.2 instead of the final error.
- Writes `stats_report.md` (tables + "claims you can make"), `stats_pairwise.csv`,
  `stats_friedman.csv`, `stats_runs.csv`.

## 9.2 `MutationsStats.py` — mutation counts

```bash
python Optimizer/Stats/MutationsStats.py Results/results.json --stage base --out Results/stats/mutation_base
python Optimizer/Stats/MutationsStats.py Results/results.json --stage free --out Results/stats/mutation_free
python Optimizer/Stats/MutationsStats.py Results/results_fixedbase.json --stage free --out Results/stats/mutation_free_fixedbase
```

Per method: Friedman across mutation counts and pairwise Wilcoxon + Holm; then every method
at its own best count, GA vs baselines. Reads the stored final checks only (seconds).
Writes `mutation_report.md`, `mutation_pairwise.csv`, `mutation_friedman.csv`, `best_mutation.csv`.

## 9.3 `NoiseStudy.py` — simulator noise

```bash
python Optimizer/Stats/NoiseStudy.py --results Results/results.json --runs 30 --spins 10000000
python Optimizer/Stats/NoiseStudy.py --mode FreeGame --mutation 5          # one mode / mutation count
```

Takes each method's best reelset (per stage and mutation count), re-simulates it `--runs`
times on different seeds, and reports the run-to-run SD of every statistic and of the fitness,
the smallest difference that counts as real, and whether a shared seed reduces noise. About
2,880 simulations; run it on the big machine. Writes `NoiseStudy/report.txt`,
`noise_runs.csv`, `noise_summary.csv`, `reelsets/`. Not needed again for the fixed-base check.

## 9.4 `Compare.py` — charts 1–14 and the cost report

```bash
python Optimizer/Stats/Compare.py --results Results/results.json --fixed Results/results_fixedbase.json
python Optimizer/Stats/Compare.py --stage base       # base charts only
python Optimizer/Stats/Compare.py --mutation 3       # mutation count for charts 4, 9, 11
```

| Output                                      | Chart                                                                                                                                                        |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `Results/Graphs/1–9`                        | base game: convergence, final error by mutation, heatmap, speed to target, Steady-state by mutation, selection, best vs mean, best–mean gap, GA vs baselines |
| `Results/Graphs/10–11`, `compute_report.md` | computing cost; budget and population                                                                                                                        |
| `Results/Graphs/FreeGame/3`, `9`            | free-game heatmap; GA vs baselines                                                                                                                           |
| `Results/Graphs/FreeGame/13`                | Both mode vs fixed base (needs `--fixed`)                                                                                                                    |
| `Results/Graphs/FreeGame/14`                | free-game hit-rate / retrigger trade-off                                                                                                                     |

Final-error charts use the 100M-spin final checks (the numbers the tests use); curves over a
run use in-run values and say so on the axis. Known issue: the cost-vs-spins panel of chart
10 and the "Spins per evaluation" table of `compute_report.md` use a 51-thread model that
does not match the 10-thread runs; do not cite them.

## 9.5 `ExtraGraphs.py` — charts 15–17

```bash
python Optimizer/Stats/ExtraGraphs.py            # writes to Results/Graphs/
```

Needs the outputs of 9.1, 9.2 and 9.3. Draws `15_noise_vs_error.png`,
`16_paired_wins_vs_hill_climbing.png` and `17_overview_best_mutation.png`.

## 10. Reproduce everything, in order

1. Part A: simulator, Python, config, quick test.
2. Section 6/7: main sweep, `GA-config.yaml`, runs 1–30, prefix `sweep1`; `merge`.
3. Section 8: fixed-base sweep, prefix `fixedbase`; `merge`; verify.
4. Section 9.3: noise study.
5. Sections 9.1, 9.2: statistics on `results.json` (base, free) and `results_fixedbase.json` (free).
6. Sections 9.4, 9.5: charts.

## 11. Troubleshooting

| Problem                                                            | Fix                                                                                                                                           |
| ------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `CONFIG ERROR: Simulator not found at ...`                         | Get the simulator (section 2) and set `simulatorPath` (section 4). On Windows the path ends in `.exe`.                                        |
| `ModuleNotFoundError: No module named 'yaml'`                      | The virtual environment is not active: run the `activate` line (section 3).                                                                   |
| `JSONDecodeError: Expecting value`                                 | The simulator wrote no output, usually because it is older than the Python code (no `sessions` mode). Download the latest release or rebuild. |
| `myapp failed (...)`                                               | The simulator crashed; its own error is printed below. Run it by hand (section 2).                                                            |
| Linux: `Permission denied` on the downloaded simulator             | `chmod +x build/simulator`                                                                                                                    |
| Linux: `GLIBC_2.xx not found`                                      | The download was built on a newer Linux. Build it yourself (option B).                                                                        |
| Linux link error mentioning `pthread`                              | Add `find_package(Threads REQUIRED)` and `target_link_libraries(simulator PRIVATE Threads::Threads)` to `Simulator/CMakeLists.txt`, rebuild.  |
| Windows: `cmake` or `cl` not found                                 | Use the **Developer PowerShell for VS 2022**.                                                                                                 |
| Windows: `python3` not found                                       | Use `python`.                                                                                                                                 |
| macOS: "cannot be opened because the developer cannot be verified" | You built it yourself, so this should not happen; for a copied binary run `xattr -d com.apple.quarantine build/simulator`.                    |
| Runs are very slow                                                 | Simulator not built in Release, or `--workers × --threads` above the CPU count.                                                               |
| `can't open file ...`                                              | Check exact file names and case (`prepare_fixedBase.py`, `MutationsStats.py`): `ls Optimizer Optimizer/Stats`.                                |
| Status loop prints `run_*: waiting`                                | You are not in the project root, or `launch` has not started a run.                                                                           |
| `launch` says all runs already done                                | An old `Parallel/` folder (move it away) or an old S3 prefix (use a new one).                                                                 |
| Stats.py `ModuleNotFoundError: Seeding`                            | A run lacks a final check: use `--reeval stored`, or `PYTHONPATH=Optimizer`.                                                                  |
| A FreeGame run says there are no BaseGame results                  | Run BaseGame first with the same `runNumber` and `experiments`, or use `baseReelSource: manual`.                                              |
| `git push` rejected, file over 100 MB                              | Result files stay out of git (`Results/*.json`, `Parallel/` are in `.gitignore`); keep them in S3 / Zenodo.                                   |
