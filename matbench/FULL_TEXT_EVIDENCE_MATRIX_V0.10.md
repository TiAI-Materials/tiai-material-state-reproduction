# Full-Text Evidence Matrix v0.10

## Purpose

This release converts the publication-method review into an auditable benchmark asset. The detailed machine-readable matrix is stored as `literature/FULL_TEXT_EVIDENCE_MATRIX_V0.10.json.gz.b64`; the validator reads the gzip payload directly. It
counts **51 primary full-paper bodies** inspected on 2026-11-13. Abstract-only, metadata-only,
malformed, inaccessible, and duplicate records do not count.

The matrix is not a bibliography padding exercise. Every counted record contains:

- the professional-work or scientific task horizon;
- the paper's verifier pattern;
- method axes relevant to repeatability, recovery, human intervention, cost, safety, or claim
  boundaries;
- one transferable design rule;
- one explicit limitation.

`full_text_matrix.py` rejects a release with fewer than 50 counted papers, duplicate normalized
titles, abstract-only entries, unverified entries, declaration/count mismatches, or missing claim
boundaries.

## Cross-paper result

The 51-paper audit supports six design conclusions:

1. **Terminal success is insufficient.** Durable state, artifacts, provenance, execution
   contracts, intermediate progress, and process-level safety are repeatedly required.
2. **Scaffold comparisons must be matched.** Model, task, tools, time, call budget, compute and
   cost have to be frozen before attributing gains to Goal-Driven orchestration.
3. **One run is not reliability.** Repeats, task-level agreement, horizon effects and uncertainty
   must be reported.
4. **Scientific work needs domain gates.** Evidence alignment, solver convergence, material and
   specimen identity, multiscale compatibility and bounded claims cannot be replaced by generic
   code or GUI success.
5. **Embodied success can be unsafe.** The benchmark must retain safe success, unsafe success,
   safe failure, unsafe failure, cumulative risk and ordered step gates.
6. **Human work remains measurable.** Expert task construction, hidden adjudication, safety
   authority and open-ended scientific judgment must enter Human-Loop Fraction rather than
   disappearing from the score.

## Direct consequence for the registered experiment

The frozen six-arm pilot remains the shortest causal test:

- single agent;
- ordinary multi-agent;
- Goal-Driven without independent verifier;
- Goal-Driven without recovery;
- Goal-Driven without provenance/claim gates;
- full Goal-Driven.

The literature matrix strengthens the requirement for identical task/model/provider/tool/budget
bindings, external native-verifier receipts, repeated trials, intervention/recovery/cost ledgers,
and no inference of safety or autonomy from missing evidence.

## Claim boundary

This is **method evidence**, not a new TiAI-AgentBench performance result. It does not replace:

- the 192 registered real agent runs;
- the three minimal LiveCompute tasks;
- digital-twin or supervised physical replay;
- contamination and near-duplicate audits;
- independent external expert adjudication.

No system advantage, job replacement, organization replacement or industry replacement is
claimed from the literature count.
