# TiAI-MatBench v0.1 research specification

## Status

- 20-task adversarial development set implemented.
- Deterministic declarative grader implemented; primary score does not use an LLM judge.
- Nine unit tests passed on 2026-11-12.
- Deliberately mixed correct/incorrect smoke-test submissions achieved 75% strict pass rate. This is a judge smoke test, not model performance.
- This branch is a review draft. It does not change the published numerical analyses or claim a validated leaderboard.

## Research position

Working paper name: **SourceMatBench: Benchmarking Evidence- and State-Aware Reasoning in Materials Research Agents**.

The benchmark asks whether an agent preserves the full chain:

`source → material state → test condition → analysis cohort → executable result → calibrated claim`.

The gap is narrower than “materials-agent evaluation.” Existing work already covers scientific code generation, computational-materials claim reproduction, materials software operation, and evidence extraction. The proposed contribution is the combination of:

1. paper-family-disjoint evaluation rather than random-row testing;
2. explicit material-state, endpoint and test-condition compatibility;
3. source-macro versus row-macro statistical reasoning;
4. paired adversarial tasks where one source/state change flips the valid conclusion;
5. deterministic grading of provenance, analysis scope and claim strength;
6. open and controlled tracks that do not redistribute publisher full text.

## Implemented task categories

- evidence extraction and unit/provenance fidelity;
- material-state and test-condition comparability;
- source-family leakage detection and split design;
- source-aware statistics and aggregation reversal;
- calibrated claims and abstention;
- distinction between executable success and scientific support.

## Hard scientific gates

A task score is forced to zero when the submission violates a declared hard gate, including wrong source, wrong endpoint/unit, material-state mismatch, source leakage, wrong analysis subset or unsupported non-abstention. A numerically correct final value is insufficient when its evidence chain is invalid.

## Existing TiAI assets reused

- `数据/科研抽取任务与提示.jsonl`: source- and state-scoped extraction task contracts;
- `数据/科研抽取参考标注.jsonl`: source-bound references and evidence locators;
- `代码/文献抽取评分协议.py`: existing extraction scorer;
- source-aware and paper-family-held-out analyses in the TiAI release repositories.

The prototype references these assets by repository path, DOI, observation ID and source hash. It does not copy publisher XML/PDF into the public package.

## Acceptance gates before publication

- 120–200 tasks from at least 40 independent paper families;
- family-disjoint private test set with no development feedback;
- two independent domain annotations plus adjudication for every hidden task;
- explicit grader false-positive/false-negative audit;
- matched model, tool, runtime, token and retry budgets;
- deterministic, direct-LLM and tool-agent baselines;
- ablations for source metadata, material-state metadata and executable checks;
- external audit of at least 20% of hidden tasks;
- documented source-asset rights and controlled-access process.

## Package

The companion ZIP contains the complete v0.1 Python package, development tasks, gold checks, seed registry, schemas, documentation, collaboration draft and test suite. It runs with Python 3.11+ and no third-party dependencies.
