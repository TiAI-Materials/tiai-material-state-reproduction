# Alignment with Li Dang's Goal-Driven work-replacement thesis

## Source boundary

This design note distinguishes Li Dang's published claims from TiAI-AgentBench's engineering
interpretation. The primary sources used here are:

- `https://github.com/lidangzzz/goal-driven`;
- the archived X posts in `TiAI-Materials/lidang-transcripts`, especially
  `x/2026-10_软件重写与GoalDriven.md`;
- the September 2026 post arguing that the share of work requiring a persistent human in the
  loop is a central indicator of replaceability, and that locally executable simulation and
  computation are especially exposed to agent replacement.

The benchmark does not treat rhetorical forecasts as established empirical facts. It converts
those forecasts into falsifiable evaluation contracts.

## What the thesis actually implies

The thesis is broader than a materials benchmark and stricter than a task collection.

### 1. Goal and Criteria are the control surface

A long-running worker is not allowed to decide by itself that the job is done. A master or
independent verifier checks explicit success criteria. If criteria remain unmet, the system
continues, restarts, repairs or truthfully exhausts its budget.

Benchmark consequence: every long-horizon task needs an executable `GoalContract`, weighted
criteria, independent verifier identities, heartbeat/restart records and a false-completion
check.

### 2. Human-in-the-loop dependence is the replacement variable

A profession is not replaced merely because an agent can perform one visible subtask. The
benchmark must decompose the job and measure what fraction remains human-led, mixed or fully
agent-executed after verification.

Benchmark consequence: report task, workflow, role, team, organization and industry scope;
report the Human-Loop Fraction (`HLF`) beside Verified Work Replacement (`VWR`).

### 3. Local verifiability predicts the first replacement frontier

Compiler work, formal mathematics and many simulation tasks can be repeatedly executed and
tested in a bounded environment. Physical and social work can also be agent-assisted, but
requires digital twins, instruments, safety systems, approvals or human judgment.

Benchmark consequence: separate five verifiability levels:

- `V0_LOCAL_DETERMINISTIC`;
- `V1_COMPUTE_OR_REPLAY`;
- `V2_DIGITAL_TWIN`;
- `V3_PHYSICAL_INSTRUMENT`;
- `V4_SOCIO_REGULATORY`.

A score from one level cannot be relabeled as another.

### 4. Reconstructing professional tools is a first-class target

The thesis names CAD, EDA, Simulink/LabVIEW-like control systems and Ansys-like simulation
stacks as candidates for specification-driven reconstruction. This differs from benchmarking
an agent that merely operates an existing tool.

Benchmark consequence: maintain two tracks:

1. `TOOL_USE` — configure and operate the admitted software correctly;
2. `TOOL_RECONSTRUCTION` — implement a compatible system from specifications and obtain
   functional signoff by differential, formal or physical tests.

Goal-Driven Core v0.4 adds an executable 1D finite-element reconstruction fixture as the first
small signoff kernel. It is deliberately limited: it validates the reconstruction evaluator,
not a claim that an Ansys-class product has been rebuilt.

### 5. Long duration, recovery and persistence are part of capability

A 100-hour agent process is not equivalent to 100 independent one-shot prompts. Context loss,
idle workers, failed solvers, stale checkpoints and premature completion must be visible.

Benchmark consequence: report Criteria Closure Rate (`CCR`), Persistence Integrity (`PI`),
Continuity Recovery Rate (`CRR`), Fault Recovery Rate (`FRR`) and False Completion Rate
(`FCR`) in addition to final success.

### 6. Inputs and outputs should be machine-auditable

The archived practical recipe places documents, tables, databases, code, prompts and configs
inside a bounded working directory, invokes a headless agent and writes success and failure to
structured JSON.

Benchmark consequence: use strict JSON/JSONL, frozen artifact identities, run manifests,
checkpoint lineage and deterministic command-line validation.

## Correct TiAI-AgentBench architecture

```text
Universal Goal-Driven Core
  GoalContract + Criteria + WorkGraph + AgentEpisodes + Verifiers
  + Artifacts + InterventionLedger + Faults + Budgets + Safety

        ↓ loaded by

Industry / Profession Registry
  materials, chemistry, biology, software, EDA, CAD/construction,
  CAE, controls/electrical, robotics, manufacturing, healthcare,
  finance, legal, logistics, energy, education, enterprise operations,
  mathematics/TCS, media/design and public administration

        ↓ instantiated as

Domain Task Packs
  public development, hidden replay, live compute, digital twin,
  physical instrument and socio-regulatory evaluation

        ↓ aggregated by

Replacement Scope
  TASK → WORKFLOW → ROLE → TEAM → ORGANIZATION → INDUSTRY
```

Materials science remains the first active vertical because it already contains verifiable
work across all major layers: literature, data, thermodynamics, DFT, learned potentials, MD,
mesoscale evolution, continuum mechanics, experiments and laboratory automation.

## Full materials multiscale chain

The material vertical is not restricted to evidence reliability. The v0.4 Goal-Driven fixture
requires the complete chain:

```text
mission and material identity
→ source-resolved evidence
→ CALPHAD / Scheil / kinetics
→ DFT and atomistic defects
→ MLIP admission
→ finite-temperature MD
→ phase-field / cellular automata
→ CPFEM / RVE / FEM
→ independent DIC / EBSD / microscopy bridge
→ contradiction ledger
→ bounded decision and next action
```

Each handoff must preserve quantity meaning, units, composition, temperature, phase, structure,
specimen, model lineage, applicability domain and uncertainty. Two individually converged
models do not pass if their handoff is invalid.

## Metrics added in v0.4

- `GDS` — Goal-Driven Success after criteria, persistence, faults and budget checks;
- `GA` — Goal Attainment;
- `CCR` — weighted Criteria Closure Rate;
- `VWR` — Verified Work Replacement;
- `HLF` — Human-Loop Fraction, lower is more autonomous;
- `ARP` — Autonomous Replacement Potential observed in the run;
- `PI` — Persistence Integrity;
- `CRR` — Continuity Recovery Rate after failed or idle episodes;
- `FRR` — required Fault Recovery Rate;
- `FCR` — False Completion Rate;
- `FSR` — Functional Signoff Rate for reconstruction tasks;
- `HOURS_REPLACED` — verified human-baseline hours replaced;
- `RNU` — resource-normalized utility.

These are reported as a vector. A high partial work score cannot cancel false completion,
non-independent verification, failed signoff or an unsafe physical trajectory.

## Claim boundary

Goal-Driven Core v0.4 makes the Goal-Driven evaluator, 20-family industry registry, four synthetic
Goal-Driven protocol regressions and one executable solver-reconstruction fixture runnable.
The fourth fixture is a mandatory-human-authority healthcare workflow, demonstrating that verified success can retain human authority and report `VWR<1`. It does not establish that all professions, CAD/EDA products, materials simulations or robots
have already been replaced. That claim requires hidden expert task packs, real agent baselines,
authorized software and compute, certified digital twins, supervised physical execution and
repeated trials.
