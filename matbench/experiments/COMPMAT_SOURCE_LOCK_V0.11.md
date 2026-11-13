# CompMat public source lock v0.11 — bounded input-identity advance

This record resolves which official CompMat-Bench Git directories and published release package contain the eight public tasks selected in the frozen v0.8 matched experiment. It does **not** claim that the native input archive has been downloaded, that complete workspaces are hashed, or that any new Agent run is completed.

## Pinned upstream

- Repository: https://github.com/cz2014/CompMat-Bench
- Release: https://github.com/cz2014/CompMat-Bench/releases/tag/v1.0.0 (published 2026-10-16).
- Commit: 03fec439ca9c9b1b14ea914896886b74d3e739bc.
- Published core package name: compmat_bench_core.zip.
- Published core package size: 516859324 bytes.
- Publisher-reported SHA-256: 6be09447536a8d3e23aa9e21e3cea3864380ad1a7c841fb9970930b008f067bb.
- Source and task Git-tree SHA identities for all eight frozen public tasks: see companion machine-readable JSON.
- Native bytes actually downloaded and independently hashed during this change: **NONE**.

The [upstream download guide](https://github.com/cz2014/CompMat-Bench/blob/03fec439ca9c9b1b14ea914896886b74d3e739bc/docs/download.md) explicitly states that a Git clone lacks some release-staged simulation inputs. The six frozen step tasks do not appear among the five supplemental heavy-input exceptions, so the core package is the relevant first download. The two selected workflows C03/C07 are part of the released core. [Upstream evaluation instructions](https://github.com/cz2014/CompMat-Bench/blob/03fec439ca9c9b1b14ea914896886b74d3e739bc/docs/evaluation.md) require isolated agent workspaces, private native graders, no internet access, and separate reference-submission grader checks.

C03 is the BAs force-constant/isotope-disorder/near-field workflow. C07 is the V2CoAl magnetic ordering and exchange workflow, and **requires separately licensed VASP POTCAR files that are excluded from the upstream release**. No actual POTCAR entitlement has been verified. Git tree hashes alone do not authorize a VASP workflow run, and generic installed software is not equivalent to matching the upstream runtime version.

## Frozen experimental continuity

The inventory records six exact v0.8 public step IDs, two workflow IDs C03/C07, and all four private RealReplay IDs. It does not change any task, trial count, condition, mode, grader identity or owner. Four private task inputs and hidden verifier credentials stay unbound. No model route, allowed-tool list, frozen cost budget, independent verifier key, release archive checksum, extracted-workspace hash, or native reference-grader receipt has been fabricated.

Expected deterministic source-identity report: 6 public step source pins; 2 public workflow source pins; 4 private tasks unbound; 0 verified staged workspaces; 0 verified native grader runs; 0 real Agent runs; **0 legitimate READY / 192 BLOCKED**.

Use the standard-library validator:

```bash
PYTHONPATH=matbench/src python -m tiai_matbench.compmat_source_identity \
  --protocol matbench/experiments/matched_goal_driven_protocol_v0.8.json \
  --inventory matbench/experiments/COMPMAT_SOURCE_IDENTITY_V0.11.json \
  --output /tmp/compmat_source_preflight.json
```

The next admissible action is staging only the frozen public packages on an isolated authorized worker, checking the **actual** downloaded SHA-256 against the publisher digest, hashing the **complete** extracted agent inputs, performing upstream reference-grader self-tests outside the agent environment, verifying C07 licensed POTCAR availability, and then freezing model/provider/tools/budgets and the independent verifier trust root. These preparatory checks are not TiAI benchmark system performance.

This is evidence of published source provenance, not of native execution or Goal-Driven advantage. No heavy A100/Colab/PC128 task is justified for this Git metadata-only step.
