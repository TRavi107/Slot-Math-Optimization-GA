"""
Deterministic seeds for the whole optimizer.

Everything random is derived from one master seed (run.runNumber), so the same
runNumber + config always reproduces the same results, byte for byte.

Never use Python's built-in hash() for this: it is salted per process.
"""
import hashlib
import random


def derive_seed(master, *labels) -> int:
    """Stable 64-bit seed from the master seed plus any labels (strings/ints)."""
    key = "|".join(str(x) for x in (master, *labels)).encode("utf-8")
    return int.from_bytes(hashlib.sha256(key).digest()[:8], "little")


def make_rng(master, *labels) -> random.Random:
    """Independent random.Random stream for one purpose (e.g. one GA combination)."""
    return random.Random(derive_seed(master, *labels))