# TiAI-MatBench

**A source-aware, executable benchmark for trustworthy materials-research agents.**

TiAI-MatBench evaluates whether an agent can complete a materials-research task while
preserving source identity, material state, test conditions, split integrity, evidential
scope and execution status. It does not award credit merely because an answer sounds
scientific, and it does not use another language model as the judge.

This directory is the **v0.1 public development set**. It is executable and CI-tested,
but its visible references make it unsuitable for headline leaderboard claims. A hidden,
externally adjudicated evaluation set is a later release milestone.

## What is different

The benchmark targets failure modes that ordinary materials question answering and
workflow-reproduction benchmarks do not isolate:

- pooled versus within-source inference;
- room-temperature versus high-temperature state boundaries;
- source-held-out evaluation and source leakage;
- task/query/source/evidence binding;
- unsupported causal or prospective claims;
- tool failure, missing artifacts and ambiguous serialization.

Seven tasks are derived from released TiAI titanium-alloy evidence and numerical replay.
One task is explicitly labeled `SYNTHETIC_SCORER_TEST`; it tests the evaluation harness and
must not be interpreted as evidence of materials-research capability.

## Frozen evidence base

The development set is bound to repository commit
`1f16938c615e5bbed742dc59faf168117dcd12fe`. Each allowed asset carries its Git blob SHA.
The grader rejects an unregistered asset, a mismatched blob identity, or a locator outside
the task's declared evidence scope. `verify-assets` recomputes Git blob identities from a
local checkout before a run.

## Install and run

The package has no runtime dependency outside the Python 3.11+ standard library.

```bash
python -m pip install -e ./matbench

tiai-matbench validate \
  --tasks matbench/tasks/dev.jsonl \
  --references matbench/references/dev.jsonl \
  --manifest matbench/MANIFEST.json

tiai-matbench verify-assets \
  --tasks matbench/tasks/dev.jsonl \
  --references matbench/references/dev.jsonl \
  --manifest matbench/MANIFEST.json \
  --repository-root .

tiai-matbench grade \
  --tasks matbench/tasks/dev.jsonl \
  --references matbench/references/dev.jsonl \
  --manifest matbench/MANIFEST.json \
  --submission matbench/examples/oracle_submission.jsonl \
  --output score_report.json
```

For an offline checkout without an editable install:

```bash
PYTHONPATH=matbench/src python -m tiai_matbench.cli validate \
  --tasks matbench/tasks/dev.jsonl \
  --references matbench/references/dev.jsonl \
  --manifest matbench/MANIFEST.json
```

## Submission contract

A submission is JSONL with one strict JSON object per answered task. Duplicate keys,
`NaN`, `Infinity` and unknown task IDs are rejected.

```json
{
  "schema": "tiai.matbench.response.v1",
  "task_id": "TMB-STAT-RT-001",
  "status": "ANSWERED",
  "answer": {
    "cohort": "rt",
    "pairs": 1233
  },
  "evidence": [
    {
      "asset": "数据/数值复现结果.json",
      "git_blob_sha": "b69588db6ee51b56439b3492faddf9f9367d745e",
      "locator": "/reports/material-relations/cohorts/rt"
    }
  ],
  "claims": [
    {
      "claim_id": "example",
      "scope": "descriptive",
      "support": "SUPPORTED"
    }
  ],
  "execution": {
    "success": true,
    "artifacts": [],
    "warnings": []
  }
}
```

## Scoring

The primary score is the unweighted macro-average across **real released tasks** after
critical gates. Scorer-only synthetic fixtures are reported separately and never contribute
to the scientific capability score. An all-task diagnostic is emitted only for harness
debugging.
Within a task, applicable dimensions use the manifest weights:

| Dimension | Weight |
| --- | ---: |
| outcome correctness | 0.30 |
| evidence fidelity | 0.25 |
| state/condition fidelity | 0.15 |
| split integrity | 0.10 |
| claim calibration | 0.15 |
| execution integrity | 0.05 |

A weighted average alone can hide scientifically fatal errors. TiAI-MatBench therefore
applies deterministic gates. Unregistered or mismatched evidence, state mixing, source
leakage, a wrong split unit, a fabricated value, an unsupported causal claim, or an
out-of-scope prospective answer can zero the task. Less severe failures cap the task score.
Every check, observed value, expected value and gate is emitted in the score report.

## Files

- `tasks/dev.jsonl`: prompts, frozen assets and allowed evidence locators;
- `references/dev.jsonl`: deterministic checks and critical-gate rules;
- `MANIFEST.json`: version, task accounting, weights and policy;
- `examples/oracle_submission.jsonl`: scorer regression fixture, not a model baseline;
- `examples/naive_submission.jsonl`: pooled-only/causal-error negative control;
- `src/tiai_matbench/`: strict parser, validator, asset verifier, grader and CLI;
- `tests/`: regression tests for leakage, state mixing, evidence fabrication and CLI use;
- `BENCHMARK_CARD.md`: scientific scope, governance and release plan;
- `RELATED_WORK.md`: benchmark boundary and the Matbench naming-collision note.

## Interpreting scores

The oracle fixture should score `1.0` on both the real-task primary metric and the synthetic
self-check. The deliberately incomplete pooled-only negative control scores very low and
triggers causal-calibration violations. Neither result is a claim about a language model. A
model comparison must record the exact model, prompt, tool permissions, retry policy, cost,
wall time and benchmark commit.
