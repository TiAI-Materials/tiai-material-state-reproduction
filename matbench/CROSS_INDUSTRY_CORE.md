# Cross-industry Agent Work Replacement Protocol

## Scope

TiAI-AgentBench is not defined as a materials question-answering benchmark. Its reusable core
asks a broader operational question:

> What verified fraction of a professional workflow did the agent actually execute, and what
> scientific, operational, safety, resource or human-intervention conditions were required?

Materials science is the first full domain adapter. Chemistry, biology, manufacturing,
software engineering, healthcare, energy and scientific robotics are represented as staged
adapter contracts, not as completed public task packs.

## Common work classes

Every domain maps its work to a shared vocabulary:

1. `GOAL_DEFINITION` — convert an objective into terminal states and constraints;
2. `EVIDENCE` — acquire and bind sources, observations and prior results;
3. `DATA` — curate, transform, validate and version data;
4. `PLANNING` — select methods, tools, sequence and budgets;
5. `SOFTWARE_EXECUTION` — deploy code, environments and services;
6. `MODELING_SIMULATION` — execute mathematical, statistical or physical models;
7. `EXPERIMENT_INSTRUMENT` — configure instruments and acquire measurements;
8. `ROBOTIC_ACTION` — perform embodied manipulation or machine actions;
9. `VERIFICATION_RECOVERY` — check outputs, diagnose faults, checkpoint and resume;
10. `DECISION_OPTIMIZATION` — choose candidates, actions or operating points;
11. `KNOWLEDGE_UPDATE` — revise models, memory and future decisions;
12. `COMMUNICATION_GOVERNANCE` — produce auditable artifacts and respect approvals.

A domain adapter supplies domain objects, tool families and fatal gates. For example,
materials science adds material state, phase, structure, specimen, potential identity,
solver convergence and cross-scale compatibility. Healthcare adds patient identity, consent,
clinical scope and mandatory human approval. Manufacturing adds part revision, tolerance,
machine capability and quality acceptance.

## Work protocol

A protocol declares:

- domain adapter, suite, work horizon and autonomy target;
- execution mode: evidence, sandbox code, replay, live compute, digital twin, physical lab or
  expert review;
- criticality-weighted work units and the corresponding human baseline time;
- required artifacts and independent verifier gates for each work unit;
- fatal, major and minor gate definitions;
- time, compute, monetary, experimental and robot budgets;
- required fault injections;
- whether trajectory-level safety applies;
- whether the task is real released, synthetic protocol testing or private hidden evaluation.

The run record reports the actual performer (`AGENT`, `MIXED`, `HUMAN`), completion state,
artifact SHA-256 identities, gate outcomes, interventions, faults, resources and safety steps.
A missing work unit, artifact, gate, fault recovery or safety trace remains visible.

## Implemented deterministic metrics

The v0.3 protocol scorer computes a vector rather than hiding failure in one average:

- `VSS` — verified scientific success after required work, fatal gates, budgets and safety;
- `WRC` — criticality-weighted autonomous work replacement, reduced by mixed/human execution
  and intervention severity;
- `E2E_ASR` — run-level and aggregate end-to-end success rate;
- `HIR` — normalized human-intervention severity;
- `RRR` — recovery rate over required injected faults;
- `RNU` — verified autonomous work multiplied by resource efficiency;
- `SSR` — safe fraction of the recorded digital or physical trajectory.

A run that claims success after a fatal scientific gate, unsafe trajectory or resource-budget
violation receives `VSS = 0`. It can still expose partial work and failure details; negative
results are not discarded.

## Multiscale materials protocol

The public protocol regression fixture represents the following chain:

```text
mission and material state
→ source-bound evidence
→ thermodynamic phase/quantity handoff
→ converged DFT quantities and lineage
→ MLIP admission
→ finite-temperature MD
→ continuum/experiment bridge
→ bounded decision and next action
```

The scorer checks each handoff independently. A thermodynamic result cannot be passed to a
mesoscale or mechanical model without quantity semantics, normalization, compatible state and
uncertainty. DFT cannot justify MD without potential identity, training/test isolation,
applicability-domain admission and trajectory stability. Individually valid calculations can
still fail the cross-scale protocol.

## Robotics protocol

Scientific robotics is a horizontal adapter because chemistry, biology, materials and
manufacturing can all use embodied agents. The staged path is:

```text
natural-language protocol
→ typed action representation
→ digital-twin execution
→ supervised physical replay
→ adaptive physical closed loop
```

The protocol separates final-state success from trajectory safety. Sample identity,
collision/clearance, force/torque, tilt/spill, contamination, instrument state, sensor receipts,
safe abort and fault recovery are explicit gates. A robot that reaches the target after an
unsafe step does not pass.

## Current executable fixtures

`protocols/protocols_v0.3.jsonl` contains three **synthetic protocol tests**:

- materials multiscale evidence-to-decision replay;
- scientific-robot digital-twin protocol execution;
- software artifact deployment and recovery.

The oracle and negative runs validate the generalized scorer. They do not constitute real
multiscale, robot or software capability results. Real task packs must replace synthetic
artifacts with frozen replay assets, authorized live execution or certified physical hardware.

## Domain adapter registry

`DOMAIN_ADAPTER_REGISTRY.json` currently registers eight adapters:

- materials science;
- chemistry;
- biology and biotechnology;
- manufacturing;
- software engineering;
- healthcare;
- energy and climate technology;
- scientific robotics.

The registry is intentionally extensible. Adding an industry means mapping its objects, tools,
work classes, approvals and fatal gates to the same work protocol; it does not mean forcing
all fields or safety rules to be identical across industries.

## Claim boundary

The executable cross-industry protocol and scorer demonstrate that multiscale simulation,
robotics and other professional work can be evaluated by one common contract. They do not
show that every industry adapter already has expert-adjudicated tasks or physical environments.
Each adapter retains a readiness state, and leaderboard claims must report the exact domain,
execution mode, horizon, autonomy level and hardware/software contract.
