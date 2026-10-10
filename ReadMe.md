# Slot Math Tuning with a Genetic Algorithm

Tunes the reel strips of a 5-reel slot game so that its statistics (RTP, hit rate,
free-game trigger rate, …) hit target values.

- **Simulator** (C++) spins a reelset millions of times and reports its statistics.
- **Optimizer** (Python) is a genetic algorithm: it breeds and mutates reelsets,
  asks the simulator to score each one, and keeps the best.

Everything you normally change lives in one file: **`GA-config.yaml`**.

---

## Contents

1. [Project layout](#1-project-layout)
2. [Install the tools](#2-install-the-tools)
3. [Build the simulator](#3-build-the-simulator)
4. [Set up Python](#4-set-up-python)
5. [Point the config at the simulator](#5-point-the-config-at-the-simulator)
6. [Run the optimizer](#6-run-the-optimizer)
7. [Changing the config](#7-changing-the-config)
8. [Results and charts](#8-results-and-charts)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Project layout

```
<project root>/                  <- run every command from here
├── GA-config.yaml               <- all settings
├── requirements.txt             <- Python packages
├── Simulator/                   <- C++ simulator
│   ├── CMakeLists.txt
│   └── src/
│       ├── main.cpp
│       ├── constants.hpp
│       └── reelset.json         <- default reelset when none is passed
├── Optimizer/                   <- Python genetic algorithm
│   ├── main.py                  <- entry point
│   ├── Config.py                <- reads and checks GA-config.yaml
│   ├── Parents.py  Selection.py  Replacement.py  Utility.py
│   ├── Compare.py               <- draws charts from the results
│   └── ReelSets/                <- reelset files used during a run
├── build/                       <- created when you build the simulator
└── Results/                     <- created on the first run (results.json, charts)
```

All paths in `GA-config.yaml` are relative to the **project root**, so always run
commands from there.

---

## 2. Install the tools

You need:

| Tool | Version | Why |
|---|---|---|
| C++ compiler with C++20 | GCC 11+, Clang 14+, or Visual Studio 2022 | builds the simulator |
| CMake | 3.20+ | build system for the simulator |
| Python | 3.10+ | runs the optimizer |

Pick your operating system:

### Ubuntu / Debian

```bash
sudo apt update
sudo apt install build-essential cmake python3 python3-venv python3-pip
```

### Fedora

```bash
sudo dnf install gcc-c++ make cmake python3 python3-pip
```

### Arch / Manjaro

```bash
sudo pacman -S base-devel cmake python python-pip
```

### macOS

```bash
xcode-select --install          # Apple's C++ compiler (Clang)
brew install cmake python       # needs Homebrew: https://brew.sh
```

### Windows

1. Install **Visual Studio 2022 Build Tools** with the
   **"Desktop development with C++"** workload (this includes the compiler *and* CMake):
   <https://visualstudio.microsoft.com/downloads/> → *Tools for Visual Studio* → *Build Tools*.
2. Install **Python 3.10+** from <https://www.python.org/downloads/>.
   In the installer, tick **"Add python.exe to PATH"**.

Or, with `winget` in PowerShell:

```powershell
winget install Microsoft.VisualStudio.2022.BuildTools --override "--add Microsoft.VisualStudio.Workload.VCTools --includeRecommended --passive"
winget install Kitware.CMake
winget install Python.Python.3.12
```

Run the build commands below from the **"Developer PowerShell for VS 2022"**
(Start menu), so the compiler is found.

### Check the install

Open a **new** terminal and run:

```bash
cmake --version          # 3.20 or newer
python3 --version        # 3.10 or newer   (Windows: python --version)
g++ --version            # Linux; macOS: clang++ --version; Windows: skip
```

---

## 3. Build the simulator

From the project root:

```bash
cmake -S Simulator -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release -j
```

- `-S Simulator` is where the source is, `-B build` is where the program is built.
- **Always build `Release`.** A debug build can be many times slower, and the
  optimizer runs the simulator thousands of times.

Where the program ends up:

| OS | Simulator path |
|---|---|
| Linux / macOS | `build/simulator` |
| Windows (Visual Studio) | `build/Release/simulator.exe` |

**Test it** with a quick 100,000-spin run on the built-in reelset:

```bash
./build/simulator 100000                    # Linux / macOS
build\Release\simulator.exe 100000          # Windows
```

You should see a table of symbol stats followed by `RTP: ...`.

> **Rebuild after every C++ change.** Python always runs whatever binary is in
> `build/`. If you change the C++ code and forget to rebuild, the optimizer silently
> uses the old version.

### Simulator command line (for reference)

The optimizer calls the simulator like this; you don't need to do it yourself:

```
simulator <spins> <reelset.json> <runOnlyBase: true|false> <output.json>
```

`runOnlyBase = true` skips the free spins but still counts free-game triggers.
The optimizer uses it in BaseGame mode to save time.

---

## 4. Set up Python

Use a **virtual environment** (`.venv`), a private folder of packages for this
project, so nothing clashes with other Python projects.

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows (PowerShell)**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> If PowerShell says running scripts is disabled, run
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then activate again.

When the environment is active, your prompt starts with `(.venv)`.
**Activate it again every time you open a new terminal** (just the `activate`
line; the install only happens once).

---

## 5. Point the config at the simulator

Open `GA-config.yaml` and set `simulatorPath` to the path from step 3:

```yaml
paths:
  simulatorPath: build/simulator                  # Linux / macOS
  # simulatorPath: build/Release/simulator.exe    # Windows
```

Use forward slashes `/` in the config, even on Windows.

The optimizer checks this path before it starts. If it's wrong, you get
`Simulator not found at '...'` instead of a crash later.

---

## 6. Run the optimizer

From the project root, with `.venv` active:

```bash
python Optimizer/main.py GA-config.yaml
```

### Do a quick test run first

A full run can take hours. Before that, copy the config and make it tiny:

```bash
cp GA-config.yaml quick-test.yaml        # Windows: copy GA-config.yaml quick-test.yaml
```

In `quick-test.yaml` set:

```yaml
run:
  runNumber: 999          # keeps test results separate from real ones
  generations: 20
  spins: 100_000
  finalCheckSpins: 0
```

Then:

```bash
python Optimizer/main.py quick-test.yaml
```

If this finishes and `Results/results.json` appears, everything is set up correctly.

### What you'll see

```
[parents] Using seed parents from Optimizer/ReelSets/seed_parents.json
Evaluating 10 initial parents...
parent0: fitness 115.2524, rtp 61.20 %
...
>> SteadyState + RouletteSelection | mutation 5 | 300 generations
Gen 1: child 98.1234 | replaced 3 (worst was 130.2001) | best 95.0000, mean dist 110.0000
...
Best ever: fitness 0.1543, found in generation 295 (last generation's best: 0.1543)
SteadyState_RouletteSelection took 1234.5s
```

**Fitness is an error score: lower is better, 0 is a perfect hit on every target.**

---

## 7. Changing the config

Every setting in `GA-config.yaml` has a comment above it. The sections are:

### `run`: what kind of run

| Setting | Meaning |
|---|---|
| `runNumber` | Label for this run. Results are saved under `seed_<runNumber>`. Same number = continue or repeat on the same parents; new number = start fresh. |
| `generations` | How long to evolve. SteadyState uses it as-is; Generational uses `generations / populationSize`. |
| `createNewParents` | `true`: start from random reelsets. `false`: reuse saved parents (see below). |
| `populationSize` | Reelsets in the population (10 is typical). |
| `spins` | Spins per evaluation. More = more accurate and slower. `100_000` for tests, `10_000_000` for real runs. |
| `gameMode` | `BaseGame`: tune base reels. `FreeGame`: keep base reels fixed and tune free reels. |
| `finalCheckSpins` | After each experiment, re-test the best reelset with this many spins. `0` = off. |

With `createNewParents: false`, starting parents are looked up in this order:

1. `Results/results.json` → `seed_<runNumber>` → `initial_population`
2. `paths.seedParentsFile`
3. If neither exists, random parents are created automatically.

> Use `createNewParents: true` **only with a new `runNumber`**. Re-running an
> existing `runNumber` with new random parents mixes populations in the results.

### `freeGame`: only for `gameMode: FreeGame`

| `baseReelSource` | Where the fixed base reels come from |
|---|---|
| `same` | For each combination, the best base reels that **same** combination found in the BaseGame run with the same `runNumber`. The free run also starts from that run's parents. |
| `manual` | One reelset file, `baseReelFile`, used for every combination. |

**Typical two-step workflow:**

1. `gameMode: BaseGame`, `runNumber: 4`. Saves results under `seed_4`.
2. `gameMode: FreeGame`, `runNumber: 4`, `baseReelSource: same`. Reads `seed_4`,
   saves under `seed_4_free`.

Keep `experiments` the same in both steps. With `same`, every free-game combination
must exist in the BaseGame run, or the run stops at the start and lists what's missing.

### `experiments`: what to compare

Every combination of the three lists is run, one after another.

```yaml
experiments:
  replacementTypes: [SteadyState]                            # Generational, SteadyState, ElistismGenerational
  selectionTypes:   [RouletteSelection, TournamentSelection]  # RouletteSelection, TournamentSelection, SUS
  mutationCounts:   [5]                                      # reel stops changed per mutation (5 of 50 = 10%)
```

Two selection types × one replacement × one mutation count = 2 experiments.
To switch one off, delete it or put `#` in front of it.

### `reels`: the reel layout

`symbols`, `reelSize` (stops per reel) and `columnCount` (number of reels).
They must match what the simulator expects.

### `fitnessVariables`: the targets

One list per game mode. Only the list for the current `gameMode` is used.

```yaml
fitnessVariables:
  BaseGame:
    - { type: baseRTP,         target: 0.57, weight: 10, enabled: true }
    - { type: baseHitRate,     target: 3,    weight: 5,  enabled: true }
    - { type: freeTriggerRate, target: 80,   weight: 3,  enabled: true }
  FreeGame:
    - { type: freeRTP,           target: 0.38, weight: 10, enabled: true }
    - { type: freeHitRate,       target: 2.7,  weight: 5,  enabled: true }
    - { type: freeRetriggerRate, target: 60,   weight: 4,  enabled: true }
```

- `target`: the value you want. Use the same units the simulator reports.
- `weight`: how much this goal matters compared with the others.
- `enabled: false`: ignore this goal without deleting the line.

Fitness = sum of `weight × |current − target| / target` over the enabled goals.

Types: `baseRTP`, `baseHitRate`, `freeRTP`, `freeHitRate`, `freeTriggerRate`,
`freeRetriggerRate`.

### `paths`

| Setting | What it is |
|---|---|
| `tempParentsFolder` | Working folder for reelset files during a run |
| `initialParentsFolder` | Where new random parents are written |
| `seedParentsFile` | Optional fixed starting parents (a JSON list of reelsets) |
| `resultFile` | Where results are saved |
| `simulatorPath` | The built simulator (step 5) |

### Config mistakes

The config is checked before any spinning starts, and mistakes give a one-line
message instead of a Python traceback:

```
CONFIG ERROR: 'Basegame' is not valid for run.gameMode. Choose one of: BaseGame, FreeGame
CONFIG ERROR: run.spins must be a whole number, got '10m'
```

YAML is sensitive to **indentation**: use spaces (never tabs), and keep items lined
up under their section exactly as in the original file.

---

## 8. Results and charts

Everything is saved in `Results/results.json`:

```
seed_<runNumber>                      <- BaseGame runs
  initial_population                  <- the parents the run started from
  results
    mutation_<n>
      <Replacement>_<Selection>
        results  [[best, mean], ...]  <- one entry per generation
        reelset  {BaseGameReel, FreeGameReel}   <- best reelset ever found
seed_<runNumber>_free                 <- FreeGame runs, same layout
```

To draw comparison charts (PNG files written to `Results/`):

```bash
python Optimizer/Compare.py
```

---

## 9. Troubleshooting

| Problem | Fix |
|---|---|
| `CONFIG ERROR: Simulator not found at ...` | Build the simulator (step 3) and set `simulatorPath` (step 5). On Windows the path ends in `.exe`. |
| `ModuleNotFoundError: No module named 'yaml'` | The virtual environment isn't active. Run the `activate` line from step 4. |
| `JSONDecodeError: Expecting value` | The simulator wrote no output, usually an old binary. Rebuild (step 3). |
| `myapp failed (...)` | The simulator crashed; its own error message is printed below this line. Run it by hand (step 3) to investigate. |
| Runs are very slow | Make sure you built with `-DCMAKE_BUILD_TYPE=Release` and `--config Release`. For tests, lower `spins`. |
| Linux link error mentioning `pthread` | Older Linux systems: add `find_package(Threads REQUIRED)` and `target_link_libraries(simulator PRIVATE Threads::Threads)` to `Simulator/CMakeLists.txt`, then rebuild. |
| `cmake` or `cl` not found on Windows | Use the **Developer PowerShell for VS 2022** from the Start menu. |
| `python3` not found on Windows | Use `python` instead of `python3`. |
| FreeGame run says no BaseGame results | Run BaseGame first with the same `runNumber` and the same `experiments`, or use `baseReelSource: manual`. |
| Free run seems to use other parents than the base run | Check that you didn't start the base run's `runNumber` twice with `createNewParents: true` (see section 7). |