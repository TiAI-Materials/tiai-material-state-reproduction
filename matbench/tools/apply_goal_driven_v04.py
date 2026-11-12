"""One-time verified bootstrap for TiAI-AgentBench Goal-Driven Core v0.4."""
from __future__ import annotations

import base64
import gzip
import hashlib
import json
import shutil
from pathlib import Path

PAYLOAD_SHA256 = "d51047295cf3aefb3db80f6b928c8f32c17664cc6ad1dfbf2d0452a7814b7eba"
EXPECTED_FILES = 25
PARTS = (
    "part01.txt",
    "part02.txt",
    "part03.txt",
    "part04a.txt",
    "part04b.txt",
    "part05.txt",
)


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    payload_dir = root / "matbench" / "tools" / "goal_driven_v04_payload"
    encoded = "".join(
        (payload_dir / name).read_text(encoding="utf-8").strip()
        for name in PARTS
    )
    compressed = base64.b64decode(encoded)
    observed = hashlib.sha256(compressed).hexdigest()
    if observed != PAYLOAD_SHA256:
        raise SystemExit(f"payload SHA-256 mismatch: {observed}")

    files = json.loads(gzip.decompress(compressed).decode("utf-8"))
    if len(files) != EXPECTED_FILES:
        raise SystemExit(f"payload file count mismatch: {len(files)}")
    for relative, content in files.items():
        target = (root / relative).resolve()
        if root != target and root not in target.parents:
            raise SystemExit(f"unsafe payload path: {relative}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    shutil.rmtree(payload_dir)
    (root / "matbench" / "tools" / "apply_goal_driven_v04.py").unlink()
    (root / ".github" / "workflows" / "apply_goal_driven_v04.yml").unlink()
    print(f"applied {len(files)} Goal-Driven Core v0.4 files")


if __name__ == "__main__":
    main()
