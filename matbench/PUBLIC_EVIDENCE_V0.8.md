# PublicEvidenceCore v0.8

PublicEvidenceCore converts the published CompMat-Bench trajectory manifest into a frozen, outcome-complete empirical baseline for TiAI-AgentBench. It does not rerun expensive simulations and does not relabel upstream fixed-rule pass/fail outcomes.

## Why this is the next high-value step

The architecture, source-bound RealReplay tasks and external result adapters already exist. The publication-critical question is now empirical: does Goal-Driven persistence, independent verification, recovery and provenance improve verified work replacement under matched tasks and budgets?

Before testing that question, the public baseline must establish three quantities that a one-shot leaderboard hides:

1. sensitivity to methodological guidance on the same task and model;
2. stability over repeated trials of the same task;
3. degradation and interaction effects in complete long-horizon workflows.

The frozen evidence uses every public row in `reduced52`, `repeat20x5` and `workflow`, plus the same-task `full94` partners. No task is selected because of its outcome.

## Frozen source identity

- upstream repository: `cz2014/CompMat-Bench`;
- release: `v1.0.0`;
- commit: `03fec439ca9c9b1b14ea914896886b74d3e739bc`;
- trajectory manifest blob: `de6f82bc77a35b1a01d1d03a608c58e502e36516`;
- downloaded manifest SHA-256: `63e29888f514a139d2c0e20394d7d4e7a3fe08ea803232e6e8b3c991be0c5e22`.

The full public manifest contains 976 reported attempts and 771 native passes. PublicEvidenceCore uses a matched 756-attempt evidence matrix:

| Stratum | Design | Attempts |
| --- | --- | ---: |
| Same-task guidance | 52 tasks × 3 models × 2 guidance conditions | 312 |
| Repeated trials | 20 tasks × 3 models × 5 trials | 300 |
| Complete workflows | 8 workflows × 3 models × 2 guidance conditions × 3 trials | 144 |

## Finding 1: guidance sensitivity is horizon- and model-dependent

On the same 52 single-step tasks:

| Model | Full guidance | Reduced guidance | Difference |
| --- | ---: | ---: | ---: |
| DeepSeek v4.1 Flash | 33/52 = 63.5% | 28/52 = 53.8% | -9.6 percentage points |
| Gemini 3.8 Flash | 47/52 = 90.4% | 43/52 = 82.7% | -7.7 percentage points |
| GPT-5.6 Sol | 46/52 = 88.5% | 46/52 = 88.5% | 0.0 percentage points |

The exact paired McNemar p-values are 0.267, 0.219 and 1.000. These are descriptive published contrasts from one stochastic attempt per condition, not definitive causal estimates.

In complete workflows, the same models show larger and less uniform differences:

| Model | Long/full guidance (LG) | Abbreviated guidance (LA) | LA - LG |
| --- | ---: | ---: | ---: |
| DeepSeek v4.1 Flash | 10/24 = 41.7% | 12/24 = 50.0% | +8.3 pp |
| Gemini 3.8 Flash | 19/24 = 79.2% | 13/24 = 54.2% | -25.0 pp |
| GPT-5.6 Sol | 22/24 = 91.7% | 18/24 = 75.0% | -16.7 pp |

The DeepSeek reversal prevents a universal claim that more guidance always improves performance. The result supports interaction-aware, repeated evaluation rather than a single pooled effect.

## Finding 2: mean success and repeatability are separate capabilities

Across 20 tasks with five trials each:

| Model | Pass rate | Mixed-outcome tasks | Mean pairwise agreement |
| --- | ---: | ---: | ---: |
| DeepSeek v4.1 Flash | 62/100 = 62% | 11/20 | 0.73 |
| Gemini 3.8 Flash | 88/100 = 88% | 3/20 | 0.93 |
| GPT-5.6 Sol | 93/100 = 93% | 2/20 | 0.96 |

A system can therefore have an acceptable pooled success rate while remaining unreliable on individual scientific tasks. TiAI-AgentBench must report repeated-trial stability rather than treating one successful attempt as a stable capability.

One task, `task_202602_015_step_ws2-wse2-moire-lammps-inputs`, failed in all 15 published attempts across the three repeated-trial models. Seven tasks passed in all 15 attempts. These provide deterministic hard and easy controls for future harness checks, but they are not selected as the only evaluation tasks.

## Finding 3: complete workflows expose structured failure, not uniform difficulty

Aggregating the three models and three trials per guidance condition:

| Workflow | LG passes | LA passes | Interpretation boundary |
| --- | ---: | ---: | --- |
| C03 | 6/9 | 0/9 | strongly guidance-sensitive in this published sample |
| C05 | 9/9 | 9/9 | robust positive control |
| C06 | 2/9 | 1/9 | persistently difficult under both conditions |
| C07 | 9/9 | 9/9 | robust positive control |

The benchmark should therefore distinguish recoverable planning/guidance failures from persistent scientific or tooling failures. That distinction is exactly where Goal-Driven restart, verifier and provenance ablations become informative.

## Pre-registered next experiment

`experiments/matched_goal_driven_protocol_v0.8.json` freezes six system conditions:

1. single agent;
2. ordinary multi-agent;
3. Goal-Driven without an independent verifier;
4. Goal-Driven without recovery;
5. Goal-Driven without provenance and claim gates;
6. the full Goal-Driven system.

The 192-run materials pilot contains all four hidden RealReplay decisions, six hash-selected CompMat single-step tasks and two hash-selected complete workflows. The hash rule was frozen before TiAI outcomes. Pilot results remain separate from later cross-domain confirmatory results.

Every run must preserve the native verifier and record interventions, faults, recovery, restarts, artifacts, native success, claimed success, false completion, GDS, VWR, HLF, FCR, FRR, RNU, time, compute and cost.

## Claim boundary

PublicEvidenceCore v0.8 supports claims about the published CompMat-Bench trajectories: native success, same-task guidance contrasts, repeated-trial stability and workflow behavior.

It does not support claims that:

- TiAI-AgentBench or Goal-Driven already outperforms another system;
- 79 rerun records define complete infrastructure reliability;
- missing human-loop, cost, safety or false-completion metrics are zero;
- task-level evidence proves role, organization or industry replacement;
- a single published contrast establishes a causal effect.

Those claims require the pre-registered matched experiment, repeated runs, identical budgets, independent native verifiers and complete run ledgers.

## Resource policy

The public evidence extraction is a sub-megabyte JSON analysis. It used no A100 time and no scientific PC128 core-hours. The authorized 128-core node remains assigned to native scientific owners and to the two pre-registered workflow executions only when the matched harness is bound. Deterministic parsing and grading remain on CPU CI.
