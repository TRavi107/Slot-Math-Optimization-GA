"""
Computing cost: the time of every simulator call, and the machine it ran on.

Every simulator call goes through Utility.Evaluate, which records it here:
    seconds      wall time of the call as the optimizer pays it (process start,
                 reading the reelset, spinning, writing and reading the JSON)
    simSeconds   time the simulator itself spent spinning (its "compute" block)
    spins, threads, baseOnly

main.py takes a mark() before a piece of work and since(mark) after it, so each
experiment gets exactly its own calls, without passing a timer through every
function. Nothing here changes any result: timing is recorded next to the
results, never used by the search.

What ends up in results.json:
    seed_<n> -> compute -> totalSeconds       total time of this stage of the run
    seed_<n> -> machines -> <id>              the machine description (CPU, threads, OS,
                                              compiler, build mode, ...)
    seed_<n> -> results -> mutation_<m> -> <combo> -> timing
                                              per experiment: total simulator time of the
                                              search, final check, wall time
"""
import hashlib
import json
import os
import platform
import subprocess
import sys

_CALLS = []          # one record per simulator call made by this process
_LAST_BUILD = {}     # the simulator's own "build" block, from the latest call


# =====================================================================
#  Call log
# =====================================================================
def record_call(seconds, spins, run_only_base, output):
    """Called by Utility.Evaluate after every simulator call."""
    global _LAST_BUILD
    comp = output.get("compute") or {}
    if output.get("build"):
        _LAST_BUILD = output["build"]
    _CALLS.append({
        "seconds": seconds,
        "simSeconds": comp.get("simSeconds"),
        "threads": comp.get("threads"),
        "hardwareThreads": comp.get("hardwareThreads"),
        "spins": int(spins),
        "baseOnly": bool(run_only_base),
    })


def mark():
    """Position in the call log; pass it to since() after the work is done."""
    return len(_CALLS)


def since(start, end=None):
    """The calls made between two marks (or from start until now)."""
    return _CALLS[start:end]


def _total(calls, key):
    vals = [c[key] for c in calls if c.get(key) is not None]
    return round(sum(vals), 4) if vals else None


def summary(calls):
    """Totals for a list of calls (no per-call record is kept)."""
    if not calls:
        return {"evaluations": 0, "seconds": 0.0}
    return {
        "evaluations": len(calls),
        "seconds": _total(calls, "seconds"),
        "simSeconds": _total(calls, "simSeconds"),
        "spins": sorted({c["spins"] for c in calls}),
        "threads": sorted({c["threads"] for c in calls if c["threads"] is not None}),
    }


def experiment_timing(start_calls, search_calls, final_calls, wall_seconds, machine_id):
    """
    Timing saved with one experiment (GA combination or baseline):
        evaluations                fitness evaluations in the search
        searchSeconds, simSeconds  their total time (wall, and simulator-only)
        startEvaluations           FreeGame 'same' only: evaluating the starting
                                   population on this experiment's own base reels
        finalCheck                 the high-spin re-check of the best reelset
        wallSeconds                the whole experiment, including the optimizer's own
                                   work (selection, files, saving results)
    """
    search = summary(search_calls)
    timing = {
        "machineId": machine_id,
        "wallSeconds": round(wall_seconds, 3),
        "spins": search.get("spins", []),
        "threads": search.get("threads", []),
        "evaluations": search["evaluations"],
        "searchSeconds": search["seconds"],
        "simSeconds": search.get("simSeconds"),
    }
    if start_calls:
        timing["startEvaluations"] = summary(start_calls)
    if final_calls:
        timing["finalCheck"] = summary(final_calls)
    simulated = sum(c["seconds"] for c in start_calls + search_calls + final_calls)
    timing["overheadSeconds"] = round(max(0.0, wall_seconds - simulated), 3)
    return timing


# =====================================================================
#  Machine description
# =====================================================================
def _run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def _cpu_linux():
    model, cores = None, set()
    phys = core = None
    try:
        with open("/proc/cpuinfo", encoding="utf-8") as f:
            for line in f:
                key, _, val = line.partition(":")
                key, val = key.strip(), val.strip()
                if key == "model name" and model is None:
                    model = val
                elif key == "physical id":
                    phys = val
                elif key == "core id":
                    core = val
                elif not key:                     # blank line ends one logical CPU
                    if core is not None:
                        cores.add((phys, core))
                    phys = core = None
        if core is not None:
            cores.add((phys, core))
    except OSError:
        pass
    mem = None
    try:
        with open("/proc/meminfo", encoding="utf-8") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    mem = int(line.split()[1]) / 1024 ** 2          # kB -> GB
                    break
    except OSError:
        pass
    return model, (len(cores) or None), mem


def _cpu_macos():
    model = _run(["sysctl", "-n", "machdep.cpu.brand_string"]) or None
    cores = _run(["sysctl", "-n", "hw.physicalcpu"])
    mem = _run(["sysctl", "-n", "hw.memsize"])
    return model, (int(cores) if cores.isdigit() else None), (int(mem) / 1024 ** 3 if mem.isdigit() else None)


def _cpu_windows():
    model = cores = mem = None
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                             r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
        model = winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
    except OSError:
        pass
    try:
        import ctypes

        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        mem = stat.ullTotalPhys / 1024 ** 3
    except (OSError, AttributeError):
        pass
    # try:
    #     import psutil                        # optional; only for the physical core count
    #     cores = psutil.cpu_count(logical=False)
    # except ImportError:
    #     pass
    return model, cores, mem


def _file_sha(path):
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()[:16]
    except OSError:
        return None


def machine_info(simulator_path):
    """
    The machine and simulator build that produced the timings. The simulator part
    comes from its own output, so call this after at least one evaluation.
    No host or user name is stored, so results.json can be published as is.
    """
    system = platform.system()
    model, cores, mem = {"Linux": _cpu_linux, "Darwin": _cpu_macos,
                         "Windows": _cpu_windows}.get(system, lambda: (None, None, None))()
    build = _LAST_BUILD or {}
    return {
        "cpu": model or platform.processor() or platform.machine(),
        "physicalCores": cores,
        "logicalCpus": os.cpu_count(),
        "memoryGB": round(mem, 1) if mem else None,
        "os": f"{system} {platform.release()}",
        "osVersion": platform.version(),
        "architecture": platform.machine(),
        "python": platform.python_version(),
        "compiler": build.get("compiler"),
        "buildType": build.get("buildType"),
        "optimized": build.get("optimized"),
        "cxxStandard": build.get("cxxStandard"),
        "simulatorSha256": _file_sha(simulator_path),
    }


def machine_id(info):
    """Short stable id: same CPU, OS and simulator build -> same id. Threads used are
    saved per experiment (timing -> threads), since they depend on the spin count."""
    keep = {k: info.get(k) for k in ("cpu", "logicalCpus", "os", "compiler", "buildType",
                                     "simulatorSha256")}
    return hashlib.sha1(json.dumps(keep, sort_keys=True).encode()).hexdigest()[:10]


def describe(info, threads=()):
    """One line for the console."""
    used = "/".join(str(t) for t in threads) or "?"
    return (f"{info.get('cpu')} | {used} of {info.get('logicalCpus')} threads | "
            f"{info.get('os')} | {info.get('compiler')} {info.get('buildType')}")


def warn_if_slow_build():
    """A Debug simulator is many times slower and makes every timing meaningless."""
    if _LAST_BUILD and _LAST_BUILD.get("optimized") is False:
        print("[compute] WARNING: the simulator was built WITHOUT optimisation "
              f"({_LAST_BUILD.get('buildType')}). Rebuild with -DCMAKE_BUILD_TYPE=Release; "
              "timings from this build are not representative.", file=sys.stderr)
    elif not _LAST_BUILD and _CALLS:
        print("[compute] NOTE: this simulator build does not report its compiler, build type "
              "or threads. Rebuild it from Simulator/src to record them.", file=sys.stderr)