import os
from dataclasses import dataclass

import yaml

from Parents import VariableType, FitnessVariable, GameMode
from Selection import SelectionTypes
from Replacement import ReplacementType
from Baselines import BaselineType

# run.gameMode: one of the GameMode stages, or BOTH_MODE = BaseGame then FreeGame
BOTH_MODE = "Both"
RUN_MODES = [m.name for m in GameMode] + [BOTH_MODE]


@dataclass
class Config:
    runNumber: int               # the run currently being executed (set per run by main.py)
    runNumbers: list             # every run to execute, in order
    generations: int
    populationSize: int
    spins: int
    gameMode: GameMode           # the stage currently being executed (set per stage by main.py)
    finalCheckSpins: int

    # run.gameMode as written in the config: BaseGame | FreeGame | Both
    runMode: str
    # stages run for every run number, in order: [BaseGame], [FreeGame] or [BaseGame, FreeGame]
    stages: list

    # free game: where the fixed base reels come from
    freeGameBaseSource: str      # same | manual  (Both always uses same)
    baseReelFile: str            # manual: single reelset file

    runGA: bool                  # false = skip the GA sweep, run only the baselines
    replacementTypes: list
    selectionTypes: list
    mutationCounts: list

    # baselines: same budget (generations), starting reelsets, spins and sim seed as the GA
    baselineTypes: list
    saStartTemperature: float
    saEndTemperature: float

    symbols: list
    reelSize: int
    columnCount: int

    fitnessVariables: list       # goals of the current stage
    fitnessByMode: dict          # GameMode -> goals, for every stage in `stages`

    folder: str
    parentsFolder: str
    seedParentsFile: str
    resultFile: str
    simulatorPath: str


class ConfigError(Exception):
    pass


def _get(section, key, section_name):
    if section is None or key not in section:
        raise ConfigError(f"Missing setting '{key}' under '{section_name}:' in the config file")
    return section[key]


def _enum(enum_cls, name, where):
    try:
        return enum_cls[str(name)]
    except KeyError:
        valid = ", ".join(e.name for e in enum_cls)
        raise ConfigError(f"'{name}' is not valid for {where}. Choose one of: {valid}") from None


def _positive_int(value, where):
    try:
        v = int(str(value).replace("_", ""))
    except ValueError:
        raise ConfigError(f"{where} must be a whole number, got '{value}'") from None
    if v <= 0:
        raise ConfigError(f"{where} must be greater than 0, got {v}")
    return v


def _non_negative_int(value, where):
    try:
        v = int(str(value).replace("_", "").strip())
    except ValueError:
        raise ConfigError(f"{where} must be a whole number, got '{value}'") from None
    if v < 0:
        raise ConfigError(f"{where} must be 0 or more, got {v}")
    return v


def _positive_float(value, where):
    try:
        v = float(value)
    except (TypeError, ValueError):
        raise ConfigError(f"{where} must be a number, got '{value}'") from None
    if v <= 0:
        raise ConfigError(f"{where} must be greater than 0, got {v}")
    return v


def _run_numbers(run):
    """
    run.runNumbers accepts:
        runNumbers: [1, 2, 3]        explicit list (recommended - easy to re-create one run)
        runNumbers: "1-30"           inclusive range, same as [1, 2, ..., 30]
        runNumbers: [1-10, 50]       ranges and numbers mixed
        runNumbers: 4                a single run
    The old single setting `runNumber: 4` still works.
    """
    if "runNumbers" in run:
        raw, where = run["runNumbers"], "run.runNumbers"
    elif "runNumber" in run:
        raw, where = run["runNumber"], "run.runNumber"
    else:
        raise ConfigError("Missing setting 'runNumbers' under 'run:' in the config file")

    items = raw if isinstance(raw, list) else [raw]
    numbers = []
    for item in items:
        text = str(item).strip()
        if "-" in text.lstrip("-"):                      # "a-b" range
            lo, hi = text.split("-", 1)
            lo = _non_negative_int(lo, where)
            hi = _non_negative_int(hi, where)
            if hi < lo:
                raise ConfigError(f"{where}: range '{text}' ends before it starts")
            numbers.extend(range(lo, hi + 1))
        else:
            numbers.append(_non_negative_int(text, where))

    if not numbers:
        raise ConfigError(f"{where} is empty - give at least one run number")
    dups = sorted({n for n in numbers if numbers.count(n) > 1})
    if dups:
        raise ConfigError(f"{where} lists these run numbers more than once: {dups}")
    return numbers


def _run_mode(run):
    """run.gameMode -> (mode name, [stages]). Both = BaseGame first, then FreeGame."""
    name = str(_get(run, "gameMode", "run")).strip()
    if name == BOTH_MODE:
        return BOTH_MODE, [GameMode.BaseGame, GameMode.FreeGame]
    if name not in RUN_MODES:
        raise ConfigError(f"'{name}' is not valid for run.gameMode. "
                          f"Choose one of: {', '.join(RUN_MODES)}")
    return name, [GameMode[name]]


def _fitness(raw, mode):
    """
    The goals for one stage. fitnessVariables is either one list (used in every mode)
    or one list per mode:
        fitnessVariables:
          BaseGame: [...]
          FreeGame: [...]
    """
    fitness_raw = raw.get("fitnessVariables") or []
    section = "fitnessVariables"
    if isinstance(fitness_raw, dict):
        unknown = set(fitness_raw) - {m.name for m in GameMode}
        if unknown:
            raise ConfigError(f"fitnessVariables has unknown mode(s) {sorted(unknown)}. "
                              f"Use: {', '.join(m.name for m in GameMode)}")
        section = f"fitnessVariables.{mode.name}"
        fitness_raw = fitness_raw.get(mode.name) or []

    fitness = []
    for i, fv in enumerate(fitness_raw, start=1):
        if not fv.get("enabled", True):
            continue
        where = f"{section} item {i}"
        fitness.append(FitnessVariable(
            _enum(VariableType, _get(fv, "type", where), f"{where} type"),
            0,                                   # current value, filled in by the simulator
            float(_get(fv, "target", where)),
            float(_get(fv, "weight", where)),
        ))
    if not fitness:
        raise ConfigError(f"No fitness goals enabled under {section} - "
                          "set 'enabled: true' on at least one")
    return fitness


def _baselines(raw):
    """
    Optional section; leaving it out runs no baselines (older configs keep working).
        baselines:
          methods: [RandomSearch, HillClimbing, SimulatedAnnealing]
          simulatedAnnealing: { startTemperature: 0.14, endTemperature: 0.002 }
    """
    bl = raw.get("baselines") or {}
    names = bl.get("methods") or []
    if not isinstance(names, list):
        names = [names]
    methods = [_enum(BaselineType, n, "baselines.methods") for n in names]
    dups = sorted({m.name for m in methods if methods.count(m) > 1})
    if dups:
        raise ConfigError(f"baselines.methods lists these more than once: {dups}")

    sa = bl.get("simulatedAnnealing") or {}
    t_start = _positive_float(sa.get("startTemperature", 0.14),
                              "baselines.simulatedAnnealing.startTemperature")
    t_end = _positive_float(sa.get("endTemperature", 0.002),
                            "baselines.simulatedAnnealing.endTemperature")
    if t_end > t_start:
        raise ConfigError("baselines.simulatedAnnealing: endTemperature must not be "
                          "higher than startTemperature")
    return methods, t_start, t_end


def LoadConfig(path="config.yaml"):
    if not os.path.exists(path):
        raise ConfigError(f"Config file not found: {path}")

    try:
        with open(path, encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ConfigError(f"Could not read {path} - check indentation and colons.\n{e}") from None

    run = raw.get("run")
    exp = raw.get("experiments")
    reels = raw.get("reels")
    paths = raw.get("paths")
    if run is None:
        raise ConfigError("Missing 'run:' section in the config file")
    run_mode, stages = _run_mode(run)
    fitness_by_mode = {mode: _fitness(raw, mode) for mode in stages}

    if "createNewParents" in run:
        print("[config] run.createNewParents is no longer used and is ignored: a run reuses "
              "its saved initial parents if there are any, otherwise it generates new ones "
              "seeded by the runNumber. You can delete that line.")

    fg = raw.get("freeGame") or {}
    base_source = str(fg.get("baseReelSource", "same")).strip().lower()
    if run_mode == BOTH_MODE and base_source != "same":
        print(f"[config] gameMode Both always takes each combination's base reels from its "
              f"own BaseGame result; freeGame.baseReelSource '{base_source}' is ignored.")
        base_source = "same"

    run_numbers = _run_numbers(run)
    baseline_types, sa_start, sa_end = _baselines(raw)

    cfg = Config(
        runNumber=run_numbers[0],
        runNumbers=run_numbers,
        generations=_positive_int(_get(run, "generations", "run"), "run.generations"),
        populationSize=_positive_int(_get(run, "populationSize", "run"), "run.populationSize"),
        spins=_positive_int(_get(run, "spins", "run"), "run.spins"),
        gameMode=stages[0],
        finalCheckSpins=int(str(run.get("finalCheckSpins", 0)).replace("_", "")),

        runMode=run_mode,
        stages=stages,

        freeGameBaseSource=base_source,
        baseReelFile=str(fg.get("baseReelFile", "")),

        runGA=bool((exp or {}).get("runGA", True)),
        replacementTypes=[_enum(ReplacementType, n, "experiments.replacementTypes")
                          for n in _get(exp, "replacementTypes", "experiments")],
        selectionTypes=[_enum(SelectionTypes, n, "experiments.selectionTypes")
                        for n in _get(exp, "selectionTypes", "experiments")],
        mutationCounts=[_positive_int(m, "experiments.mutationCounts")
                        for m in _get(exp, "mutationCounts", "experiments")],

        baselineTypes=baseline_types,
        saStartTemperature=sa_start,
        saEndTemperature=sa_end,

        symbols=[str(s) for s in _get(reels, "symbols", "reels")],
        reelSize=_positive_int(_get(reels, "reelSize", "reels"), "reels.reelSize"),
        columnCount=_positive_int(_get(reels, "columnCount", "reels"), "reels.columnCount"),

        fitnessVariables=fitness_by_mode[stages[0]],
        fitnessByMode=fitness_by_mode,

        folder=str(_get(paths, "tempParentsFolder", "paths")),
        parentsFolder=str(_get(paths, "initialParentsFolder", "paths")),
        seedParentsFile=str(paths.get("seedParentsFile", "Optimizer/ReelSets/seed_parents.json")),
        resultFile=str(_get(paths, "resultFile", "paths")),
        simulatorPath=str(_get(paths, "simulatorPath", "paths")),
    )

    if not cfg.runGA and not cfg.baselineTypes:
        raise ConfigError("experiments.runGA is false and baselines.methods is empty - "
                          "nothing to run")
    if cfg.runMode == "FreeGame":
        src = cfg.freeGameBaseSource
        if src not in ("same", "manual"):
            raise ConfigError(f"freeGame.baseReelSource '{src}' must be same or manual")
        if src == "manual" and not os.path.isfile(cfg.baseReelFile):
            raise ConfigError(f"freeGame.baseReelFile not found: '{cfg.baseReelFile}'")
    if cfg.finalCheckSpins < 0:
        raise ConfigError("run.finalCheckSpins must be 0 (off) or a positive number")
    if not os.path.isfile(cfg.simulatorPath):
        raise ConfigError(
            f"Simulator not found at '{cfg.simulatorPath}'. Build it first or fix paths.simulatorPath")

    return cfg