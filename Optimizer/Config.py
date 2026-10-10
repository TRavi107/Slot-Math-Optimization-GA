import os
from dataclasses import dataclass

import yaml

from Parents import VariableType, FitnessVariable, GameMode
from Selection import SelectionTypes
from Replacement import ReplacementType


@dataclass
class Config:
    runNumber: int
    generations: int
    createNewParents: bool
    populationSize: int
    spins: int
    gameMode: GameMode
    finalCheckSpins: int

    # free game: where the fixed base reels come from
    freeGameBaseSource: str      # same | manual
    baseReelFile: str            # manual: single reelset file

    replacementTypes: list
    selectionTypes: list
    mutationCounts: list

    symbols: list
    reelSize: int
    columnCount: int

    fitnessVariables: list

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
    game_mode = _enum(GameMode, _get(run, "gameMode", "run"), "run.gameMode")

    # fitnessVariables is either one list (used in every mode) or one list per mode:
    #   fitnessVariables:
    #     BaseGame: [...]
    #     FreeGame: [...]
    fitness_raw = raw.get("fitnessVariables") or []
    section = "fitnessVariables"
    if isinstance(fitness_raw, dict):
        unknown = set(fitness_raw) - {m.name for m in GameMode}
        if unknown:
            raise ConfigError(f"fitnessVariables has unknown mode(s) {sorted(unknown)}. "
                              f"Use: {', '.join(m.name for m in GameMode)}")
        section = f"fitnessVariables.{game_mode.name}"
        fitness_raw = fitness_raw.get(game_mode.name) or []

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

    fg = raw.get("freeGame") or {}

    cfg = Config(
        runNumber=int(_get(run, "runNumber", "run")),
        generations=_positive_int(_get(run, "generations", "run"), "run.generations"),
        createNewParents=bool(_get(run, "createNewParents", "run")),
        populationSize=_positive_int(_get(run, "populationSize", "run"), "run.populationSize"),
        spins=_positive_int(_get(run, "spins", "run"), "run.spins"),
        gameMode=game_mode,
        finalCheckSpins=int(str(run.get("finalCheckSpins", 0)).replace("_", "")),

        freeGameBaseSource=str(fg.get("baseReelSource", "same")).strip().lower(),
        baseReelFile=str(fg.get("baseReelFile", "")),

        replacementTypes=[_enum(ReplacementType, n, "experiments.replacementTypes")
                          for n in _get(exp, "replacementTypes", "experiments")],
        selectionTypes=[_enum(SelectionTypes, n, "experiments.selectionTypes")
                        for n in _get(exp, "selectionTypes", "experiments")],
        mutationCounts=[_positive_int(m, "experiments.mutationCounts")
                        for m in _get(exp, "mutationCounts", "experiments")],

        symbols=[str(s) for s in _get(reels, "symbols", "reels")],
        reelSize=_positive_int(_get(reels, "reelSize", "reels"), "reels.reelSize"),
        columnCount=_positive_int(_get(reels, "columnCount", "reels"), "reels.columnCount"),

        fitnessVariables=fitness,

        folder=str(_get(paths, "tempParentsFolder", "paths")),
        parentsFolder=str(_get(paths, "initialParentsFolder", "paths")),
        seedParentsFile=str(paths.get("seedParentsFile", "Optimizer/ReelSets/seed_parents.json")),
        resultFile=str(_get(paths, "resultFile", "paths")),
        simulatorPath=str(_get(paths, "simulatorPath", "paths")),
    )

    if cfg.gameMode.name == "FreeGame":
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