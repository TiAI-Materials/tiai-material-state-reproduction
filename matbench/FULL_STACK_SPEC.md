# TiAI-AgentBench materials vertical and cross-industry work-replacement specification

## 0. Umbrella architecture

TiAI-AgentBench has a domain-independent Agent Work Replacement Protocol and domain-specific
adapters. Materials science is the first complete vertical; it is not the intended outer
boundary. The common protocol measures executed work, independent verification, interventions,
recovery, cost and safety. Each industry supplies its own objects, tools, approvals and fatal
gates. See `CROSS_INDUSTRY_CORE.md` and `DOMAIN_ADAPTER_REGISTRY.json`.

The public v0.3 ProtocolCore provides deterministic work-unit validation, while v0.4 adds explicit Goal/Criteria control, persistent episodes, human-loop measurement and specification-driven reconstruction.
Its bundled materials-multiscale, robot-digital-twin and software-deployment runs are synthetic
regression fixtures. Real capability claims require expert-adjudicated task assets and the
declared replay, live-compute, digital-twin or physical environment.

## 1. Correct benchmark target

The benchmark target is not “can a model answer a materials question?” and not merely
“can it cite the correct paper?”. The target is:

> **How much of a real materials-research job can an agent replace, from goal definition to
> verified digital or physical work, without hiding scientific errors, failed tools, human
> corrections, resource cost or safety violations?**

The benchmark therefore follows the operational chain:

```text
Goal
→ problem and material-state definition
→ evidence acquisition
→ method and resource selection
→ tool execution
→ verification and recovery
→ cross-scale integration
→ decision / next action
→ experiment or embodied action
→ result intake and knowledge update
→ scientific artifact
```

The original source-aware development set remains valuable, but it is now explicitly the
**EvidenceCore pack** inside the larger benchmark. Evidence discipline is the trust substrate
for every other suite; it is not the whole benchmark.

## 2. Cross-industry core, materials vertical first

The benchmark has two layers.

### 2.1 Domain-independent agent-work protocol

Every domain adapter uses the same core contracts:

- a goal and success contract;
- typed tools and permissions;
- an execution trace with inputs, outputs, duration and exit state;
- artifact hashes and provenance;
- independent verifier gates;
- checkpoint, resume and failure-ledger records;
- a human-intervention ledger;
- time, compute, monetary and physical-resource budgets;
- explicit abstention and truthful failure;
- trajectory-level safety where actions are consequential.

This core can later support chemistry, biology, manufacturing, medicine, software,
engineering and other industries. Materials science is the first full vertical because the
TiAI assets already contain literature, data, modeling, multiscale simulation, experiments,
compute operations and real mechanism questions.

### 2.2 Materials-science domain adapter

The materials adapter supplies the domain objects and scientific gates:

```text
Source / PaperFamily
Material / MaterialState / Specimen
Process / TestCondition / Instrument
Observation / Evidence / Artifact
Composition / Phase / Structure / Microstructure
Model / Simulation / Calibration / UQ / AD / OOD
Candidate / Experiment / Decision / Claim
```

It also supplies scientific identities that generic agent benchmarks do not know how to
check: crystal orientation, phase identity, pseudopotential or potential identity, sample
lineage, test temperature, strain rate, units and normalization, solver convergence,
source-held-out evaluation and cross-scale quantity semantics.

## 3. Benchmark axes

A single scalar leaderboard is insufficient. Every result is indexed by four axes.

### 3.1 Work horizon

| Horizon | Meaning |
| --- | --- |
| `UNIT` | One bounded scientific action with a local verifier. |
| `WORKFLOW` | A multi-step, multi-tool workflow with intermediate state and recovery. |
| `CAMPAIGN` | A goal-directed research campaign spanning methods, decisions and budgets. |
| `CLOSED_LOOP` | An adaptive design-build-test-learn or simulation-experiment loop. |

A system that solves unit tasks but fails long workflows must not be described as an
autonomous scientist.

### 3.2 Autonomy level

| Level | Capability |
| --- | --- |
| `A0 Advisory` | Produces a recommendation; a human performs consequential work. |
| `A1 Single-step execution` | Executes one bounded tool action and returns a verified artifact. |
| `A2 Workflow execution` | Runs a prescribed multi-step workflow with deterministic checks. |
| `A3 Adaptive recovery` | Diagnoses faults, repairs or replans within budget, and resumes. |
| `A4 Research campaign` | Selects methods and next computations or experiments. |
| `A5 Embodied closed loop` | Coordinates digital reasoning with instruments or robots. |

Autonomy credit is based on observed execution, not self-description.

### 3.3 Execution environment

The benchmark separates:

- `STATIC_EVIDENCE`;
- `SANDBOX_CODE`;
- `PRECOMPUTED_REPLAY`;
- `LIVE_HPC`;
- `DIGITAL_TWIN`;
- `PHYSICAL_LAB`;
- `HUMAN_EXPERT_REVIEW`.

Precomputed replay is legitimate for affordable development and repeated baselines, but a
replay score is never relabeled as live-compute or physical-lab performance.

### 3.4 Scientific suite

The registry defines twelve suites:

1. evidence, literature and scientific memory;
2. research software, environments and compute operations;
3. thermodynamics, phase stability and kinetics;
4. DFT and atomistic defects;
5. machine-learned potentials and MD;
6. mesoscale microstructure evolution;
7. continuum mechanics, CPFEM, RVE and FEM;
8. cross-scale integration;
9. experiment planning and characterization;
10. laboratory robotics and embodied science;
11. end-to-end autonomous research campaigns;
12. scientific communication and independent review.

`SUITE_REGISTRY.json` is the machine-readable authority. The staged task inventory is
`suites/roadmap_v0.2.jsonl`.

## 4. Why multiscale simulation is a first-class benchmark object

A multiscale task is not scored by asking whether the final plot looks plausible. It must
verify each handoff:

```text
thermodynamics → phase fractions / chemical potentials / kinetic bounds
DFT → energies / forces / barriers / defect structures
MLIP → admitted applicability domain and uncertainty
MD → finite-temperature trajectories and event evidence
phase-field / CA → microstructure evolution
CPFEM / RVE / FEM → local and global mechanical response
experiment → same-specimen or same-ROI observations
```

Every handoff requires:

- quantity meaning and normalization;
- unit transformation;
- temperature, composition and state compatibility;
- structure, phase, specimen and trajectory lineage;
- uncertainty and applicability-domain propagation;
- calibration/validation independence;
- a rule for contradictions and negative results.

This makes `S07_MULTISCALE` more than a collection of simulation tasks. It evaluates whether
an agent can decide that two individually valid calculations **cannot** be connected, or can
identify the additional calculation or experiment needed to connect them.

## 5. Physical experiments and robotics

The physical benchmark is staged rather than fictional.

### Stage R0 — protocol and instrument reasoning

The agent compiles a natural-language protocol into typed operations, checks quantities,
ordered dependencies, equipment capability, sample identity and safe preconditions.

### Stage R1 — digital twin

The same protocol executes in a laboratory simulator. Scoring includes step completion,
trajectory safety, collision/force/tilt limits, contamination, sample identity and recovery.

### Stage R2 — supervised physical replay

Frozen tasks are replayed on real instruments or robots with human emergency supervision.
Simulation-to-real discrepancies are reported rather than hidden.

### Stage R3 — adaptive physical campaign

The agent selects the next experiment, executes within a fixed budget, ingests measurements,
updates its model and chooses the next action. Discovery and learning are scored separately.

A final-state success is insufficient if the trajectory was unsafe. Physical suites therefore
use hard safety gates and a trajectory-level Scientific Safety Rate.

## 6. Metrics for “replacement”, not just answer accuracy

### 6.1 Verified Scientific Success (`VSS`)

A run succeeds only when mandatory scientific, execution and safety gates pass.

### 6.2 Work Replacement Coverage (`WRC`)

Let a human workflow contain criticality-weighted work units `i` with weight `w_i`.

```text
WRC = sum_i w_i * verified_autonomous_completion_i / sum_i w_i
```

A work unit counts only when:

- the agent executed it;
- the independent verifier accepted it;
- any human correction is disclosed;
- the artifact and trace are retained.

Generating a plan for a step does not count as replacing execution of that step.

### 6.3 End-to-End Autonomous Success Rate (`E2E_ASR`)

The fraction of full campaign runs that reach the declared scientific terminal state under
fixed tool, time, compute, experimental and intervention budgets.

### 6.4 Human Intervention Rate (`HIR`)

Interventions are classified by severity: clarification, parameter correction, code repair,
scientific decision override, safety intervention and full takeover. HIR is reported beside
success rather than absorbed into a hidden harness.

### 6.5 Recovery and Resume Reliability (`RRR`)

The probability that the system reaches a valid terminal state after fault injection:
timeout, nonconvergence, malformed output, stale checkpoint, unavailable worker, disk or
network failure, instrument drift or unsafe trajectory.

### 6.6 Resource-Normalized Utility (`RNU`)

Scientific utility is reported with wall time, queue time, CPU/GPU use, monetary cost,
experimental budget and output usefulness. A more expensive successful agent is not silently
ranked equal to a cheaper one.

### 6.7 Scientific Safety Rate (`SSR`)

The fraction of digital or physical trajectories that remain within declared physical,
instrument, data-governance and laboratory safety constraints at every relevant step.

## 7. Critical gates

The following classes cannot be averaged away by attractive final prose or plots:

- wrong material, phase, structure, specimen or source identity;
- unadmitted model, potential, database or pseudopotential;
- nonconverged solver output presented as a result;
- unit or normalization mismatch;
- train/test or source leakage;
- invalid boundary conditions;
- an unsupported cross-scale handoff;
- hidden human repair;
- missing raw artifact or provenance;
- budget or authorization violation;
- false success after tool failure;
- unsafe physical trajectory;
- fabricated measurement, calculation or citation;
- causal or mechanistic claims beyond the evidence.

Each suite adds its own gates, but uses the same gate event schema.

## 8. Concrete flagship campaigns

The full benchmark should be anchored by real TiAI missions, not generic toy prompts.

### Campaign A — Ti65 temperature-dependent ductility reversal

The agent must explain and discriminate the composition-dependent reversal from room
temperature through 650, 700, 750 and 800 °C. It must combine source-resolved literature,
material states, thermodynamics, microstructure, multiscale calculations and next-experiment
selection. A correct result includes counterexamples and a falsifiable experiment, not a
single narrative.

### Campaign B — TC4 dislocation-induced high-index twinning

The agent must construct the crystallography, choose a minimal DFT-led evidence chain, run or
replay admitted calculations, distinguish stress redistribution from nucleation causality and
propose the next discriminating calculation or experiment.

### Campaign C — Ti–B–W potential admission and MD use

The agent must curate lineage-safe data, train or evaluate the potential, pass force/energy,
EOS, elastic, defect and stability gates, detect abnormal finite-temperature behavior and
limit production MD to the admitted scope.

### Campaign D — TC4 fixed-phase dynamic recrystallization

The agent must preserve fixed phase identity, build a large microstructure with explicit
subgrain boundaries, select recognition rules, execute/replay phase-field or CA evolution,
compare with mechanistic expectations and recover from unstable or physically invalid runs.

### Campaign E — design-build-test-learn materials loop

The agent selects candidates under UQ/AD/OOD and process constraints, requests experiments,
reads measurements, updates rankings and demonstrates both discovery and learning under a
fixed budget.

## 9. Release stages

| Stage | Deliverable | Claim allowed |
| --- | --- | --- |
| `P0 EvidenceCore` | Current 7 real public tasks + scorer fixture | Evidence and analysis reliability only |
| `P1 ReplayCore` | Sanitized thermodynamics, DFT, MD, mesoscale and continuum replays | Reproducible workflow completion on frozen outputs |
| `P2 LiveCompute` | Sandboxed software and authorized HPC execution | Live scientific tool execution and recovery |
| `P3 DigitalLab` | Experiment protocols and scientific-robot digital twins | Embodied planning and simulated safe execution |
| `P4 PhysicalLoop` | Supervised instruments/robots and adaptive campaigns | Physical closed-loop performance on the released hardware configuration |
| `P5 Hidden evaluation` | Externally adjudicated hidden tasks and campaigns | Headline comparison and leaderboard claims |

The repository must always state which stage is actually implemented. The presence of a task
specification in the roadmap is not evidence that the corresponding runtime or physical
benchmark is complete.

## 10. Immediate implementation rule

All new benchmark tasks must enter through a task contract containing:

- scientific goal and terminal states;
- suite, horizon, autonomy target and execution mode;
- required inputs and admissible tools;
- required artifacts and source identities;
- scientific and execution verifier gates;
- resource and intervention budgets;
- fault-injection cases;
- human baseline work unit;
- replay/live/physical status;
- contamination and hidden-test grouping key.

This prevents the benchmark from becoming an unstructured list of questions and allows it to
measure gradual replacement of real professional work.


## 11. Goal-Driven v0.4 mapping

The 12 materials suites are instantiated as a role-level Goal-Driven work graph rather than an
unordered checklist. The current synthetic fixture requires mission identity, evidence,
thermodynamics, DFT, MLIP, MD, mesoscale, continuum, experiment and decision units. Each unit
closes one or more independent criteria and preserves a cross-scale lineage contract.

A materials role-replacement claim additionally requires representative hidden cases, real
agent runs, repeated trials, human baseline time and at least one adversarial fault family per
major solver or experimental handoff.
