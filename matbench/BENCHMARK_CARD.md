# TiAI-AgentBench benchmark card — v0.2 architecture and EvidenceCore v0.1

## Intended use

TiAI-AgentBench evaluates whether an AI agent can replace verified units of professional
materials-research work. The unit of evaluation is an **agent run with artifacts and an
execution trajectory**, not a conversational impression.

The umbrella benchmark covers the full research lifecycle:

```text
goal → evidence → problem definition → method selection → execution → verification/recovery
→ multiscale integration → decision → experiment/robot action → knowledge update → artifact
```

The current executable public pack, EvidenceCore, evaluates source identity, material state,
condition fidelity, source-aware statistics, split integrity, claim calibration, abstention
and basic execution receipts. The full-stack registry adds staged suites for research
software, thermodynamics, DFT, MLIP/MD, mesoscale and continuum simulation, cross-scale
integration, experiments, robotics, campaigns and scientific communication.

## What the benchmark is trying to measure

The central question is not whether an agent can produce a plausible answer. It is:

> How much of the work normally performed by literature researchers, data analysts,
> computational materials scientists, simulation engineers, experimentalists, instrument
> operators, laboratory-automation engineers, scientific leads and authors can the agent
> complete autonomously and pass to an independent verifier?

The benchmark therefore reports capability by work horizon, autonomy level, execution mode,
suite, resource budget, intervention rate and safety—not only by final-answer accuracy.

## Scientific construction principles

1. **Goal → Execution → Verification.** A plan is not completion. Consequential work must
   produce artifacts and pass independent gates.
2. **Real work units before generic questions.** Tasks are derived from actual research
   activities and failure modes.
3. **Evidence is an object.** Sources, locators, material states, structures, specimens,
   models and simulation inputs have stable identities.
4. **Deterministic work belongs in code.** Stable checks, unit conversions, parsers and
   numerical comparisons are programmatic; agents handle planning, adaptation and recovery.
5. **The truth chain excludes unsupported model invention.** Scientific numerical truth must
   originate from executed code, admitted models, instruments or admissible sources.
6. **Human intervention is observable.** Corrections, overrides and takeovers are logged and
   reduce autonomy credit.
7. **Replay, live compute and physical work are distinct.** A frozen replay is not relabeled
   as an HPC run; a digital twin is not relabeled as a physical laboratory.
8. **Fatal errors cannot be averaged away.** Identity, convergence, leakage, cross-scale,
   provenance, authorization and safety failures trigger gates.
9. **Negative results remain.** Nonconvergence, absence of an event on an insufficient time
   scale and rejected hypotheses are retained in the failure ledger.
10. **Cross-industry extensibility.** The runtime and work-replacement protocol is generic;
    materials science supplies the first domain adapter.

## Suite taxonomy

| Suite | Professional work represented |
| --- | --- |
| `S00_EVIDENCE` | literature review, extraction, scientific memory and source-aware analysis |
| `S01_RESEARCH_OPS` | environment setup, artifact deployment, HPC dispatch, checkpoint and recovery |
| `S02_THERMO_KINETICS` | CALPHAD, Scheil, diffusion, precipitation and phase stability |
| `S03_DFT_ATOMISTIC` | crystallography, DFT, defects, interfaces and energy paths |
| `S04_MLIP_MD` | dataset curation, potential training/admission and MD |
| `S05_MESO` | phase-field, cellular automata and mesoscale evolution |
| `S06_CONTINUUM` | CPFEM, RVE, FEM, calibration and field validation |
| `S07_MULTISCALE` | quantity handoffs, UQ propagation and cross-scale contradiction resolution |
| `S08_EXPERIMENT` | experimental design, specimen ledgers, DIC, EBSD and characterization |
| `S09_ROBOT_LAB` | protocol compilation, safe embodied execution and hardware recovery |
| `S10_CAMPAIGN` | goal-directed end-to-end research campaigns and closed loops |
| `S11_COMMUNICATION` | figures, source data, manuscripts, peer review and revision |

## Work horizons and autonomy

Unit tasks test local competence. Workflow tasks test multi-step state and tool coordination.
Campaign tasks test method selection and budgets. Closed-loop tasks test adaptation from new
observations.

Autonomy ranges from `A0` advisory work to `A5` embodied closed-loop operation. A task's target
level is declared before evaluation. A system cannot gain A4/A5 credit by returning a plan for
work a human subsequently performs.

## Primary full-stack metrics

- **Verified Scientific Success (`VSS`)**: mandatory scientific and execution gates pass.
- **Work Replacement Coverage (`WRC`)**: criticality-weighted fraction of human work units
  executed autonomously and accepted independently.
- **End-to-End Autonomous Success Rate (`E2E_ASR`)**: full campaign success under fixed
  budgets.
- **Human Intervention Rate (`HIR`)**: frequency and severity of disclosed human help.
- **Recovery and Resume Reliability (`RRR`)**: successful terminal states after faults.
- **Resource-Normalized Utility (`RNU`)**: scientific utility relative to time, compute, cost
  and experimental budget.
- **Scientific Safety Rate (`SSR`)**: trajectory-level compliance with physical, instrument,
  data-governance and laboratory safety constraints.

No single aggregate may hide suite- or horizon-level collapse. Results must include the metric
vector and gate profile.

## Multiscale evaluation contract

Cross-scale tasks must verify more than the individual solvers. Each handoff declares:

- source and target quantity semantics;
- units and normalization;
- composition, temperature, material state and structure compatibility;
- phase, specimen, trajectory and model lineage;
- uncertainty and applicability-domain propagation;
- calibration and validation independence;
- allowed claims and contradiction handling.

A scientifically correct abstention from an invalid handoff can outscore a forced but
unsupported multiscale narrative.

## Robotics and physical-lab protocol

Physical evaluation is staged through protocol reasoning, digital twins, supervised physical
replay and adaptive physical campaigns. Task success and trajectory safety are scored
separately. A robot that reaches the final state after unsafe force, tilt, collision,
contamination or sample-identity violations does not pass.

The physical benchmark must freeze or report:

- robot and instrument configuration;
- calibration and safety envelopes;
- sample and reagent inventory;
- perception and control interfaces;
- human emergency supervision;
- sim-to-real differences;
- intervention and abort policy.

## Current executable pack: EvidenceCore

EvidenceCore contains seven real released tasks and one isolated scorer fixture. Its primary
metric is the post-gate macro-average over only the real tasks. Its six dimensions are:

- outcome correctness;
- evidence fidelity;
- state/condition fidelity;
- split integrity;
- claim calibration;
- execution integrity.

Examples of critical failures are source leakage, temperature mixing, unregistered evidence,
unsupported causal endorsement and answering an estimand that the released evidence cannot
identify.

## Data and artifact governance

Each public task identifies admissible assets and frozen Git identities. Future computational
and physical task packs must additionally record:

- software, solver and parser versions;
- database, pseudopotential or interatomic-potential identities;
- input hashes and boundary conditions;
- hardware and parallel layout;
- queue time, wall time and restart lineage;
- raw-output and derived-output locations;
- convergence and admission status;
- sample, instrument and calibration identities;
- human interventions and safety events.

Commercial software and proprietary databases are not redistributed. A benchmark can expose
an adapter and input/output contract without exposing licensed binaries or files.

## Contamination policy

Public development references are visible and cannot support definitive leaderboard claims.
A blind release must:

- freeze candidate tasks before evaluated model access;
- keep reference values, gate thresholds and adversarial variants private;
- group variants by source, scientific template, structure lineage and workflow family;
- prevent near-duplicate protocols or calculations crossing development and test;
- disclose model and agent exposure to TiAI repositories;
- publish hashes and construction methodology after the evaluation window;
- separate public-development, private-replay, live-compute and physical-lab scores.

## Baseline reporting protocol

A defensible baseline must disclose:

- model, agent scaffold and prompt;
- tool permissions and network access;
- software and hardware environment;
- retry, timeout, checkpoint and recovery policy;
- number and severity of human interventions;
- run success distribution over repeated trials;
- wall time, compute, monetary and experimental cost;
- artifacts and failure ledger;
- per-suite, per-horizon and per-autonomy results;
- VSS, WRC, E2E_ASR, HIR, RRR, RNU and SSR where applicable.

The included oracle remains a scorer regression fixture, not a competitive baseline.

## Limitations and claim boundary

- EvidenceCore is currently the only executable public scientific pack.
- The 39 v0.2 task specifications are a validated implementation roadmap, not 39 completed
  benchmark environments.
- Sanitized simulation assets, licensed-software adapters, live HPC contracts, digital twins
  and physical-lab setups remain staged work.
- The benchmark begins with titanium alloys and titanium-matrix composites, not a complete
  census of materials science.
- Expert review remains necessary for open-ended mechanism novelty and physical safety, but
  expert review must be calibrated against deterministic artifacts and cannot replace them.

## Release path

1. keep EvidenceCore stable and add real agent baselines;
2. release sanitized computational replay packs;
3. add sandboxed and authorized live-compute tracks;
4. add experiment and characterization task packs;
5. certify scientific-robot digital twins;
6. run supervised physical tasks;
7. release externally adjudicated hidden campaigns and a public leaderboard.
