# TiAI-AgentBench

**A cross-industry work-replacement benchmark with materials science as the first full vertical.**

`TiAI-AgentBench` measures how much of real professional work an agent actually replaces,
using executed artifacts, independent verifier gates, human-intervention records, fault
recovery, resources and trajectory safety. Materials science is the first full vertical and
includes evidence, research software, thermodynamics, DFT, ML potentials, MD, phase-field,
CPFEM/RVE/FEM, multiscale integration, experiments, laboratory robotics, campaigns and
scientific communication. The same core protocol is designed for other industries through
domain adapters.

The package name and CLI remain `tiai-matbench` for backward compatibility. The earlier
**TiAI-MatBench v0.1** source-aware benchmark is retained as the first executable suite,
`EvidenceCore`; it is no longer presented as the complete benchmark.

## Current status

Three layers are committed:

1. **Executable EvidenceCore public development pack** — seven real released TiAI tasks plus
   one isolated scorer self-test. It has deterministic grading, critical scientific gates,
   frozen Git-blob evidence and CI regression tests.
2. **Full-stack materials v0.2 architecture** — twelve suites and 39 concrete staged task
   specifications spanning digital analysis, live computation, multiscale simulation,
   experiments, robotics and end-to-end research campaigns.
3. **Cross-industry ProtocolCore v0.3** — a deterministic work-replacement schema and scorer,
   eight staged domain adapters, and synthetic regression fixtures for a materials multiscale
   chain, a scientific-robot digital twin and software deployment/recovery.

Only layer 1 is currently a runnable real scientific task pack. Layer 3 is executable as a
protocol/scorer harness, but its included runs are synthetic regression fixtures rather than
claims of real multiscale, robot or cross-industry capability. The remaining suite entries carry
explicit readiness states such as `DESIGN_READY`, `REQUIRES_SANITIZED_ASSETS`,
`REQUIRES_LIVE_HPC`, `REQUIRES_DIGITAL_TWIN` and `REQUIRES_PHYSICAL_LAB`. A roadmap entry is
not mislabeled as a completed benchmark.

Read [FULL_STACK_SPEC.md](FULL_STACK_SPEC.md) for the materials benchmark model,
[CROSS_INDUSTRY_CORE.md](CROSS_INDUSTRY_CORE.md) for the universal work protocol,
[SUITE_REGISTRY.json](SUITE_REGISTRY.json) for the materials suite authority and
[DOMAIN_ADAPTER_REGISTRY.json](DOMAIN_ADAPTER_REGISTRY.json) for staged industry adapters.

## Full-stack suites

| Suite | Scope | Current readiness |
| --- | --- | --- |
| `S00_EVIDENCE` | literature, evidence, material states, source-aware analysis | executable public dev |
| `S01_RESEARCH_OPS` | environments, research artifacts, HPC, checkpoint and recovery | design ready |
| `S02_THERMO_KINETICS` | CALPHAD, Scheil, phase stability and kinetics | sanitized assets needed |
| `S03_DFT_ATOMISTIC` | structures, DFT, defects, interfaces and energy paths | live HPC needed |
| `S04_MLIP_MD` | datasets, potential training/admission and MD | live HPC needed |
| `S05_MESO` | phase-field, CA and mesoscale microstructure | sanitized assets needed |
| `S06_CONTINUUM` | CPFEM, RVE, FEM and local-field validation | sanitized assets needed |
| `S07_MULTISCALE` | cross-scale handoffs, UQ and contradiction resolution | design ready |
| `S08_EXPERIMENT` | experiment planning, DIC, EBSD and characterization | sanitized assets needed |
| `S09_ROBOT_LAB` | protocol compilation, digital twins and physical robots | digital twin needed |
| `S10_CAMPAIGN` | end-to-end autonomous research campaigns | design ready |
| `S11_COMMUNICATION` | figures, source data, manuscripts and review | design ready |

The roadmap includes real TiAI flagship missions: Ti65 temperature-dependent ductility
reversal, TC4 high-index twinning, Ti–B–W potential admission, TC4 fixed-phase dynamic
recrystallization and a design-build-test-learn campaign.

## Benchmark axes

Scores are reported by:

- suite;
- work horizon: `UNIT`, `WORKFLOW`, `CAMPAIGN`, `CLOSED_LOOP`;
- autonomy: `A0` advisory through `A5` embodied closed loop;
- execution mode: evidence, sandbox code, precomputed replay, live HPC, digital twin,
  physical lab or expert review;
- readiness and contamination boundary.

The main full-stack metrics are Verified Scientific Success, Work Replacement Coverage,
End-to-End Autonomous Success Rate, Human Intervention Rate, Recovery and Resume Reliability,
Resource-Normalized Utility and Scientific Safety Rate.

## Validate the full-stack registry

The package has no runtime dependency outside Python 3.11+.

```bash
python -m pip install -e ./matbench

tiai-matbench validate-registry \
  --registry matbench/SUITE_REGISTRY.json \
  --roadmap matbench/suites/roadmap_v0.2.jsonl

tiai-matbench list-suites \
  --registry matbench/SUITE_REGISTRY.json
```

The validator checks the suite vocabulary, autonomy levels, horizons, execution modes,
readiness states, metric registry, task-to-suite compatibility, resource-mode consistency
and the requirement that every suite has at least one concrete task specification.

## Validate the cross-industry ProtocolCore

```bash
tiai-matbench validate-adapters \
  --adapters matbench/DOMAIN_ADAPTER_REGISTRY.json

tiai-matbench validate-protocols \
  --protocols matbench/protocols/protocols_v0.3.jsonl \
  --adapters matbench/DOMAIN_ADAPTER_REGISTRY.json \
  --suites matbench/SUITE_REGISTRY.json

tiai-matbench score-work-runs \
  --protocols matbench/protocols/protocols_v0.3.jsonl \
  --runs matbench/examples/protocol_oracle_runs.jsonl \
  --output protocol_oracle_report.json \
  --require-vss 1.0 \
  --require-wrc 1.0
```

The protocol scorer emits `VSS`, `WRC`, `E2E_ASR`, `HIR`, `RRR`, `RNU` and `SSR`, plus
work-unit credit, failed gates, interventions, resource accounting, fault recovery, safety
steps and a violation ledger. The current protocol fixtures are marked
`SYNTHETIC_PROTOCOL_TEST`; they validate the evaluator and cannot be reported as domain
capability results.

## Run the executable EvidenceCore pack

```bash
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

EvidenceCore uses strict JSONL and rejects duplicate keys, non-finite numbers, unknown task
IDs, unregistered evidence, mismatched Git blobs and locators outside a task's evidence scope.

## EvidenceCore scoring

The current executable pack retains its six deterministic dimensions:

| Dimension | Weight |
| --- | ---: |
| outcome correctness | 0.30 |
| evidence fidelity | 0.25 |
| state/condition fidelity | 0.15 |
| split integrity | 0.10 |
| claim calibration | 0.15 |
| execution integrity | 0.05 |

Fatal errors such as source leakage, state mixing, fabricated evidence, unsupported causality
or false tool success can zero a task. The primary EvidenceCore score includes only the seven
real released tasks; the synthetic scorer fixture is reported separately.

## Repository map

- `CROSS_INDUSTRY_CORE.md`: domain-independent work-replacement, multiscale and robotics protocol;
- `FULL_STACK_SPEC.md`: materials benchmark vision, axes, suites and flagship campaigns;
- `DOMAIN_ADAPTER_REGISTRY.json`: staged cross-industry domain objects, tools and fatal gates;
- `SUITE_REGISTRY.json`: authoritative materials suite, metric, autonomy and readiness registry;
- `suites/roadmap_v0.2.jsonl`: 39 materials task specifications and implementation states;
- `protocols/protocols_v0.3.jsonl`: domain-independent executable protocol fixtures;
- `examples/protocol_*_runs.jsonl`: oracle and adversarial protocol regression runs;
- `tasks/dev.jsonl`, `references/dev.jsonl`: executable EvidenceCore public development pack;
- `MANIFEST.json`: EvidenceCore scoring and frozen asset registry plus umbrella metadata;
- `src/tiai_matbench/`: strict parser, EvidenceCore grader, suite/adapter validators, work-replacement scorer and CLI;
- `tests/`: EvidenceCore, suite, adapter and work-replacement regression tests;
- `BENCHMARK_CARD.md`: governance, claims and evaluation protocol;
- `RELATED_WORK.md`: benchmark landscape and positioning.

## Interpretation boundary

The public EvidenceCore references are visible and cannot support a headline blind
leaderboard. The v0.2 full-stack registry is an executable architecture and task roadmap, and ProtocolCore
v0.3 is an executable generalized scorer. Neither is a claim that all simulation, robotics,
industry adapters or physical-lab environments have already been built. A
publication-grade comparison requires externally adjudicated hidden tasks, frozen hardware and
software contracts where relevant, strong agent baselines, repeated trials, cost and
intervention accounting, contamination auditing and expert review.
