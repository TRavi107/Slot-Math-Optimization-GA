import json, subprocess, tempfile, os
from pathlib import Path

def Evaluate(spin_count, reelset_path, exe):
    fd, out_path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    try:
        proc = subprocess.run(
            [exe, str(spin_count), reelset_path, out_path],
            capture_output=True, text=True,
            stdin=subprocess.DEVNULL, timeout=3600,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"myapp failed ({proc.returncode}):\n{proc.stdout}{proc.stderr}")
        with open(out_path, encoding="utf-8") as f:
            return json.load(f)
    finally:
        os.remove(out_path)

# HERE = Path(__file__).resolve().parent
# reelset = HERE / "reelset.json"

# if not reelset.is_file():
#     raise FileNotFoundError(reelset)

# res = Evaluate(100_000_000, str(reelset))

# print(res["totalRTP"], res["baseRTP"])