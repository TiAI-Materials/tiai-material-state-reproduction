"""Execute the frozen BaTiO3 dislocation-dipole *official* CompMat native grader.
This is a reference-grader self-test, never an agent run, and it does not
stage release-core simulation inputs or expose private grader bytes to agents.
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

TASK = "task_202603_034_step_batio3-dislocation-dipole-relaxed"
TREE = "cc0f9a2fc727a9bdab09a6e6e8328b0a1358dafa"
COMMIT = "03fec439ca9c9b1b14ea914896886b74d3e739bc"
BASE = "https://api.github.com/repos/cz2014/CompMat-Bench/"
HEADERS = {"User-Agent": "TiAI-AgentBench-BaTiO3-Native-Reference-Selftest",
           "Accept": "application/vnd.github+json"}


def upstream(path: str) -> dict:
    with urlopen(Request(BASE + path, headers=HEADERS), timeout=45) as handle:
        return json.load(handle)


def file_digests(data: bytes) -> tuple[str, str]:
    git_header = b"blob " + str(len(data)).encode("ascii") + b"\0"
    return hashlib.sha1(git_header + data).hexdigest(), hashlib.sha256(data).hexdigest()


def grade_native(script: Path, workspace: Path, cwd: Path) -> dict:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", OMP_NUM_THREADS="1")
    p = subprocess.run([sys.executable, "-B", str(script), str(workspace)],
                       cwd=cwd, env=env, text=True, errors="replace",
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       timeout=60, check=False)
    head, marker, tail = p.stdout.rpartition("SCORE:")
    score = int(tail.strip()) if p.returncode == 0 and marker and tail.strip() in {"0", "1"} else None
    details = json.loads(head) if marker else {}
    return {"score": score, "returncode": p.returncode,
            "accepted_naming_convention": details.get("accepted_naming_convention"),
            "stdout_sha256": hashlib.sha256(p.stdout.encode()).hexdigest(),
            "stderr_tail": p.stderr.splitlines()[-4:]}


def reproduce() -> dict:
    tree = upstream("git/trees/" + TREE + "?recursive=1")
    if tree.get("sha") != TREE or tree.get("truncated"):
        raise ValueError("Git tree identity or truncation error")
    entries = sorted((x for x in tree["tree"] if x["type"] == "blob" and
                      x["path"].startswith("grader/")), key=lambda x: x["path"])
    required = {"grader/grader.py", "grader/graderlib/grader_numeric.py",
                "grader/ground_truth.json", "grader/reference_submission/answer.json"}
    if {x["path"] for x in entries} != required:
        raise ValueError("unexpected official grader files")
    report = {
        "schema": "tiai.agentbench.compmat_dislocation_native_selftest.v0.14",
        "task_id": TASK, "upstream_commit": COMMIT,
        "official_tree_sha": TREE, "source_mode": "GIT_BLOBS_NOT_CORE_RELEASE",
        "core_asset_sha256_verified": False, "native_dispatch_allowed": False,
        "real_tiai_agent_runs": 0, "pilot_ready_slots": 0,
    }
    with tempfile.TemporaryDirectory(prefix="tiai-compmat-batio3-") as tmp:
        root = Path(tmp)
        src = root / "native_scorer_private"
        files = []
        for entry in entries:
            raw = upstream("git/blobs/" + entry["sha"])
            if raw.get("encoding") != "base64":
                raise ValueError("unexpected Git blob encoding")
            data = base64.b64decode(raw["content"])
            git_sha, sha256 = file_digests(data)
            if git_sha != entry["sha"]:
                raise ValueError("official Git blob identity mismatch")
            target = src / entry["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            files.append({"path": entry["path"], "byte_size": len(data),
                          "git_blob_sha": git_sha, "sha256": sha256})
        script = src / "grader" / "grader.py"
        original = src / "grader" / "reference_submission"
        ans = json.loads((original / "answer.json").read_text(encoding="utf-8"))
        if ans["min_contact_nearest_core"] != "TiO2":
            raise ValueError("upstream reference has changed")
        # Two valid conventions MUST be accepted by this exact official scorer.
        # Then reject two physically inconsistent mutations, no local grader patches.
        variants = {"identity_reference": ans}
        swapped = dict(ans)
        swapped["core_BaO_xy_A"] = ans["core_TiO2_xy_A"]
        swapped["core_TiO2_xy_A"] = ans["core_BaO_xy_A"]
        swapped["min_contact_nearest_core"] = "BaO"
        variants["coherent_global_swap"] = swapped
        bad_label = dict(ans)
        bad_label["min_contact_nearest_core"] = "BaO"
        variants["incoherent_label_only_swap"] = bad_label
        bad_value = dict(ans)
        bad_value["ba_spacing_x_region_A_A"] = float(ans["ba_spacing_x_region_A_A"]) + 0.2
        variants["corrupted_spacing"] = bad_value
        results = {}
        for name, payload in variants.items():
            wd = root / name
            wd.mkdir()
            (wd / "answer.json").write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
            results[name] = grade_native(script, wd, src)
    expected = {
        "identity_reference": (1, "identity"),
        "coherent_global_swap": (1, "BaO_TiO2_swapped"),
        "incoherent_label_only_swap": (0, None),
        "corrupted_spacing": (0, None),
    }
    passed = all(results[n]["score"] == ex_score and
                 results[n]["accepted_naming_convention"] == ex_name and
                 results[n]["returncode"] == 0
                 for n, (ex_score, ex_name) in expected.items())
    report.update(git_blob_integrity=True, files=files, evaluations=results,
                  expected_scores={k: v[0] for k, v in expected.items()},
                  selftest_pass=passed,
                  status="NATIVE_EQUIVALENCE_SELFTEST_PASS" if passed else "NATIVE_EQUIVALENCE_SELFTEST_FAIL",
                  execution_kind="OFFICIAL_UPSTREAM_REFERENCE_GRADER_SELFTEST_NOT_AGENT_EVALUATION",
                  claim_boundary=("Official source-only grader tested for coherent crystal-core naming "
                                  "equivalence and false-positive avoidance. No core inputs staged, "
                                  "no independent production signature, no TiAI Agent results."))
    return report


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = reproduce()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"],
                      "scores": {k: v["score"] for k, v in result["evaluations"].items()},
                      "real_agent_runs": 0}))
    return 0 if result["selftest_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
