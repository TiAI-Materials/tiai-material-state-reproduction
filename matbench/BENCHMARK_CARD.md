# TiAI-MatBench benchmark card — v0.1 public development set

## Intended use

TiAI-MatBench measures whether a research agent can produce a numerically correct,
source-bound and scientifically calibrated answer from frozen materials-research assets.
The intended unit is an **agent run**, not a conversational impression. The output is
machine-readable, and every scored assertion is evaluated by a fixed rule.

The public development set supports implementation testing, baseline debugging, error
taxonomy development and collaboration design. Because its references are visible, it is
not a blind test set and must not be used for a definitive leaderboard claim.

## Scientific construction principles

1. **Real released tasks first.** Seven tasks are derived from the released TiAI material-
   state reproduction package. Synthetic data are reserved for testing the scorer itself.
2. **Evidence is an object, not prose decoration.** A citation carries an asset path, a
   frozen Git blob identity and a permitted locator.
3. **State and source are part of the answer.** Temperature regime, material state and
   paper-family split cannot be discarded while keeping only a property value.
4. **Execution is observable.** A run distinguishes answer, abstention and failure and
   reports artifacts and warnings.
5. **No LLM judge.** Scoring is deterministic and inspectable.
6. **Fatal scientific errors cannot be averaged away.** Critical gates zero or cap a task.

## Task taxonomy

| Track | What it tests | v0.1 task |
| --- | --- | --- |
| source-aware statistics | pooled, equal-source and within-source distinctions | RT and 500–<800 °C slope tasks |
| state/condition fidelity | preservation of temperature-specific cohorts | separate-cohort accounting |
| claim calibration | descriptive evidence versus causal inference | pooled-slope causal claim |
| source split integrity | paper-family grouping and no cross-fold source leakage | 1,111 → 1,070 → 913 cohort accounting |
| provenance | task/query/source/locator identity | extraction protocol identity fields |
| abstention | refusal outside released estimand | complete unseen-corpus prospective request |
| execution integrity | deterministic machine-readable receipts | synthetic scorer self-check |

## Evidence boundary

The track is closed-book with respect to evidence: each task lists all admissible assets and
locator prefixes. A response may use fewer assets, but it may not introduce an undeclared
file. The blob SHA prevents a same-path file from silently changing. This design measures
whether an agent used the supplied evidence correctly; it does not measure unrestricted web
research.

## Metrics and gates

The report exposes:

- post-gate macro score over real released tasks (primary);
- raw real-task macro score before critical gates;
- synthetic scorer-fixture score and all-task harness diagnostics separately;
- per-track macro scores;
- per-dimension macro scores;
- every rule result;
- critical-violation counts.

Examples of zero-score events are source leakage, temperature-regime mixing, fabricated or
unregistered evidence, unsupported causal endorsement and answering a prospective estimand
that the released retrospective package cannot identify. Missing required evidence or a
failed tool can impose a score cap when the numerical portion remains partially useful.

## Data provenance and licensing

The benchmark adds task and scoring metadata around files already present in this repository.
It does not redistribute source articles, publisher figures, credentials, API histories or
the complete curated corpus. Original-source documents must be acquired lawfully. The
benchmark records only released asset identities and locators.

## Contamination policy

The development tasks and references are public by design. Any future blind evaluation must:

- freeze candidate tasks before model access;
- retain a private reference/gate file;
- group variants by source and scientific template;
- prevent near-duplicate task templates from crossing development and test sets;
- publish task hashes and the hidden-set construction protocol after evaluation;
- disclose any model or agent exposure to TiAI repositories.

A public-dev score and a hidden-test score must never be presented as interchangeable.

## Baseline protocol

A defensible baseline report should include at least:

- model and agent version;
- prompt and tool policy;
- temperature/seed when applicable;
- retry and timeout policy;
- whether evidence files were directly visible;
- run success rate, cost and wall time;
- post-gate score, raw score and violation profile.

The included oracle is a unit-test fixture. The included naive baseline is a negative control,
not a competitive model baseline.

## Limitations

- The current domain is titanium-alloy and titanium-matrix-composite evidence, not all
  materials science.
- The public set is small and visible.
- Evidence-locator validation checks the frozen identity and declared locator contract; it
  does not independently re-download publisher documents.
- Most tasks evaluate analysis and evidence discipline rather than long-running DFT/MD jobs.
- English is the primary task language; Chinese mirror prompts are supplied but cross-language
  equivalence has not yet been independently adjudicated.

## Release path

A publication-grade v1 should add an externally reviewed hidden set, at least two additional
materials families, tool-execution tasks with sandboxed artifacts, multi-run uncertainty,
strong model/agent baselines, contamination audits, inter-annotator agreement and an error
analysis that separates domain knowledge from evidence-use and execution failures.
