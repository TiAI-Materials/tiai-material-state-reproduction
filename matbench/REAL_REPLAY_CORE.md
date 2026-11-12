# RealReplayCore v0.5

RealReplayCore converts completed, failed and still-running professional work into source-bound evaluation tasks. It is the first empirical layer above the Goal-Driven protocol core: an agent must read immutable evidence, choose a bounded next action, preserve the scientific counterfactual and avoid false completion.

## Why this is a separate layer

A protocol regression proves that the evaluator can represent goals, criteria, recovery and human intervention. A real replay asks whether an agent makes the same defensible decision as an independent expert when given an actual research state. Expensive calculations are not repeated during ordinary replay evaluation; their frozen artifacts and provenance are reused, while small live-compute gates remain a separate track.

## Public and hidden split

`real_replay/contracts_v0.5.jsonl` publishes four task contracts and immutable source identities. The answer key, oracle submissions and adversarial submissions remain in an access-controlled scientific repository. This prevents public-answer leakage and avoids releasing unpublished numerical or mechanism results while still freezing the evaluation contract.

The first-wave materials tasks cover:

1. constraint-preserving alloy candidate adjudication;
2. matched TC4 DFT SCF continuity and downstream gating;
3. same-parent L160 static acceptance and hot-release gating;
4. Ti-B-W MLIP continuation and production-MD admission.

Together they exercise research operations, thermodynamics, DFT, MLIP/MD, mesoscale handoffs, multiscale consistency and campaign decisions. They intentionally include a positive selection, a continue-in-place decision, a terminal negative result and a resource-stop versus physics-stop distinction.

## Deterministic scoring

The grader checks five dimensions:

- decision correctness;
- required-action coverage and forbidden-action avoidance;
- immutable evidence-reference coverage;
- rationale-code coverage;
- claim-ceiling compliance.

Wrong decisions, forbidden actions, missing required evidence, claim-ceiling breaches and missing submissions are fatal. A run that claims completion despite a fatal or partial result receives `FALSE_COMPLETION_CLAIM` and zero score.

Primary outputs are macro score, human-work-weighted score, verified success rate, false-completion rate and verified human-baseline hours replaced. The four public contracts represent 720 baseline minutes, or 12 human-hours.

## Development regression

The unit tests contain a synthetic matched-calculation replay. The oracle continues the valid owner and holds downstream work; it must score 1.0. The adversarial run restarts the valid owner or breaches the claim ceiling and falsely declares completion; it must score zero.

The reusable Python API is:

```python
from tiai_matbench.io import read_jsonl
from tiai_matbench.real_replay import grade_replay_submission

report = grade_replay_submission(
    read_jsonl("tasks.jsonl"),
    read_jsonl("references.jsonl"),
    read_jsonl("submission.jsonl"),
)
```

## Scientific-extraction rule

A replay is admitted only when the source has a frozen commit, explicit artifact paths, a stable scientific state and an independently defensible next action. A failed or negative calculation is eligible and often more valuable than an easy positive result. A merely running job is eligible only when the decision itself is the research work—for example, whether to preserve a matched counterfactual or kill and restart it.

## Resource policy

RealReplayCore does not spend A100 or PC128 capacity to rerun already-frozen expensive calculations. Those resources remain assigned to the original Ti65 and TC4 scientific owners. A separate LiveComputeCore will contain only three small calculations that test environment setup, native execution, checkpoint recovery and source-bound result intake.

## Claim boundary

The contracts are real and source-bound, but the public repository does not expose their hidden scientific answers. Passing the public tests proves the evaluator works, not that an agent has replaced a materials scientist. Publication-grade claims require repeated hidden-pack runs, multiple agent baselines, contamination checks, external expert adjudication, one small live-compute pack and one certified digital-twin task.
