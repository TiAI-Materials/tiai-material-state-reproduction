# Related-work boundary and naming note

This file fixes the intended scientific gap of the v0.1 development set. It is not a
claim that other benchmarks are deficient; the task units and evaluation targets differ.

## Existing materials benchmarks

- **Matbench v0.1** (Dunn et al., *npj Computational Materials*, 2020) standardizes
  materials-property prediction datasets and nested cross-validation. It is not an agent
  benchmark. Its established name creates a naming collision with the internal working name
  `TiAI-MatBench`.
- **AutoMat** (arXiv:2605.00803, 2026) evaluates whether coding agents can reproduce claims
  from computational-materials papers.
- **CompMat-Bench** (arXiv:2610.00636, 2026) contains 94 tasks from 15 computational-materials
  studies, precomputes expensive simulations and uses fixed-rule grading without an LLM judge.
- **MatToolBench** (arXiv:2609.37053, 2026) evaluates multimodal agents on 204 real-environment
  tasks across ten professional materials tools in a Windows 11 virtual machine.
- **MatScope / MatEvoBench-20** (arXiv:2611.12014, 2026) evaluates condition-specific reasoning,
  knowledge transfer and revision as materials-laboratory observations accumulate.

## TiAI benchmark boundary

The present benchmark does not try to replace property-prediction, computational-workflow,
GUI-operation or evolving-laboratory benchmarks. It operationalizes a narrower reliability
question:

> Can an agent bind its answer to the correct source and material state, preserve source-
> isolated evaluation, execute a checkable analysis, and refuse claims that the evidence
> cannot identify?

Its distinctive scored objects are therefore source identities and locators, condition/state
boundaries, paper-family split integrity, claim scope, abstention and critical scientific
violations. This is complementary to task-completion and tool-use success.

## Public-name decision

`TiAI-MatBench` is retained as the repository working identifier because it connects to the
existing TiAI assets. Before a paper or leaderboard launch, the authors should choose a name
that cannot be confused with the established Materials Project **Matbench** benchmark. Possible
paper-facing candidates include `SourceMat-AgentBench`, `MatSciTrust`, and
`EvidenceMatBench`. Renaming should occur before DOI registration so that package, paper and
leaderboard identifiers remain stable.

## Primary references

1. Dunn, A. et al. “Benchmarking materials property prediction methods: the Matbench test set
   and Automatminer reference algorithm.” *npj Computational Materials* 6, 138 (2020).
   DOI: `10.1038/s41524-020-00406-3`.
2. “Can Coding Agents Reproduce Findings in Computational Materials Science?”
   arXiv:`2605.00803`.
3. Zhang, C. et al. “CompMat-Bench: Benchmarking AI Agents for Computational Materials
   Science.” arXiv:`2610.00636`.
4. Wu, M. et al. “MatToolBench: Benchmarking Multimodal Agents in Real-World Materials
   Science Workflows.” arXiv:`2609.37053`.
5. Dong, X. et al. “Benchmarking language models and agents for scientific reasoning in
   evolving materials laboratories.” arXiv:`2611.12014`.
