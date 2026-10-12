# Running the project

This guide explains how to set the project up and reproduce the results in the
[README](README.md). Every command is followed by a short table explaining what each part of
it means.

There are two ways to use it:

| | What you get | Time |
|---|---|---|
| **A. Check the published results** | Re-run every statistical test and redraw every chart from the study's saved results | Minutes, on a laptop |
| **B. Repeat the whole experiment** | Run all 2,700 optimizations again from scratch | About 14 hours on a 64-core machine (83 hours of computing) |

Most readers only need **A**. Both start with the same setup (sections 1–5).

Run every command from the **project folder** (the one containing `GA-config.yaml`).

## Contents

**Setup**

1. [What you need](#1-what-you-need)
2. [Get the simulator](#2-get-the-simulator)
3. [Set up Python](#3-set-up-python)
4. [Point the project at the simulator](#4-point-the-project-at-the-simulator)
5. [The settings file](#5-the-settings-file-ga-configyaml)

**Using the project**

- [A. Check the published results](#a-check-the-published-results) — `Stats.py`, `MutationsStats.py`, `Compare.py`, `ExtraGraphs.py`
- [B. Repeat the whole experiment](#b-repeat-the-whole-experiment) — `main.py`, `run_parallel.py`, `prepare_fixedBase.py`, `NoiseStudy.py`
- [Running on a cloud machine](#running-on-a-cloud-machine-optional) — `Setup_spot.sh`, `Spot_watch.sh`
- [Common problems](#common-problems)

---

## 1. What you need

- **Python 3.10 or newer** — always needed.
- **The simulator** — the C++ program that plays the slot game. Download a ready-made copy (no
  C++ tools needed) or build it yourself.
- **Git**, to download the code.

```bash
git clone https://github.com/TRavi107/Slot-Math-Optimization-GA.git Slot-Math-Optimization-GA
cd Slot-Math-Optimization-GA
```

## 2. Get the simulator

### Option 1: download it (recommended)

1. Open the repository's **Releases** page and download, from the latest release:
   - Windows: `simulator-windows-x64.exe`
   - Linux: `simulator-linux-x64`
2. Create a folder called `build` inside the project folder and put the file there, renamed to
   `simulator.exe` (Windows) or `simulator` (Linux).
3. On Linux, make it runnable: `chmod +x build/simulator`.
   On Windows, if a SmartScreen warning appears, choose **More info → Run anyway**.

The downloaded simulator gives exactly the same results as one you build yourself.

### Option 2: build it yourself

Needed on macOS, or if you want to change the game's rules. First install a C++ compiler and
CMake:

| System | Install |
|---|---|
| Ubuntu / Debian | `sudo apt install build-essential cmake git python3 python3-venv python3-pip` |
| Fedora | `sudo dnf install gcc-c++ make cmake git python3 python3-pip` |
| Arch | `sudo pacman -S base-devel cmake git python python-pip` |
| macOS | `xcode-select --install`, then `brew install cmake python` ([Homebrew](https://brew.sh)) |
| Windows | Install [Visual Studio 2022 Build Tools](https://visualstudio.microsoft.com/downloads/) with **"Desktop development with C++"**, and [Python](https://www.python.org/downloads/) (tick **"Add python.exe to PATH"**). Run the commands below in the **Developer PowerShell for VS 2022**. |

Then build:

```bash
cmake -S Simulator -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

| Part | Meaning |
|---|---|
| `-S Simulator` | Where the simulator's source code is |
| `-B build` | Where to put the finished program |
| `-DCMAKE_BUILD_TYPE=Release` / `--config Release` | Build with full speed optimisations. Always use Release: a debug build is many times slower. |

The simulator appears at `build/simulator` (Linux, macOS) or `build/Release/simulator.exe`
(Windows).

### Using the simulator directly

You normally never run the simulator yourself — the optimizer does it — but it is useful for
checking a reel set by hand:

```bash
./build/simulator 1000000 Simulator/src/reelset.json        # Linux / macOS
build\simulator.exe 1000000 Simulator\src\reelset.json      # Windows
```

This plays one million spins and prints the game's statistics, ending with a line starting
with `RTP:`. The full form is:

```
simulator <spins> [reelset] [mode] [output] [seed] [triggerRate]
```

| Argument | Meaning | Example |
|---|---|---|
| `<spins>` | How many spins to play. More spins give more accurate statistics. | `10000000` |
| `[reelset]` | The reel strips to play, as a JSON file. If left out, `Simulator/src/reelset.json` is used. | `Simulator/src/reelset.json` |
| `[mode]` | `false` — the full game (default). `true` — base game only: free games are counted but not played. `sessions` — play free-game rounds directly, with no base spins; `<spins>` then means the number of rounds. | `true` |
| `[output]` | File to save the statistics to, as JSON. Optional. | `result.json` |
| `[seed]` | Number that fixes the random spins. The same seed and settings always give exactly the same result. If left out, a random seed is used and printed. | `42` |
| `[triggerRate]` | Only for `sessions` mode: how often the base game starts a free game, as "1 in X". | `80` |

Arguments are given in this order, so to set a later one you must also give the earlier ones.
Setting the environment variable `SIM_THREADS` (for example `SIM_THREADS=4`) limits how many
CPU cores it uses; this changes only the speed, never the results.

## 3. Set up Python

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
pip install -r Requirements.txt
```

| Command | Meaning |
|---|---|
| `python3 -m venv .venv` | Creates a private folder of Python packages (`.venv`) for this project, so it cannot clash with other projects. On Windows, type `python` instead of `python3`. |
| `source .venv/bin/activate` | Switches the terminal to use that folder. Your prompt then starts with `(.venv)`. **Repeat this in every new terminal.** |
| `pip install -r Requirements.txt` | Installs the packages the project needs (PyYAML, numpy, pandas, matplotlib, scipy). Needed only once. |

If PowerShell refuses to run the activate script, run
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once and try again.

## 4. Point the project at the simulator

Open `GA-config.yaml` and set the simulator's location (use forward slashes, also on Windows):

```yaml
paths:
  simulatorPath: build/simulator                # Linux / macOS
  # simulatorPath: build/simulator.exe          # Windows, downloaded
  # simulatorPath: build/Release/simulator.exe  # Windows, built yourself
```

## 5. The settings file (`GA-config.yaml`)

Every setting of the experiment lives in `GA-config.yaml`, and each line in it is commented.
You do not need to change anything to reproduce the study; these are the settings it used:

| Setting | Study value | Meaning |
|---|---|---|
| `run.runNumbers` | `"1-30"` | Which runs to do. Each run number is that run's random seed: the same number always gives the same result. |
| `run.gameMode` | `Both` | Tune the base game, then the free game, for every run. (`BaseGame` or `FreeGame` does only one.) |
| `run.generations` | `1000` | Budget: how many reel sets each method may simulate in one run. |
| `run.populationSize` | `10` | How many reel sets the genetic algorithm keeps at once. |
| `run.spins` | `10_000_000` | Spins per simulation during the search. |
| `run.finalCheckSpins` | `100_000_000` | Spins for the final, more precise check of each run's best reel set. |
| `experiments.replacementTypes` | all three | Which GA replacement strategies to run. |
| `experiments.selectionTypes` | all three | Which GA selection methods to run. |
| `experiments.mutationCounts` | `[1, 3, 5, 10]` | How many of the 250 reel positions are changed per child. |
| `baselines.methods` | `RandomSearch, HillClimbing, SimulatedAnnealing` | The comparison methods. |
| `fitnessVariables` | see README, section 3 | The targets (RTP, hit rate, ...) and how much each one counts. |
| `paths.resultFile` | `Results/results.json` | Where results are saved. |

If something in the file is wrong, the program stops straight away with a one-line message such
as `CONFIG ERROR: run.spins must be a whole number, got '10m'`.

---

# A. Check the published results

**Step 1.** From the latest release, download `results.json` and `results_fixedbase.json` and
put them in the `Results` folder.

**Step 2. Compare the methods with `Stats.py`.** Run it three times: base game, free game, and
the fixed-base free-game check.

```bash
python Optimizer/Stats/Stats.py Results/results.json --stage base --reeval stored --out Results/stats
python Optimizer/Stats/Stats.py Results/results.json --stage free --reeval stored --out Results/stats/FreeGame
python Optimizer/Stats/Stats.py Results/results_fixedbase.json --stage free --reeval stored --out Results/stats/FreeGame_fixedbase
```

| Argument | Meaning |
|---|---|
| `Results/results.json` | The results file to analyse. |
| `--stage base` / `free` | Which part of the game to analyse: the base game or the free game. |
| `--reeval stored` | Score each run by its final 100-million-spin check, which is saved in the results file. This is the fair score; the best score seen during a run is slightly too optimistic. |
| `--out` | Folder for the reports. |
| `--metric evals` *(optional)* | Instead of the final error, compare how many simulations each method needed to reach an error of 0.2. |
| `--alpha 0.05` *(optional)* | Significance level for the tests (default 0.05). |

**What it does:** for each mutation count, it tests whether the methods differ (Friedman test),
then compares them pair by pair, run by run (Wilcoxon test with Holm correction), and gives an
effect size (A12) for each pair. **Output:** `stats_report.md` — readable tables plus a list of
the conclusions the data supports — and the same numbers as CSV files.

**Step 3. Compare mutation counts with `MutationsStats.py`.**

```bash
python Optimizer/Stats/MutationsStats.py Results/results.json --stage base --out Results/stats/mutation_base
python Optimizer/Stats/MutationsStats.py Results/results.json --stage free --out Results/stats/mutation_free
python Optimizer/Stats/MutationsStats.py Results/results_fixedbase.json --stage free --out Results/stats/mutation_free_fixedbase
```

| Argument | Meaning |
|---|---|
| `Results/results.json` | The results file to analyse. |
| `--stage base` / `free` | Base game or free game. |
| `--out` | Folder for the reports. |

**What it does:** for every method, tests whether the mutation count (1, 3, 5 or 10) changes
its result, finds each method's best count, and compares all methods at their best counts.
**Output:** `mutation_report.md`, `best_mutation.csv` and CSV files of every test.

**Step 4. Draw the charts with `Compare.py` and `ExtraGraphs.py`.**

```bash
python Optimizer/Stats/Compare.py --results Results/results.json --fixed Results/results_fixedbase.json
python Optimizer/Stats/ExtraGraphs.py
```

`Compare.py` options:

| Argument | Meaning |
|---|---|
| `--results` | The main results file (default `Results/results.json`). |
| `--fixed` | The fixed-base check's results file, used for the chart comparing the two free-game experiments. If it is missing, that one chart is skipped. |
| `--out` *(optional)* | Folder for the charts (default `Results/Graphs`; free-game charts go in its `FreeGame` subfolder). |
| `--stage base` / `free` / `both` *(optional)* | Draw only the base-game charts, only the free-game charts, or both (default). |
| `--mutation 5` *(optional)* | Which mutation count to use for the charts that show a single count (default 5). |

`ExtraGraphs.py` options (it reads the reports made in steps 2 and 3, and the noise study):

| Argument | Meaning |
|---|---|
| `--stats` *(optional)* | Folder with the statistics reports (default `Results/stats`). |
| `--noise` *(optional)* | The noise study's results (default `NoiseStudy/noise_runs.csv`). |
| `--out` *(optional)* | Folder for the charts (default `Results/Graphs`). |

**Output:** every chart shown in the README, in `Results/Graphs/`. The simulator-noise
measurements are already included in `NoiseStudy/` (`report.txt`).

The numbers in the reports and charts should match the README exactly.

---

# B. Repeat the whole experiment

The experiment has three parts. Each is fully reproducible: every random choice comes from the
run number, so the same settings give the same results on any computer. Afterwards, analyse the
new results exactly as in part A (steps 2–4).

## B1. Main study with `main.py` or `run_parallel.py`

`GA-config.yaml` already holds the study's settings (section 5).

**On one computer**, with `main.py`:

```bash
python Optimizer/main.py GA-config.yaml
```

| Argument | Meaning |
|---|---|
| `GA-config.yaml` | The settings file. `main.py` runs every combination of settings in it (each GA configuration and each comparison method, at each mutation count) for every run number listed, one after another, and saves the results in `paths.resultFile`. |

This works anywhere, but all 30 runs one after another take several days. A quick way to test
your setup first: copy `GA-config.yaml` to `quick-test.yaml`, set `runNumbers: [999]`,
`generations: 20`, `spins: 100_000`, `finalCheckSpins: 0` and `mutationCounts: [5]`, and run
`python Optimizer/main.py quick-test.yaml`. It finishes in a few minutes.

**On a large computer**, run several seeds at the same time with `run_parallel.py`:

```bash
python Optimizer/run_parallel.py launch GA-config.yaml --runs 1-30 --workers 6 --threads 10
python Optimizer/run_parallel.py status GA-config.yaml --runs 1-30
python Optimizer/run_parallel.py merge  GA-config.yaml --runs 1-30
```

| Part | Meaning |
|---|---|
| `launch` | Starts the runs. Each run works in its own folder, `Parallel/run_<n>/`, with its own log file. If the process is stopped, run the same command again: finished runs are skipped and the rest restart. |
| `status` | Shows which runs are finished, running or not started. Safe to use at any time. |
| `merge` | When all runs are finished, combines them into `Results/results.json`. A backup of any existing file is kept. |
| `GA-config.yaml` | The settings file. |
| `--runs 1-30` | Which run numbers to do. Also accepts lists such as `1-10,15`. If left out, the list in the settings file is used. |
| `--workers 6` | How many runs work at the same time. |
| `--threads 10` | How many CPU cores each run's simulator uses. Keep `workers × threads` at or below your number of cores; 10 is the most a 10-million-spin simulation can use. |
| `--s3 s3://bucket/folder` *(optional)* | Also copy each finished run to Amazon S3 storage (see "Running on a cloud machine"). |

## B2. Fixed-base free-game check with `prepare_fixedBase.py`

This repeats the free-game stage with one shared set of base reels for every method (README,
section 5.4). It needs the main study's results in `Results/results.json`.

```bash
python Optimizer/prepare_fixedBase.py GA-config.yaml
python Optimizer/run_parallel.py launch GA-config-fixedbase.yaml --runs 1-30 --workers 6 --threads 10
python Optimizer/run_parallel.py merge  GA-config-fixedbase.yaml --runs 1-30
```

`prepare_fixedBase.py` takes the best base-game reels from the main study and creates
everything this check needs: the shared base reels, a results file for the check
(`Results/results_fixedbase.json`) and its settings file (`GA-config-fixedbase.yaml`). It does
not change any existing file. The two `run_parallel.py` commands then run and combine the
check exactly as in B1. If a `Parallel` folder is left over from B1, rename it first, or every
run will be reported as already finished.

| Argument of `prepare_fixedBase.py` | Meaning |
|---|---|
| `GA-config.yaml` | The main study's settings file. |
| `--base seed_18/mutation_1/SteadyState_RouletteSelection` *(optional)* | Use a specific run's base reels instead of the best ones. The format is run / mutation count / method. |
| `--mutations 3,5,10` *(optional)* | Mutation counts for the check (default 3, 5 and 10, as in the study). |
| `--baselines HillClimbing,SimulatedAnnealing` *(optional)* | Comparison methods for the check (default: these two, as in the study). |

## B3. Simulator-noise study with `NoiseStudy.py`

```bash
python Optimizer/Stats/NoiseStudy.py --results Results/results.json --runs 30 --spins 10000000
```

| Argument | Meaning |
|---|---|
| `--results` | The main results file. The study takes each method's best reel set from it. |
| `--runs 30` | How many times to re-simulate each reel set, each time with a different seed. |
| `--spins 10000000` | Spins per simulation — the same as during the search, so the noise measured is the noise the methods faced. |
| `--mode BaseGame` / `FreeGame` *(optional)* | Study only one part of the game (default: both). |
| `--mutation 5` *(optional)* | Study only some mutation counts (default: all). |
| `--simulator` *(optional)* | Where the simulator is (default `build/simulator`). On Windows, give `build/simulator.exe`. |
| `--workers` *(optional)* | How many simulations run at once (default: one per CPU core). |
| `--out` *(optional)* | Output folder (default `NoiseStudy`). |

**What it does:** re-simulates the best reel set of every method, for each game stage and
mutation count, 30 times (about 2,900 simulations), and measures how much each statistic and
each score moves from one simulation to the next. **Output:** `NoiseStudy/report.txt` and CSV
files.

---

## Running on a cloud machine (optional)

The study was run on an Amazon Web Services (AWS) **c7a.16xlarge** machine (64 cores, Ubuntu
24.04) with cheaper "spot" pricing, which AWS may interrupt at short notice. Two scripts make
that safe by keeping results in Amazon S3 storage.

**1. Prepare the machine** with `Setup_spot.sh`:

```bash
git clone <repository-url> ~/Slot-Math-Optimization-GA
cd ~/Slot-Math-Optimization-GA
bash Setup_spot.sh ~/Slot-Math-Optimization-GA <your-bucket>
source .venv/bin/activate
```

| Argument | Meaning |
|---|---|
| `~/Slot-Math-Optimization-GA` | The project folder on the cloud machine. |
| `<your-bucket>` | The name of your S3 storage bucket. The machine needs permission to write to it. |

It installs the tools, builds the simulator, sets up Python and checks that the bucket can be
written to.

**2. Start the runs** inside `tmux`, which keeps them running if your connection drops:

```bash
tmux new -s sweep
python Optimizer/run_parallel.py pull   GA-config.yaml --runs 1-30 --s3 s3://<your-bucket>/sweep1
python Optimizer/run_parallel.py launch GA-config.yaml --runs 1-30 --workers 6 --threads 10 --s3 s3://<your-bucket>/sweep1
```

| Part | Meaning |
|---|---|
| `pull` | Downloads runs that were already finished on an earlier machine, so they are not repeated. Does nothing the first time. |
| `--s3 s3://<your-bucket>/sweep1` | The storage folder for this experiment. Each finished run is copied there. Use a different folder name for each experiment (for example `fixedbase` for B2). |

Press `Ctrl-b` then `d` to leave the runs working in the background; `tmux attach -t sweep`
brings them back.

**3. Watch for interruptions** with `Spot_watch.sh`, in a second tmux window (`Ctrl-b` then `c`):

```bash
bash Spot_watch.sh ~/Slot-Math-Optimization-GA s3://<your-bucket>/sweep1
```

| Argument | Meaning |
|---|---|
| `~/Slot-Math-Optimization-GA` | The project folder. |
| `s3://<your-bucket>/sweep1` | The same storage folder as in step 2. |

AWS gives about two minutes' warning before reclaiming a spot machine; this script then copies
all results to S3. On a new machine, repeat steps 1 and 2: `pull` brings back the finished
runs and `launch` continues with the rest.

**4. When all runs are finished**, combine them with
`python Optimizer/run_parallel.py merge GA-config.yaml --runs 1-30 --s3 s3://<your-bucket>/sweep1`,
run the analysis (part A, steps 2–4), and shut the machine down — it is billed until you do.

---

## Common problems

| Problem | What to do |
|---|---|
| `Simulator not found` | Check `simulatorPath` in `GA-config.yaml` (section 4). On Windows the name ends in `.exe`. |
| `No module named 'yaml'` (or `pandas`, `scipy`) | The Python environment isn't active. Run the `activate` line from section 3. |
| Linux: `Permission denied` when starting the simulator | Run `chmod +x build/simulator`. |
| Windows: `cmake` not found | Use the **Developer PowerShell for VS 2022** from the Start menu. |
| Windows: `python3` not found | Type `python` instead. |
| Runs are much slower than expected | Build the simulator in Release mode (section 2), and keep `--workers × --threads` at or below your number of CPU cores. |
| `launch` says every run is already done | An old `Parallel` folder is still there. Rename or remove it. |
| `Stats.py` says some runs have no final check | The results file was made without final checks (`finalCheckSpins: 0`). Re-run the experiment with `finalCheckSpins: 100_000_000`, as in the study. |