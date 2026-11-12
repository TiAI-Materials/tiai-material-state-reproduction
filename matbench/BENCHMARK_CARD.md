# TiAI-AgentBench benchmark card — Goal-Driven Core v0.4

## Intended use

TiAI-AgentBench evaluates whether an AI agent can replace **verified units of professional
work**, from one local task to a workflow, role, team, organization or industry. The unit of
evaluation is an agent run with a goal contract, work graph, execution trajectory, artifacts,
independent criteria, faults, interventions and resource receipts—not a conversational
impression.

Materials science is the first active full vertical. It is not the benchmark's final boundary.
The same core protocol is designed for chemistry, biotechnology, software, EDA, CAD and
construction, CAE, controls and electrical engineering, robotics, manufacturing, healthcare,
finance, legal work, logistics, energy, education, enterprise operations, mathematics/TCS,
media/design and public administration.

## Source-derived thesis and engineering interpretation

The design operationalizes three claims associated with Li Dang's Goal-Driven proposal:

1. long-running agents need an explicit `Goal`, strict `Criteria`, persistent workers and a
   master/verifier that does not accept a worker's self-declared completion;
2. locally executable and thoroughly verifiable work is the first replacement frontier;
3. the fraction of professional work that still requires a human in the loop must be measured,
   not hidden.

TiAI-AgentBench treats these as hypotheses to evaluate rather than as established facts. It
therefore measures replacement and human dependence separately and permits a successful run to
retain mandatory human authority when a domain requires it.

## Release layers

1. **EvidenceCore v0.1** — seven real released source/state/statistics tasks and one isolated
   scorer self-test.
2. **Materials Full-Stack v0.2** — 12 suites and 39 staged tasks from evidence to multiscale
   simulation, experiments, robotics and communication.
3. **Work-Replacement ProtocolCore v0.3** — criticality-weighted work units, artifacts,
   interventions, fault recovery, resource use and trajectory safety.
4. **Goal-Driven Core v0.4** — explicit Goal/Criteria contracts, persistent episodes,
   independent completion authority, human-loop measurement, role-to-industry scope and
   specification-driven tool reconstruction.

## Goal-Driven execution model

```text
Goal Contract
→ professional Work Graph
→ worker/subagent episodes
→ tools and auditable artifacts
→ independent Criteria evaluation
→ restart / repair / replan if criteria are unmet
→ verified success, abstention, failure or budget exhaustion
```

A worker may claim completion, but only the declared verifier can close the goal. Required
criteria that are self-verified, unsupported by artifacts or evaluated after an untracked human
repair do not pass. An inactive or failed episode must be resumed from an identified checkpoint
or be recorded as unrecovered.

## Replacement scopes

Results are reported at six levels:

```text
TASK → WORKFLOW → ROLE → TEAM → ORGANIZATION → INDUSTRY
```

An agent that automates one visible task does not receive role- or industry-replacement credit.
The benchmark requires a weighted human work graph and records which units were performed by an
agent, jointly, or by a human.

## Verifiability levels

| Level | Evaluation environment |
| --- | --- |
| `V0_LOCAL_DETERMINISTIC` | locally executable and deterministically or differentially testable |
| `V1_COMPUTE_OR_REPLAY` | scientific solver, authorized compute or frozen replay |
| `V2_DIGITAL_TWIN` | stateful simulator with trajectory, fault and recovery checks |
| `V3_PHYSICAL_INSTRUMENT` | instrument, specimen or robot execution with safety receipts |
| `V4_SOCIO_REGULATORY` | material human judgment, consent, negotiation or regulatory authority |

Scores are not transferable across levels. Replay is not live compute; a digital twin is not a
physical laboratory; correct decision support is not autonomous clinical authority.

## Universal metrics

The v0.4 scorer reports a vector rather than one headline score:

- **Goal-Driven Success (`GDS`)** — required criteria, persistence, recovery and budget gates
  pass;
- **Goal Attainment (`GA`)** — the declared success terminal state is independently verified;
- **Criteria Closure Rate (`CCR`)** — weighted fraction of criteria closed;
- **Verified Work Replacement (`VWR`)** — criticality-weighted work completed autonomously and
  independently accepted;
- **Human-Loop Fraction (`HLF`)** — weighted human or mixed work plus intervention burden;
- **Autonomous Replacement Potential (`ARP`)** — observed `1 - HLF`, never a universal forecast;
- **Persistence Integrity (`PI`)** — continuity, heartbeat and recovery integrity;
- **Continuity Recovery Rate (`CRR`)** — failed or idle episodes successfully resumed;
- **Fault Recovery Rate (`FRR`)** — required injected faults successfully recovered;
- **False Completion Rate (`FCR`)** — runs claiming success before required criteria close;
- **Functional Signoff Rate (`FSR`)** — compatibility/signoff criteria passed for reconstructed
  tools;
- **Hours Replaced** — verified baseline human time replaced;
- **Resource-Normalized Utility (`RNU`)** — verified replacement relative to declared budgets.

The older ProtocolCore vector—`VSS`, `WRC`, `E2E_ASR`, `HIR`, `RRR`, `RNU`, `SSR`—remains for
backward compatibility. EvidenceCore retains its six source/state/statistics dimensions.

## Materials full-stack vertical

The materials vertical is not restricted to literature or data analysis. Its flagship role-level
protocol spans:

```text
mission and material identity
→ source-resolved evidence
→ CALPHAD / Scheil / kinetics
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
specimen and model lineage, applicability domain, uncertainty, calibration independence and
claim scope. Two individually converged calculations fail the multiscale protocol when the
handoff between them is invalid.

## Tool operation and tool reconstruction

The benchmark distinguishes two different replacement claims:

- `TOOL_USE`: configure and operate an admitted professional tool correctly;
- `TOOL_RECONSTRUCTION`: implement a compatible tool from a frozen specification and obtain
  functional signoff through differential, formal, simulation or physical tests.

The first executable reconstruction fixture is a 1D axial-bar finite-element kernel with 12
frozen cases. It checks numerical agreement, global equilibrium, fixed-boundary invariants and
invalid-input behavior. It validates the reconstruction harness; it is not evidence that an
Ansys-class product has been rebuilt.

## Robotics and physical work

Robotics is a horizontal work domain and a materials-laboratory suite. Evaluation is staged:

1. protocol-to-action compilation;
2. digital-twin execution;
3. supervised physical replay;
4. adaptive physical closed loop.

Task success and trajectory safety are separate. A robot that reaches the final state after an
unsafe force, collision, tilt, contamination, sample-identity or authorization event fails the
physical protocol.

## Human authority and bounded replacement

The benchmark does not force every profession to report full autonomy. A v0.4 synthetic
healthcare fixture demonstrates a successful workflow in which the agent performs de-
identification, evidence summarization and risk screening, while a licensed clinician retains
the final decision and consent interaction. The run can achieve `GDS=1` while `VWR<1` and
`HLF>0`. This is deliberate: success and replacement are different quantities.

## Fatal conditions

The following cannot be averaged away by attractive prose or partial task completion:

- premature or false completion;
- self-verification where independence is required;
- missing or identity-mismatched artifacts;
- nonconverged solver output reported as a result;
- invalid cross-scale transfer;
- source, train/test or workflow leakage;
- hidden human repair or takeover;
- required faults not recovered;
- resource or authorization violations;
- unsafe digital or physical trajectories;
- unsupported causal, mechanistic, clinical or regulatory claims.

## Current executable contents

The repository currently contains:

- a real public EvidenceCore materials pack;
- a validated 12-suite materials architecture with 39 staged task specifications;
- an executable domain-neutral ProtocolCore;
- a 20-family industry registry with 80 representative roles;
- four synthetic Goal-Driven protocols: materials multiscale, CAE reconstruction, scientific
  robotics and a mandatory-human-authority healthcare workflow;
- oracle, human-loop and adversarial regressions;
- one executable finite-element reconstruction fixture.

Synthetic protocol fixtures validate schemas and scorers. They do not demonstrate that a real
agent has replaced the corresponding profession.

## Data and artifact governance

Each run must record, where applicable:

- source, task and material/specimen identity;
- software, solver, model, database, pseudopotential or potential identity;
- inputs, boundary conditions, hashes and versions;
- checkpoints, restarts, failures and human interventions;
- raw and derived artifacts;
- verifier identity and independence;
- resource use and safety events;
- execution level: replay, live compute, digital twin or physical.

Commercial binaries and proprietary databases are not redistributed. An adapter may expose a
licensed tool's input/output and verification contract without distributing the licensed asset.

## Contamination and hidden evaluation

Public references cannot support definitive leaderboard claims. A publication-grade release
must freeze hidden tasks before model access, hold out source and workflow families, keep
criteria and adversarial variants private, audit training contamination, run multiple trials,
report time/cost/interventions and separate replay, live-compute, digital-twin and physical
scores.

## Claim boundary

The current release supports claims about the **benchmark protocol and evaluator**, not universal
job replacement. EvidenceCore is the only released real scientific task pack. Role,
organization or industry replacement claims require representative human baselines, hidden real
work, repeated runs, expert adjudication, authorized tools/compute, certified digital twins and
supervised physical evaluation.
