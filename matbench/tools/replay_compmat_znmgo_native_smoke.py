"""Reproduce one CompMat-Bench native grader reference/negative-control smoke test.

This is SOURCE-ONLY grader validation, not a staged-input or Agent pilot run.
No credentials or native reference files are exported to tested Agents.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from urllib.request import Request, urlopen

TASK = "task_202603_007_step_znmgo-strain-composition-phase-map"
TREE = "f261454f7a57999e50186a906da9c747d16c1066"
COMMIT = "03fec439ca9c9b1b14ea914896886b74d3e739bc"
BASE = "https://api.github.com/repos/cz2014/CompMat-Bench/"
HEADERS = {"User-Agent": "TiAI-AgentBench-Native-Reference-Selftest",
           "Accept": "application/vnd.github+json"}


def upstream(path: str) -> dict:
    with urlopen(Request(BASE + path, headers=HEADERS), timeout=40) as handle:
        return json.load(handle)


def git_blob_sha256(data: bytes) -> tuple[str, str]:
    header = b"blob " + str(len(data)).encode("ascii") + b"\0"
    return hashlib.sha1(header + data).hexdigest(), hashlib.sha256(data).hexdigest()


def evaluate(grader: Path, workspace: Path, cwd: Path) -> dict:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", OMP_NUM_THREADS="1")
    result = subprocess.run(
        [sys.executable, "-B", str(grader), str(workspace)],
        cwd=cwd, env=env, text=True, errors="replace",
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60,
        check=False,
    )
    scores = [line.partition(":")[2].strip()
              for line in result.stdout.splitlines() if line.startswith("SCORE:")]
    score = int(scores[-1]) if result.returncode == 0 and scores and scores[-1] in {"0", "1"} else None
    return {
        "score": score,
        "returncode": result.returncode,
        "stdout_sha256": hashlib.sha256(result.stdout.encode()).hexdigest(),
        "stderr_tail": result.stderr.splitlines()[-4:],
    }


def reproduce() -> dict:
    report = {
        "schema": "tiai.agentbench.compmat_native_reference_selftest.v0.13",
        "task_id": TASK, "upstream_commit": COMMIT,
        "official_tree_sha": TREE, "source_mode": "GIT_BLOBS_NOT_CORE_RELEASE",
        "core_asset_sha256_verified": False, "native_dispatch_allowed": False,
        "real_tiai_agent_runs": 0, "pilot_ready_slots": 0,
    }
    tree = upstream("git/trees/" + TREE + "?recursive=1")
    if tree.get("truncated"):
        raise ValueError("upstream Git tree was truncated")
    entries = sorted(
        (f for f in tree["tree"]
         if f["type"] == "blob" and f["path"].startswith("grader/")),
        key=lambda f: f["path"],
    )
    if len(entries) != 4:
        raise ValueError("unexpected grader file count")
    with tempfile.TemporaryDirectory(prefix="tiai-compmat-native-") as tmp:
        root = Path(tmp)
        grader_root = root / "official_grader"
        files = []
        for entry in entries:
            blob = upstream("git/blobs/" + entry["sha"])
            if blob.get("encoding") != "base64":
                raise ValueError("unrecognized Git blob encoding")
            data = base64.b64decode(blob["content"], validate=False)
            git_sha, sha256 = git_blob_sha256(data)
            if git_sha != entry["sha"]:
                raise ValueError("blob identity mismatch: " + entry["path"])
            dest = grader_root / entry["path"]
            if ".." in dest.relative_to(grader_root).parts:
                raise ValueError("unsafe grader path")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            files.append({
                "path": entry["path"], "byte_size": len(data),
                "git_blob_sha": git_sha, "sha256": sha256,
            })
        reference = grader_root / "grader" / "reference_submission"
        script = grader_root / "grader" / "grader.py"
        positive = evaluate(script, reference, grader_root)
        bad = root / "corrupt_control"
        bad.mkdir()
        data = json.loads((reference / "answer.json").read_text(encoding="utf-8"))
        field = "M_R111_x0_GPa"
        if field not in data:
            raise ValueError("cannot construct the preregistered negative control")
        data[field] = float(data[field]) * 4.0 if data[field] else 1000000.0
        (bad / "answer.json").write_text(json.dumps(data), encoding="utf-8")
        negative = evaluate(script, bad, grader_root)
    passed = (positive["score"] == 1 and positive["returncode"] == 0 and
              negative["score"] == 0 and negative["returncode"] == 0)
    report.update(
        git_blob_integrity=True, files=files,
        reference_native_evaluation=positive,
        corrupt_native_evaluation=negative,
        actual_reference_score=positive["score"],
        actual_corrupt_control_score=negative["score"],
        selftest_pass=passed,
        status=("REFERENCE_NATIVE_GRADER_SELFTEST_PASS" if passed
                else "REFERENCE_NATIVE_GRADER_SELFTEST_FAIL"),
        claim_boundary="Upstream source-only grader self-test, not release-core staging or a TiAI Agent result.",
    )
    return report


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    report = reproduce()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({"status": report["status"],
                      "reference": report["actual_reference_score"],
                      "corrupt_control": report["actual_corrupt_control_score"],
                      "agent_runs": 0}))
    return 0 if report["selftest_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
