"""
Run several run numbers (seeds) of the optimizer at the same time.

Run from the "Math Optimization" folder:

    python Optimizer/run_parallel.py launch GA-config.yaml --workers 6 --threads 10
    python Optimizer/run_parallel.py status GA-config.yaml
    python Optimizer/run_parallel.py merge  GA-config.yaml

launch  Starts one optimizer process per run number, at most --workers at a time.
        Each run gets its own folder Parallel/run_<n>/ with its own config, temp
        reelsets, initial parents and results file, so runs cannot overwrite each
        other's files. Each simulator call uses --threads threads (SIM_THREADS).
        A 10M-spin call has only 10 jobs, so --threads 10 is the useful maximum;
        a good --workers is (CPU cores) / threads.
        Runs that already finished are skipped, so after an interruption (e.g. a
        spot instance being reclaimed) just run the same command again.

status  Shows which runs are done, running or failed.

merge   Copies seed_<n> (and seed_<n>_free) of every finished run into the
        resultFile from the config. A backup of the old file is saved first.

pull    (needs --s3) Downloads the finished runs from S3 into Parallel/, e.g. on a
        new spot instance, so the next launch skips them.

Results are identical to running the same run numbers one after another:
every run is seeded only by its run number, never by timing or thread count.

Options:
    --runs 1-30       run numbers to do (default: run.runNumbers from the config)
    --workers N       runs at the same time (default: CPU cores // threads)
    --threads N       simulator threads per run (default: 10)
    --s3 URI          S3 location for uploads, e.g. s3://sim-result-temp/sweep1
                      launch: after each run finishes (or fails), uploads
                              <URI>/Parallel/run_<n>/{results.json, log.txt, config.yaml, DONE}
                      merge:  uploads the combined file to <URI>/results.json
                              (plus a timestamped copy, so no merge overwrites another)
                      pull:   downloads the finished runs back
                      Uses boto3 if installed, otherwise the aws CLI. A failed upload
                      is reported and retried at the end; it never stops the runs.

Example on a spot instance:
    python Optimizer/run_parallel.py pull   GA-config.yaml --runs 1-30 --s3 s3://sim-result-temp/sweep1
    python Optimizer/run_parallel.py launch GA-config.yaml --runs 1-30 --s3 s3://sim-result-temp/sweep1
    python Optimizer/run_parallel.py merge  GA-config.yaml --runs 1-30 --s3 s3://sim-result-temp/sweep1
"""
import argparse
import copy
import json
import os
import shutil
import subprocess
import sys
import time

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from Utility.Config import _run_numbers, ConfigError   # noqa: E402  same parsing as main.py

PARALLEL_DIR = "Parallel"
MAIN_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")


# ---------------------------------------------------------------- helpers
def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def read_json(path):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def write_json(data, path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)


def run_dir(n):
    return os.path.join(PARALLEL_DIR, f"run_{n}")


def done_marker(n):
    return os.path.join(run_dir(n), "DONE")


def keys_for_run(data, n):
    """The results keys a run owns: seed_<n> and seed_<n>_free (Both / FreeGame)."""
    return [k for k in data if k == f"seed_{n}" or k.startswith(f"seed_{n}_")]


# ---------------------------------------------------------------- S3
RUN_FILES = ["results.json", "log.txt", "config.yaml", "DONE"]   # DONE last: it marks a complete upload


class S3:
    """Uploads and downloads under one s3://bucket/prefix. boto3 if available, else the aws CLI."""

    def __init__(self, uri):
        if not uri.startswith("s3://"):
            sys.exit(f"ERROR: --s3 must look like s3://bucket/prefix, got '{uri}'")
        bucket, _, prefix = uri[5:].partition("/")
        if not bucket:
            sys.exit(f"ERROR: no bucket name in --s3 '{uri}'")
        self.bucket, self.prefix = bucket, prefix.strip("/")
        try:
            import boto3
            self.client = boto3.client("s3")
        except ImportError:
            self.client = None
            if shutil.which("aws") is None:
                sys.exit("ERROR: --s3 needs boto3 (pip install boto3) or the aws CLI")

    def key(self, *parts):
        return "/".join(p for p in (self.prefix, *parts) if p)

    def url(self, key):
        return f"s3://{self.bucket}/{key}"

    def upload(self, local, key):
        """True if uploaded. Never raises: a failed upload must not stop the runs."""
        try:
            if self.client:
                self.client.upload_file(local, self.bucket, key)
            else:
                subprocess.run(["aws", "s3", "cp", "--only-show-errors", local, self.url(key)],
                               check=True, capture_output=True, text=True)
            return True
        except Exception as e:     # noqa: BLE001  network, credentials, permissions ...
            msg = getattr(e, "stderr", "") or str(e)
            print(f"[s3] upload FAILED {local} -> {self.url(key)}: {msg.strip()}")
            return False

    def download(self, key, local):
        """True if downloaded, False if the object does not exist or cannot be read."""
        os.makedirs(os.path.dirname(local) or ".", exist_ok=True)
        try:
            if self.client:
                self.client.download_file(self.bucket, key, local)
            else:
                subprocess.run(["aws", "s3", "cp", "--only-show-errors", self.url(key), local],
                               check=True, capture_output=True, text=True)
            return True
        except Exception:          # noqa: BLE001  missing object is normal here
            return False

    def upload_run(self, n):
        """Upload one run's files. Returns True if all present files went up."""
        ok = True
        for name in RUN_FILES:
            local = os.path.join(run_dir(n), name)
            if os.path.exists(local):
                ok &= self.upload(local, self.key(PARALLEL_DIR, f"run_{n}", name))
        if ok:
            print(f"[s3] run {n} uploaded to {self.url(self.key(PARALLEL_DIR, f'run_{n}'))}/")
        return ok


def runs_from(args, raw):
    try:
        if args.runs:
            return _run_numbers({"runNumbers": [s.strip() for s in args.runs.split(",")]})
        return _run_numbers(raw.get("run") or {})
    except ConfigError as e:
        sys.exit(f"ERROR: {e}")


# ---------------------------------------------------------------- launch
def prepare_run(n, raw, main_results):
    """Create Parallel/run_<n>/ with its own config and files. Returns the config path."""
    d = run_dir(n)
    os.makedirs(d, exist_ok=True)

    cfg = copy.deepcopy(raw)
    cfg["run"]["runNumbers"] = [n]
    cfg["paths"]["tempParentsFolder"] = os.path.join(d, "TempParents")
    cfg["paths"]["initialParentsFolder"] = os.path.join(d, "InitialParents")
    cfg["paths"]["resultFile"] = os.path.join(d, "results.json")
    os.makedirs(cfg["paths"]["tempParentsFolder"], exist_ok=True)
    os.makedirs(cfg["paths"]["initialParentsFolder"], exist_ok=True)

    # Start from what the main results file already holds for this run (its saved
    # initial parents, and the BaseGame results a FreeGame 'same' run reads), so the
    # run behaves exactly as it would on its own. Only on the first launch.
    run_results = cfg["paths"]["resultFile"]
    if not os.path.exists(run_results):
        own = {k: main_results[k] for k in keys_for_run(main_results, n)}
        write_json(own, run_results)

    cfg_path = os.path.join(d, "config.yaml")
    with open(cfg_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, sort_keys=False)
    return cfg_path


def launch(args):
    raw = load_yaml(args.config)
    runs = runs_from(args, raw)
    cores = os.cpu_count() or 1
    threads = args.threads
    workers = args.workers or max(1, cores // threads)

    main_results = read_json((raw.get("paths") or {}).get("resultFile", ""))
    todo = [n for n in runs if not os.path.exists(done_marker(n))]
    skipped = len(runs) - len(todo)

    print(f"[parallel] {len(runs)} runs, {skipped} already done, {len(todo)} to do")
    print(f"[parallel] {workers} at a time x {threads} simulator threads "
          f"({workers * threads} of {cores} CPUs)")
    if workers * threads > cores:
        print("[parallel] WARNING: more threads than CPUs - runs will slow each other down")

    s3 = S3(args.s3) if args.s3 else None
    if s3:
        print(f"[s3] each finished run is uploaded to {s3.url(s3.key(PARALLEL_DIR))}/run_<n>/")

    env = dict(os.environ, SIM_THREADS=str(threads), PYTHONUNBUFFERED="1")
    queue = list(todo)
    active = {}            # run number -> (process, log file, start time)
    failed = []
    upload_retry = []      # runs whose upload failed; tried again at the end

    try:
        while queue or active:
            while queue and len(active) < workers:
                n = queue.pop(0)
                cfg_path = prepare_run(n, raw, main_results)
                log = open(os.path.join(run_dir(n), "log.txt"), "a", encoding="utf-8")
                log.write(f"\n===== started {time.ctime()} =====\n")
                log.flush()
                proc = subprocess.Popen([sys.executable, MAIN_SCRIPT, cfg_path],
                                        stdout=log, stderr=subprocess.STDOUT, env=env)
                active[n] = (proc, log, time.time())
                print(f"[parallel] started run {n} (log: {run_dir(n)}/log.txt)")

            time.sleep(2)
            for n, (proc, log, t0) in list(active.items()):
                code = proc.poll()
                if code is None:
                    continue
                log.close()
                minutes = (time.time() - t0) / 60
                del active[n]
                if code == 0:
                    with open(done_marker(n), "w") as f:
                        f.write(f"finished {time.ctime()} after {minutes:.1f} min\n")
                    print(f"[parallel] run {n} done in {minutes:.1f} min "
                          f"({len(runs) - len(queue) - len(active) - len(failed)}/{len(runs)} finished)")
                else:
                    failed.append(n)
                    print(f"[parallel] run {n} FAILED (exit {code}) - see {run_dir(n)}/log.txt")
                # upload either way: a failed run's log shows what went wrong
                if s3 and not s3.upload_run(n):
                    upload_retry.append(n)
    except KeyboardInterrupt:
        print("\n[parallel] stopping running processes ...")
        for proc, log, _ in active.values():
            proc.terminate()
        for proc, log, _ in active.values():
            proc.wait()
            log.close()
        print("[parallel] stopped. Run the same command again to continue.")
        sys.exit(1)

    if s3 and upload_retry:
        print(f"[s3] retrying uploads for runs {upload_retry}")
        still = [n for n in upload_retry if not s3.upload_run(n)]
        if still:
            print(f"[s3] WARNING: runs {still} are NOT in S3. Their files are in "
                  f"{PARALLEL_DIR}/run_<n>/ - copy them off before the instance goes away.")

    if failed:
        print(f"[parallel] {len(failed)} run(s) failed: {failed}. Fix the cause and launch again; "
              f"finished runs are skipped.")
    else:
        print("[parallel] all runs finished. Next: python Optimizer/run_parallel.py merge "
              f"{args.config}")


# ---------------------------------------------------------------- status / merge
def status(args):
    raw = load_yaml(args.config)
    for n in runs_from(args, raw):
        if os.path.exists(done_marker(n)):
            with open(done_marker(n)) as f:
                state = "done   " + f.read().strip()
        elif os.path.exists(os.path.join(run_dir(n), "log.txt")):
            state = "started (running, interrupted or failed - see log.txt)"
        else:
            state = "not started"
        print(f"run {n:>4}: {state}")


def merge(args):
    raw = load_yaml(args.config)
    target = (raw.get("paths") or {}).get("resultFile")
    if not target:
        sys.exit("ERROR: paths.resultFile is missing in the config")

    data = read_json(target)
    if data:
        backup = f"{target}.backup-{time.strftime('%Y%m%d-%H%M%S')}"
        shutil.copy2(target, backup)
        print(f"[merge] backup of {target} -> {backup}")

    merged, missing = [], []
    for n in runs_from(args, raw):
        if not os.path.exists(done_marker(n)):
            missing.append(n)
            continue
        own = read_json(os.path.join(run_dir(n), "results.json"))
        for key in keys_for_run(own, n):
            data[key] = own[key]
            merged.append(key)

    write_json(data, target)
    print(f"[merge] wrote {len(merged)} entries into {target}: {', '.join(merged) or 'none'}")
    if missing:
        print(f"[merge] not finished, not merged: {missing}")

    if args.s3:
        s3 = S3(args.s3)
        name = os.path.basename(target)
        stem, ext = os.path.splitext(name)
        stamped = f"{stem}-{time.strftime('%Y%m%d-%H%M%S')}{ext}"
        ok = s3.upload(target, s3.key(name)) & s3.upload(target, s3.key("merged", stamped))
        if ok:
            print(f"[s3] merged file uploaded to {s3.url(s3.key(name))} "
                  f"(copy: {s3.url(s3.key('merged', stamped))})")
        else:
            sys.exit("[s3] merged file upload FAILED - the merged file is still at " + target)


def pull(args):
    """Download finished runs from S3 into Parallel/run_<n>/ (e.g. on a new spot instance)."""
    if not args.s3:
        sys.exit("ERROR: pull needs --s3 s3://bucket/prefix")
    raw = load_yaml(args.config)
    s3 = S3(args.s3)
    got, absent = [], []
    for n in runs_from(args, raw):
        if os.path.exists(done_marker(n)):
            got.append(n)                      # already here
            continue
        base = s3.key(PARALLEL_DIR, f"run_{n}")
        # DONE is uploaded last, so its presence means the run's files are complete
        tmp_done = os.path.join(run_dir(n), "DONE.download")
        if not s3.download(f"{base}/DONE", tmp_done):
            absent.append(n)
            if os.path.exists(tmp_done):
                os.remove(tmp_done)
            continue
        complete = all(s3.download(f"{base}/{name}", os.path.join(run_dir(n), name))
                       for name in ("results.json", "config.yaml"))
        s3.download(f"{base}/log.txt", os.path.join(run_dir(n), "log.txt"))
        if complete:
            os.replace(tmp_done, done_marker(n))  # only now does launch treat it as done
            got.append(n)
        else:
            os.remove(tmp_done)
            absent.append(n)
    print(f"[pull] finished runs available here: {got or 'none'}")
    if absent:
        print(f"[pull] not finished in S3 (launch will run them): {absent}")


# ---------------------------------------------------------------- main
def main():
    p = argparse.ArgumentParser(description="Run several optimizer runs at the same time.")
    p.add_argument("command", choices=["launch", "status", "merge", "pull"])
    p.add_argument("config", nargs="?", default="GA-config.yaml")
    p.add_argument("--runs", help='run numbers, e.g. "1-30" or "1-10,15" (default: from config)')
    p.add_argument("--workers", type=int, default=0, help="runs at the same time")
    p.add_argument("--threads", type=int, default=10, help="simulator threads per run")
    p.add_argument("--s3", help="s3://bucket/prefix for uploads (launch, merge) and pull")
    args = p.parse_args()
    {"launch": launch, "status": status, "merge": merge, "pull": pull}[args.command](args)


if __name__ == "__main__":
    main()