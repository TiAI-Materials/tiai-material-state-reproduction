# TiAI-AgentBench

**A Goal-Driven benchmark federation for verified replacement of professional work, with
materials science as the first active full vertical.**

TiAI-AgentBench does not ask only whether a model can answer a question. It asks whether an
agent can accept a goal, execute the work that a professional would normally perform, produce
auditable artifacts, survive failures, satisfy independent criteria and truthfully stop only
when the goal is closed or the budget is exhausted.

The package name and CLI remain `tiai-matbench` for compatibility with the original public
materials development set.

## Correct scope

The benchmark has four linked layers:

1. **EvidenceCore v0.1** — seven real released source/state/statistics tasks plus one isolated
   scorer self-test.
2. **Materials Full-Stack v0.2** — twelve suites and 39 staged tasks spanning evidence,
   research operations, CALPHAD, DFT, MLIP/MD, mesoscale, CPFEM/RVE/FEM, multiscale,
   experiments, robotics, campaigns and communication.
3. **Work-Replacement ProtocolCore v0.3** — criticality-weighted work units, independent
   gates, artifacts, interventions, fault recovery, resources and trajectory safety.
4. **Goal-Driven Core v0.4** — explicit Goal/Criteria contracts, persistent agent episodes,
   heartbeat/restart accounting, false-completion detection, human-loop measurement,
   role-to-industry scope and specification-driven tool reconstruction.

The architecture is cross-industry. Materials science is the first active domain adapter, not
the final boundary. The v0.4 registry stages 20 industry families, including chemistry,
biotechnology, software, EDA, CAD/construction, CAE, controls/electrical, robotics,
manufacturing, healthcare, finance, legal, logistics, energy, education, enterprise operations,
mathematics/TCS, media/design and public administration.

Read:

- [LIDANG_GOAL_DRIVEN_ALIGNMENT.md](LIDANG_GOAL_DRIVEN_ALIGNMENT.md) for the source-derived
  Goal-Driven interpretation;
- [CROSS_INDUSTRY_CORE.md](CROSS_INDUSTRY_CORE.md) for the universal work protocol;
- [FULL_STACK_SPEC.md](FULL_STACK_SPEC.md) for the materials vertical;
- [GOAL_DRIVEN_REGISTRY.json](GOAL_DRIVEN_REGISTRY.json) for industry families,
  verifiability levels and replacement scopes;
- [DOMAIN_ADAPTER_REGISTRY.json](DOMAIN_ADAPTER_REGISTRY.json) for domain objects, tools and
  fatal gates.

## Goal-Driven model

```text
Goal Contract
→ professional Work Graph
→ worker/subagent episodes
→ tool execution and artifacts
→ independent Criteria evaluation
→ restart / repair / replan when criteria are unmet
→ truthful success, abstention or budget exhaustion
```

The worker may claim completion, but only the criteria verifier may close the goal. A run that
stops early, self-verifies a required criterion or reports success after failed signoff receives
a false-completion violation.

## Replacement and verifiability axes

Results are reported by replacement scope:

```text
TASK → WORKFLOW → ROLE → TEAM → ORGANIZATION → INDUSTRY
```

They are also separated by verifiability level:

| Level | Meaning |
| --- | --- |
| `V0_LOCAL_DETERMINISTIC` | locally executable and deterministically/differentially testable |
| `V1_COMPUTE_OR_REPLAY` | scientific compute, solver or frozen replay |
| `V2_DIGITAL_TWIN` | stateful simulator with trajectory and fault checks |
| `V3_PHYSICAL_INSTRUMENT` | instrument, specimen or robot execution with safety receipts |
| `V4_SOCIO_REGULATORY` | material human judgment, consent, negotiation or regulatory authority |

A result obtained in replay cannot be relabeled as live compute, and a digital-twin result
cannot be relabeled as physical-laboratory performance.

## Materials multiscale vertical

The v0.4 Goal-Driven materials fixture treats the full chain as one role-level campaign:

```text
mission/material state
→ source-resolved evidence
→ CALPHAD/Scheil/kinetics
→ DFT and atomistic defects
→ MLIP admission
→ finite-temperature MD
→ phase-field / cellular automata
→ CPFEM / RVE / FEM
→ DIC / EBSD / microscopy bridge
→ contradiction ledger
→ bounded decision and next action
```

Each handoff checks quantity semantics, units, composition, temperature, phase, structure,
specimen and model lineage, applicability domain, uncertainty and independent validation. Two
individually converged models fail if their cross-scale handoff is invalid.

## Tool use versus tool reconstruction

TiAI-AgentBench distinguishes:

- **tool use** — correctly configure and operate an admitted professional tool;
- **tool reconstruction** — implement a compatible tool from a frozen specification and obtain
  functional signoff through differential, formal, simulation or physical tests.

The first executable reconstruction fixture is a specification-compatible 1D axial-bar finite
-element kernel. It contains 12 frozen cases, including differential numerical cases, global
equilibrium, fixed-boundary invariants and invalid-input behavior. It validates the evaluator;
it is not a claim that an Ansys-class product has been rebuilt.

## v0.4 metrics

The Goal-Driven scorer reports a vector:

- `GDS` — Goal-Driven Success;
- `GA` — Goal Attainment;
- `CCR` — weighted Criteria Closure Rate;
- `VWR` — Verified Work Replacement;
- `HLF` — Human-Loop Fraction;
- `ARP` — observed Autonomous Replacement Potential;
- `PI` — Persistence Integrity;
- `CRR` — Continuity Recovery Rate;
- `FRR` — required Fault Recovery Rate;
- `FCR` — False Completion Rate;
- `FSR` — Functional Signoff Rate for reconstruction tasks;
- `HOURS_REPLACED` — verified human-baseline hours replaced;
- `RNU` — Resource-Normalized Utility.

These extend, rather than replace, ProtocolCore v0.3 metrics (`VSS`, `WRC`, `E2E_ASR`, `HIR`,
`RRR`, `RNU`, `SSR`) and EvidenceCore's six scientific dimensions.

## Validate Goal-Driven Core v0.4

The package has no runtime dependency outside Python 3.11+.

```bash
python -m pip install -e ./matbench

tiai-matbench validate-goal-registry \
  --registry matbench/GOAL_DRIVEN_REGISTRY.json

tiai-matbench list-industries \
  --registry matbench/GOAL_DRIVEN_REGISTRY.json

tiai-matbench validate-goal-protocols \
  --protocols matbench/goal_driven/protocols_v0.4.jsonl \
  --registry matbench/GOAL_DRIVEN_REGISTRY.json \
  --adapters matbench/DOMAIN_ADAPTER_REGISTRY.json

tiai-matbench score-goal-runs \
  --protocols matbench/goal_driven/protocols_v0.4.jsonl \
  --runs matbench/examples/goal_oracle_runs.jsonl \
  --require-gds 1.0 \
  --require-vwr 1.0 \
  --max-fcr 0.0

tiai-matbench score-goal-runs \
  --protocols matbench/goal_driven/protocols_v0.4.jsonl \
  --runs matbench/examples/goal_human_loop_runs.jsonl \
  --require-gds 1.0 \
  --max-fcr 0.0

tiai-matbench verify-reconstruction \
  --task-dir matbench/reconstruction/fea1d \
  --submission matbench/reconstruction/fea1d/oracle_solver.py \
  --require-signoff \
  --min-pass-rate 1.0
```

The bundled Goal-Driven runs are `SYNTHETIC_PROTOCOL_TEST` fixtures. They validate the
universal evaluator and cannot be reported as evidence that a real agent has replaced a
materials scientist, CAE engineer, laboratory automation engineer or clinical professional.

## Validate ProtocolCore v0.3

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
  --require-vss 1.0 \
  --require-wrc 1.0
```

## Run EvidenceCore v0.1

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
  --submission matbench/examples/oracle_submission.jsonl
```

EvidenceCore retains strict JSON/JSONL parsing, frozen Git-blob identities, evidence locators,
source holdout, material-state boundaries, claim calibration and critical scientific gates.

## Repository map

- `LIDANG_GOAL_DRIVEN_ALIGNMENT.md`: source-derived design interpretation;
- `GOAL_DRIVEN_REGISTRY.json`: 20 industry families, five verifiability levels and six
  replacement scopes;
- `goal_driven/protocols_v0.4.jsonl`: materials role, CAE reconstruction, robot digital-twin
  and bounded-human-authority healthcare Goal/Criteria protocols;
- `examples/goal_*_runs.jsonl`: autonomous oracle, bounded human-loop and adversarial regression runs;
- `reconstruction/fea1d/`: executable specification-driven solver reconstruction fixture;
- `src/tiai_matbench/goal_driven.py`: persistent Goal/Criteria validator and scorer;
- `src/tiai_matbench/reconstruction.py`: differential and physics signoff harness;
- `CROSS_INDUSTRY_CORE.md`: v0.3 work-replacement protocol;
- `DOMAIN_ADAPTER_REGISTRY.json`: eight detailed domain adapters;
- `SUITE_REGISTRY.json`, `suites/roadmap_v0.2.jsonl`: 12 materials suites and 39 staged tasks;
- `tasks/dev.jsonl`, `references/dev.jsonl`: executable EvidenceCore public development pack;
- `BENCHMARK_CARD.md`: governance, claims and release protocol;
- `RELATED_WORK.md`: benchmark landscape and positioning.

## Current claim boundary

The repository now contains a runnable Goal-Driven evaluator, 20-family industry registry,
four synthetic long-horizon protocol regressions and one real executable reconstruction
verifier. EvidenceCore remains the only released **real materials task pack**. Publication-grade
claims about role, organization or industry replacement still require hidden expert-adjudicated
tasks, real agent baselines, repeated runs, sanitized solver replays, authorized live compute,
certified digital twins, supervised physical execution, contamination audits and human-work
baselines.
