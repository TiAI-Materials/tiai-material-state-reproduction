# Cross-industry Goal-Driven work-replacement core

## Purpose

The universal core evaluates professional work independently of any one industry. It does not
assume that every occupation is already replaceable. It defines a common contract for measuring
which work units an agent completes, which remain human-led, whether the result is independently
verified, and whether the system persists safely until its criteria are closed.

Materials science is the first active vertical because it contains source work, scientific
software, local computation, multiscale simulation, experiments, instruments and robotics in one
connected domain.

## Core objects

```text
GoalContract
  objective + terminal states + non-goals + budgets + heartbeat/restart policy

WorkGraph
  criticality-weighted human work units + dependencies + baseline human time

AgentEpisodes
  worker/subagent identity + steps + checkpoints + inactivity/failure + resume lineage

Criteria
  required/optional + weight + verifier type + independence + required artifacts

RunLedger
  work results + artifact hashes + faults + interventions + resources + terminal status
```

The worker's completion claim is an input to evaluation, not proof of completion.

## Industry and profession federation

`GOAL_DRIVEN_REGISTRY.json` stages 20 industry families and 80 representative roles. Every new
vertical supplies:

- work objects and stable identities;
- tool and execution environments;
- required artifacts;
- fatal domain gates;
- safety, legal and authorization constraints;
- baseline human work units and time;
- hidden task families and contamination groups.

The core supports six replacement scopes: `TASK`, `WORKFLOW`, `ROLE`, `TEAM`, `ORGANIZATION` and
`INDUSTRY`. Results may only be reported at a scope represented by the task pack.

## Verifiability frontier

The benchmark separates:

- `V0_LOCAL_DETERMINISTIC`: compilers, formal systems, bounded algorithms and local test suites;
- `V1_COMPUTE_OR_REPLAY`: scientific solvers, HPC and frozen computation replay;
- `V2_DIGITAL_TWIN`: robots, instruments, manufacturing cells and other stateful simulators;
- `V3_PHYSICAL_INSTRUMENT`: real equipment, specimens and embodied trajectories;
- `V4_SOCIO_REGULATORY`: consent, negotiation, professional authority and regulation.

This avoids turning a successful local test into an unsupported claim of physical or social
replacement.

## Human-loop accounting

For work unit `i` with criticality `w_i`, performer credit is 1.0 for `AGENT`, 0.5 for `MIXED`
and 0.0 for `HUMAN`, provided the attached criteria pass. Interventions add a disclosed penalty.

```text
VWR = sum(w_i * verified_autonomy_credit_i) / sum(w_i)
HLF = weighted human/mixed share + normalized intervention burden
ARP = max(0, 1 - HLF)
```

`ARP` is an observed run metric, not a prediction that a whole occupation will disappear.
A workflow may be scientifically successful with mandatory human authority and therefore have
`GDS=1` but `VWR<1`.

## Persistence and false completion

A Goal-Driven run records worker episodes. Failed or idle episodes require an identified
successor. Required injected faults require recovery evidence. Required criteria must be
independently verified. The following cause a false-completion failure:

- success claimed while required criteria remain open;
- a final episode marked `CRITERIA_MET` when criteria are not met;
- terminal `SUCCESS` after failed independent signoff;
- untracked human repair presented as autonomous work.

## Tool-use and tool-reconstruction tracks

Operating a tool and replacing the tool are distinct:

```text
TOOL_USE:
  typed input → admitted software → execution receipt → output verification

TOOL_RECONSTRUCTION:
  frozen specification → implementation → build → differential/formal/physics tests
  → compatibility signoff
```

The reconstruction track is necessary for evaluating specification-driven reimplementation of
CAD, EDA, CAE, control/signal and scientific software without confusing a toy demo with product
compatibility.

## v0.4 executable fixtures

Four protocols are included as `SYNTHETIC_PROTOCOL_TEST`:

1. a role-level materials multiscale evidence-to-decision campaign;
2. a specification-driven 1D finite-element solver reconstruction;
3. a scientific-robot digital-twin workflow with trajectory and recovery criteria;
4. a healthcare decision-support workflow that deliberately retains licensed human authority.

The first three test high-verifiability replacement. The fourth tests whether the scorer can
represent successful assistance without falsely claiming full replacement.

## Metrics

Goal-Driven Core reports:

`GDS`, `GA`, `CCR`, `VWR`, `HLF`, `ARP`, `PI`, `CRR`, `FRR`, `FCR`, `FSR`,
`HOURS_REPLACED`, and `RNU`.

ProtocolCore v0.3 remains available with `VSS`, `WRC`, `E2E_ASR`, `HIR`, `RRR`, `RNU`, and
`SSR` for backward compatibility.

## Claim boundary

The universal schema can represent every industry; it does not mean every industry pack has
been built. Only adapters backed by real tasks, human baselines, hidden criteria, executable
artifacts and independent adjudication may support capability claims.
