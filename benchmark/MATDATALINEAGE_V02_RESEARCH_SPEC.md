# MatDataLineage v0.2 research specification

## Decision

The earlier broad framing, “TiAI-MatBench / SourceMatBench for source- and state-aware materials reasoning,” is rejected for two reasons:

1. `Matbench` is already an established Materials Project benchmark name.
2. MatScope (submitted 2026-11-09) now directly evaluates condition-specific material-state reasoning, cross-source integration and evolving experimental trajectories.

The defensible direction is therefore narrower:

> **Benchmark whether a materials research agent preserves the lineage of literature-derived data through curation, cohort construction, statistical/model evaluation and scientific claims.**

Working title:

**MatDataLineage: Benchmarking Source-Aware Data Analysis and Claim Traceability in Materials Research Agents**

## Evaluation object

`source asset → evidence record → material state → eligible cohort → split / estimand → executable artifact → calibrated claim`

A numerically correct endpoint receives zero when a hard lineage gate fails, including wrong source binding, incompatible state pairing, invalid cohort, paper-family leakage, wrong independent unit, invalid source-shift evaluation or unsupported claim scope.

## v0.2 implemented

- 25 public synthetic adversarial development tasks;
- deterministic declarative JSONL grader;
- hard gates and category/dimension/source-family macro metrics;
- source-bound TiAI seed registry;
- 9 passing unit tests;
- mixed smoke-test fixture: 0.76 strict pass rate, deliberately non-perfect and not model performance;
- benchmark card, landscape correction, annotation protocol, error taxonomy, roadmap and collaboration draft.

## Task families

1. evidence binding and unit/provenance fidelity;
2. state/endpoint/test-condition compatibility as a data-curation gate;
3. cohort construction and observation pairing;
4. paper-family leakage and split audit;
5. source-aware estimand and aggregation choice;
6. model evaluation for unseen-source generalization;
7. executable artifact and subset validity;
8. lineage completeness, calibrated claims and abstention.

## Required real pilot

- 24 controlled tasks from 12 authorized paper families;
- two independent annotations plus adjudication;
- accepted alternatives and adversarial wrong-lineage tests for every gate;
- no publisher PDF/XML redistribution;
- evaluator-only hidden gold;
- versioned hashes for source assets, task records, grader and artifacts.

## Minimum publication gate

- 120–200 tasks from at least 40 paper families;
- family-disjoint development/validation/hidden test;
- at least 30 paired counterfactual tasks;
- deterministic primary score and measured grader false-positive/false-negative rates;
- direct LLM, tool-agent and matched single-/multi-agent baselines;
- source/state/cohort/split ablations;
- random-row versus paper-family-held-out comparison;
- external audit of at least 20% of hidden tasks;
- documented rights and controlled-access procedure.

## Collaboration fit

RISE-X is methodologically relevant because Dong Yihong's work covers data contamination, execution-aware evaluation and multi-agent collaboration. OpenCollab can serve as a controlled harness only after the benchmark task and grader are frozen. The comparison must hold the underlying model, source access, tools, token budget and retries fixed; the research question is whether collaboration improves **scientific-lineage adherence**, not merely whether more agents complete more steps.

## Status boundary

This is an engineering and annotation scaffold. It is not yet a mature benchmark dataset, blind evaluation, agent leaderboard or publication-ready result.
