# Related-work landscape and TiAI-AgentBench boundary

This document positions the full-stack benchmark. It does not claim that one benchmark should
replace every existing benchmark; different systems isolate different parts of professional
work.

## Property and materials-model benchmarks

- **Matbench** standardizes materials-property prediction datasets and nested validation. It
  evaluates predictive models, not autonomous research agents. The established name is why
  `TiAI-MatBench` is retained only as a backward-compatible package identifier while the
  umbrella project is named `TiAI-AgentBench`.
- **Matbench Discovery** and related discovery benchmarks evaluate stability or discovery
  prediction, but not tool execution, recovery, experiments or complete research campaigns.

## Scientific coding and research-agent benchmarks

- **ScienceAgentBench** evaluates code generation for 102 data-driven scientific tasks drawn
  from publications and checks programs, execution and cost.
- **SciAgentGym / SciAgentBench** evaluates multi-step tool orchestration over a large
  scientific-tool environment and shows strong horizon effects.
- **SCI-AGENT-EXAM** covers multiple research task types and requires executable and textual
  artifacts.
- **MLR-Bench** evaluates open-ended machine-learning research across idea, proposal,
  experiment and writing stages and highlights fabricated or invalid experimental results.
- **DeployBench** evaluates whether agents can install and execute research artifacts in fresh
  environments; many failures arise from agents stopping after verifying the wrong target.
- **DSAgentBench** evaluates end-to-end data-science work inside real computer environments,
  including data, modeling, visualization and validation.

These benchmarks motivate executable artifacts, trajectory analysis, environment realism and
long-horizon evaluation. TiAI-AgentBench adopts those principles but adds material-state,
solver, multiscale, specimen, instrument and physical-science gates.

## Computational materials-agent benchmarks

- **AutoMat** evaluates reproduction of findings from computational-materials papers.
- **CompMat-Bench** contains 94 tasks derived from computational-materials studies, uses
  precomputed expensive simulations and fixed-rule grading, and evaluates single tasks and
  linked workflows.
- **DFT-Agent Bench** focuses on autonomous Quantum ESPRESSO tasks, scaffold effects and
  execution provenance.
- **MatToolBench** evaluates multimodal agents operating professional materials software.
- **MatScope / MatEvoBench-20** evaluates condition-specific reasoning and revision as
  laboratory observations accumulate.

The earlier EvidenceCore deliberately focused on evidence and source boundaries. The full
benchmark now treats these computational and software capabilities as first-class suites
rather than excluding them. Its additional target is the **handoff among methods** and the
fraction of a full professional workflow actually replaced.

## Autonomous science and experimental campaigns

- **Autonomous Science Bench** evaluates budgeted design-build-test-learn campaigns grounded
  in working laboratory experiments, with separate discovery and learning gates.
- Autonomous-laboratory systems and benchmark frameworks increasingly evaluate experiment
  choice, protocol generation, result intake and iterative decision-making rather than static
  answers.

TiAI-AgentBench adopts campaign-level budgets and separate discovery/learning concepts for the
materials closed-loop suite, while adding source, state, process, simulation and specimen
lineage.

## Robotics and scientific embodied-agent benchmarks

- **RoboCerebra** and long-horizon manipulation benchmarks evaluate hierarchical planning,
  reflection, memory and subtask sequences.
- **LADDER** isolates task-horizon scaling and shows that orchestration and verification help
  but do not eliminate physical execution failures.
- **SafeLab** evaluates scientific-laboratory manipulation with trajectory-level safety,
  calibrated laboratory assets and simulated-to-physical checks.
- **SciHorizon-eLab** compiles natural-language scientific protocols into certified embodied
  tasks with ordered step-level evaluation.
- **ADePT** frames autonomous-laboratory robotics across adaptability and learning, dexterity,
  perception and task complexity.
- **AutoLabs** evaluates multi-agent generation of hardware-ready experimental procedures and
  quantitative correctness for liquid-handling workflows.

These works support the user's broader premise: benchmark design must eventually evaluate
physical work, not only text or code. TiAI-AgentBench therefore includes a staged
`S09_ROBOT_LAB` suite with protocol compilation, digital twins, trajectory safety, physical
replay and fault recovery.

## TiAI-AgentBench's intended contribution

The defensible target is not “the first scientific-agent benchmark” or “the first materials
benchmark.” It is the integration of the following in one domain-adapter architecture:

1. professional work units from evidence to physical action;
2. materials-specific identities and fatal scientific gates;
3. live, replay and physical execution modes kept separate;
4. multiscale quantity and uncertainty handoff evaluation;
5. checkpoint, recovery, provenance, human-intervention and resource accounting;
6. work-replacement coverage rather than answer accuracy alone;
7. unit, workflow, campaign and embodied closed-loop reporting;
8. real titanium-alloy flagship missions with negative results and counterexamples.

The benchmark is designed so that chemistry, biology, manufacturing and other verticals can
reuse the core contracts while supplying their own domain objects, tools and safety gates.

## Naming

The executable package and historical directory remain `tiai-matbench` to avoid breaking the
v0.1 development pack. The paper- and program-facing umbrella name is `TiAI-AgentBench`.
A final public name should be frozen before DOI registration and leaderboard launch.

## Primary references

1. Dunn, A. et al. “Benchmarking materials property prediction methods: the Matbench test set
   and Automatminer reference algorithm.” *npj Computational Materials* 6, 138 (2020).
2. Chen, Z. et al. “ScienceAgentBench: Toward Rigorous Assessment of Language Agents for
   Data-Driven Scientific Discovery.” arXiv:2410.05080.
3. Zhang, C. et al. “CompMat-Bench: Benchmarking AI Agents for Computational Materials
   Science.” arXiv:2610.00636.
4. Shen, Y. et al. “SciAgentGym: Benchmarking Multi-Step Scientific Tool-use in LLM Agents.”
   arXiv:2602.12984.
5. Zhong, T. et al. “SCI-AGENT-EXAM: Benchmarking Agents on Scientific Research Tasks.”
   arXiv:2610.32441.
6. Wen, Y. and Liu, H. “Autonomous Science Bench: Evaluating AI Agents for Autonomous
   Scientific Discovery.” arXiv:2610.18449.
7. Bai, F. et al. “SafeLab: An Interactive High-Fidelity Benchmark for Embodied Safety in
   Scientific Robotics.” ICML 2026.
8. Qin, M. et al. “SciHorizon-eLab: An Agentic Protocol-to-Task Compiler for Scalable
   Benchmarking of Scientific Embodied Agents.” arXiv:2609.30971.
9. Salazar-Villacis, P. and Benyahia, B. “The ADePT framework for assessing autonomous
   laboratory robotics.” *Communications Chemistry* 9, 99 (2026).
10. Panapitiya, G. et al. “AutoLabs: cognitive multi-agent systems with self-correction for
    autonomous chemical experimentation.” *Scientific Reports* 16, 19554 (2026).
