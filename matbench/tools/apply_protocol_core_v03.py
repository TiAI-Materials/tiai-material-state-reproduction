"""One-time verified bootstrap for TiAI-AgentBench ProtocolCore v0.3."""
from __future__ import annotations

import base64
import gzip
import hashlib
import json
import shutil
from pathlib import Path

PAYLOAD_SHA256 = "7bed7296fc002840921ef68bed6b9181ef7c74dea0131caa69b385082133c846"


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    payload_dir = root / "matbench" / "tools" / "protocol_core_v03_payload"
    encoded = "".join(
        part.read_text(encoding="utf-8").strip()
        for part in sorted(payload_dir.glob("part*.txt"))
    )
    compressed = base64.b64decode(encoded)
    observed = hashlib.sha256(compressed).hexdigest()
    if observed != PAYLOAD_SHA256:
        raise SystemExit(f"payload SHA-256 mismatch: {observed}")

    files = json.loads(gzip.decompress(compressed).decode("utf-8"))
    for relative, content in files.items():
        target = (root / relative).resolve()
        if root != target and root not in target.parents:
            raise SystemExit(f"unsafe payload path: {relative}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    shutil.rmtree(payload_dir)
    (root / "matbench" / "tools" / "apply_protocol_core_v03.py").unlink()
    (root / ".github" / "workflows" / "apply_protocol_core_v03.yml").unlink()
    print(f"applied {len(files)} ProtocolCore v0.3 files")


if __name__ == "__main__":
    main()
