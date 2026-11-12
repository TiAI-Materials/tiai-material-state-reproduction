# FederationCore v0.6

FederationCore connects TiAI-AgentBench to mature external benchmarks instead of rebuilding their environments or redefining their success criteria. It operationalizes the broad Goal-Driven thesis at the benchmark level: every profession may require different native tools and verifiers, but completed work can still be represented through common goal, execution, evidence, recovery, resource and claim-boundary contracts.

## Design rule

The upstream benchmark remains authoritative for native task success.

FederationCore may normalize an observable quantity, but it must not infer unreported capability. In particular:

- a solved SWE-bench issue is not evidence of low human intervention or low cost;
- an OSWorld evaluator score is not evidence that the entire desktop trajectory was safe;
- a CALVIN task success is not evidence of collision, force, contamination or sample-identity safety;
- a cataloged upstream project is not executable until its exact result schema has a tested adapter;
- a domain with no mature open benchmark remains a visible gap rather than receiving a synthetic success score.

## Executable adapters

The first release implements three native-result adapters:

1. `SWE_BENCH_RESULTS_V2`
   - reads the upstream `results.json` fields emitted by `swebench/harness/reporting.py`;
   - preserves the full task denominator;
   - distinguishes resolved, completed, error and infrastructure-failure counts.

2. `OSWORLD_RESULTS_V1`
   - reads the upstream summary list emitted by `lib_results_logger.py`;
   - keeps unscored errors in the denominator;
   - reports mean native evaluator score, execution coverage and infrastructure reliability.

3. `CALVIN_RESULTS_V1`
   - reads the upstream epoch-keyed `results.json`;
   - follows the native best-average-sequence-length selection rule;
   - reports task success, normalized long-horizon depth and five-instruction chain success.

Every normalized report leaves trajectory safety, human-loop fraction, false-completion rate and resource-normalized utility as `null` when the upstream artifact does not contain those facts.

## Cross-industry coverage

`FEDERATED_BENCHMARK_REGISTRY.json` contains 12 verified project anchors and an explicit coverage row for all 20 industry families already registered by Goal-Driven Core. Coverage has four honest states:

- `EXECUTABLE` — a tested result adapter exists;
- `ANCHORED` — a mature upstream project is identified, but the native schema adapter is not yet implemented;
- `GAP` — no sufficiently mature open anchor has been selected;
- `REQUIRES_PARTNER` — a real task requires regulated data, licensed authority or a physical partner.

This prevents a long catalog of project names from being misrepresented as a completed cross-industry leaderboard.

## Why this is the high-value path

The project already has a full materials vertical and a hidden RealReplayCore. The next scientific question is not whether another bespoke environment can be written. It is whether heterogeneous native evaluators can be federated without erasing their failure modes, safety gaps, human dependence or claim boundaries.

That produces a direct paper-level comparison:

```text
native benchmark success
+ execution coverage
+ infrastructure reliability
+ long-horizon depth
+ explicit missing-evidence vector
+ Goal-Driven intervention/recovery accounting
```

The same agent can then be evaluated across software engineering, desktop work, robotics and materials while each domain retains its own independent verifier.

## Resource policy

Federation validation uses small JSON artifacts and deterministic Python. It must not consume A100 or PC128 scientific capacity. GPUs and 128-core compute remain assigned to original materials calculations and are used by the benchmark only when a separately registered LiveComputeCore task genuinely requires native execution.

## Claim boundary

FederationCore v0.6 proves that three mature benchmark result formats can be normalized without changing their native success definitions, and that all 20 industry families have an explicit executable/anchored/gap/partner status. It does not prove cross-industry agent replacement. That claim requires matched model runs, repeated trials, cost and intervention logging, contamination audits, external expert review, physical/digital-twin safety evidence and hidden tasks.
