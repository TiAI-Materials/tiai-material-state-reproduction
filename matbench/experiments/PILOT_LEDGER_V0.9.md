# PilotLedger v0.9 — frozen 192-slot planning and native-receipt auditing

Status: plan and audit code tested; **zero real TiAI Agent runs have been submitted**.

This implementation consumes the merged v0.8 `matched_goal_driven_protocol_v0.8.json` without changing its six conditions, twelve materials tasks, repetition schedule, execution modes or scientific prerequisites.

## Reproducible immutable pilot plan

```bash
PYTHONPATH=matbench/src python -m tiai_matbench.pilot_ledger plan \
  --protocol matbench/experiments/matched_goal_driven_protocol_v0.8.json \
  --output pilot_plan.json
```

Expected result: **192 paired slots = 32 paired sets × 6 arms; zero ready and 192 blocked when no independent input/model/provider/tool/budget/verifier bindings are supplied**. The protocol's canonical SHA-256 is `6d2673a95e1b6f731d1d83673ed42782efb0b3305bafd6ae7f58b113958b9001`.

Each deterministic slot contains run_id, pair_id, task, trial, condition, execution mode and native verifier. The slot-set digest detects modifications after preregistration. A plan is NOT a model run; synthetic fixtures and upstream CompMat outcomes are NOT TiAI empirical scores.

## Binding requirements

An external authorized runner may provide a separate JSON object with schema `tiai.agentbench.pilot_bindings.v0.9`, the exact `protocol_sha256`, pinned `model_id` and `provider_route`, `tool_allowlist`, `budgets_by_stratum`, and a `tasks` mapping for all 12 fixed task IDs. Each task maps to `input_commit_or_blob`, the exact v0.8 `native_verifier`, and exact `execution_mode`.

Freeze actual budgets BEFORE any outcome and keep them matched across all six conditions. The repository intentionally does not invent numeric token/time/GPU/dollar limits or claim to have model credentials. Binding cannot authorize modification of existing scientific owners.

To build a completely bound plan, add `--bindings pilot_bindings.json` to the plan command. This module does not itself launch external scientific solvers or agents; scientific work requires a native authorized harness.

## Independent native-verifier receipt

Successful execution claims require a trusted index exported independently by the benchmark's native evaluator, not by the tested Agent. The index maps each `receipt_id` to the SHA-256 digest of its canonical receipt. Each receipt contains schema `tiai.agentbench.native_receipt.v0.9`, receipt_id, run_id, task_id, verifier_id, and native_success.

**Important limitation:** matching an independently supplied digest detects inconsistency, but does not cryptographically authenticate an attacker-controlled trusted index. External verifier account isolation, read-only export and ideally detached signatures are prerequisites for real claims.

```bash
PYTHONPATH=matbench/src python -m tiai_matbench.pilot_ledger audit \
  --protocol matbench/experiments/matched_goal_driven_protocol_v0.8.json \
  --plan pilot_plan.json --ledger pilot_runs.jsonl \
  --trusted-receipts native_trusted_index.json --output pilot_audit.json
```

The audit requires every field listed in the original v0.8 run ledger; matches model/provider/tools/task/condition/trial/source/budget; rejects forged or missing native receipts; and checks artifact hashes, false completion, bounded scores, recovery and safety evidence. Missing/invalid runs remain visible within the 192-slot denominator. No synthetic record can be scored as a real Agent run.

Resource accounting may remain NULL when genuinely unobservable; it must not be silently replaced by zero. Safety is not inferred from a terminal result. A claimed native success without a trusted external receipt earns no credit. The module does not claim standalone certification of physical robot safety.

## Deterministic tests

```bash
PYTHONPATH=matbench/src python -m unittest discover -s matbench/tests -p test_pilot_ledger.py -v
```

The 20 synthetic positive/adversarial unit tests exercise six-arm matching, the 192-slot denominator, bindings, absent receipts, false completion, safety, missing provenance, budget mutation, duplicate runs, malformed cost, and dishonest VWR/RNU/FRR claims. They are harness checks, NOT new scientific experiments.

## Resource and empirical claim boundary

At this revision real provider credentials, input hashes, native independent receipt trust roots, live CompMat harness binding, and approved budgets remain unbound. Therefore real submitted runs = 0 and verified TiAI system effect estimate = UNKNOWN. Do not use A100 for JSON grading, do not compute on the office mother machine, and do not restart or interfere with active Ti65/TC4/Ti–B–W/recrystallization scientific owners.

Next admissible step: complete independent harness binding, then execute the already preregistered six matched conditions and report all real failures and successes without outcome-based task selection.