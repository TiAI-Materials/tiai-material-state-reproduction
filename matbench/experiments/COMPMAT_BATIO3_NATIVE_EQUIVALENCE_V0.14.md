# BaTiO3 official native grader equivalence / source-identity correction v0.14

**Scope:** one preregistered CompMat single-step task, using the publisher's actual
fixed-rule evaluator on four reference/control submissions. This is an upstream
native-grader self-test, **not** an Agent run, live simulation, or new TiAI score.

## Discovered and corrected source-identity error

While preparing `task_202603_034_step_batio3-dislocation-dipole-relaxed`,
the frozen v0.11 inventory's `task_tree_git_sha` resolved to the
`agent/` prompt subtree **rather than the task root**:

| Identity | Git tree SHA |
| --- | --- |
| Incorrectly labeled task root, actually `agent/` | `4d3b5a71cff0e4ceef5448c5336c9f01bc202c81` |
| Correct complete task root | `cc0f9a2fc727a9bdab09a6e6e8328b0a1358dafa` |
| Actual `grader/` subtree | `0f71732a63f6926d485fb6bfc9c556a62ba24091` |

All three identities are from the **same pinned** upstream CompMat-Bench
commit `03fec439ca9c9b1b14ea914896886b74d3e739bc`.
The other five preregistered public task-root pins and C03/C07 root pins
were independently compared against upstream `contents/tasks` and
`contents/workflows` at the same commit and matched.

The inventory and local validator are corrected **without changing**
task IDs, task selection, trial counts, model conditions, execution modes,
published score rules or science-owner assignments. The previously archived
source-lock v0.11 document remains historical; this v0.14 correction
supersedes that single incorrect identity. No hidden answer is exported.

## Actual official native-grader self-test on DESKTOP-B514PPT

The source-only runner fetches the four original Git blobs for
`grader/grader.py`, `grader/graderlib/grader_numeric.py`,
`grader/ground_truth.json` and
`grader/reference_submission/answer.json`, verifies each
`SHA-1(blob-size + NUL + bytes)` against the pinned Git SHA, then runs the
**unmodified** official grader in an isolated temporary directory. It tests
two valid and two invalid variations:

| Native case | Expected | Observed | Interpretation |
| --- | ---: | ---: | --- |
| Original reference | 1 | 1 | Published valid result |
| Coherent global BaO/TiO2 coordinate **and** nearest-core label swap | 1 | 1 | Correct scientifically equivalent naming convention |
| Nearest-core label swap alone | 0 | 0 | Inconsistent identity must not be credited |
| Region-A Ba spacing displaced by +0.2 Å | 0 | 0 | Physically incorrect quantity must not pass |

All four official `grader.py` evaluations returned process exit code 0.
The native report also distinguished `identity` and
`BaO_TiO2_swapped` exactly as required by the upstream rule.
This is a **high-value boundary check**: the verifier accepts
crystallographically equivalent naming while rejecting an incoherent
partial remapping. It does not relax the official numerical tolerances.

The frozen evidence is in
`COMPMAT_BATIO3_NATIVE_RECEIPT_V0.14.json`. It stores exact
Git blob identities, SHA-256 of downloaded grader bytes and raw stdout,
native exit statuses and accepted naming conventions. A reproducible
source-only runner lives at
`matbench/tools/replay_compmat_batio3_native_selftest.py`.

To re-execute independently with public GitHub API access:

```bash
python matbench/tools/replay_compmat_batio3_native_selftest.py --output /tmp/batio3-native.json
```

The offline CI tests are structural and fixed-receipt regression checks;
**they are not a new live execution of the upstream native scorer**.
The receipt is a source/self-test artifact, not a signed production
verifier authority bundle; no Agent is allowed to see its ground truth
during a blind run.

## Boundaries and next admissible execution

- **Actual reference/control outcomes:** 2 native passes / 2 native fails.
- **Real TiAI Agent attempts:** 0.
- **192-run pilot readiness:** 0 READY / 192 BLOCKED.
- **Published 516,859,324-byte core ZIP downloaded and independently SHA-256-verified:** no.
- **Fully staged per-task input workspace digests:** missing.
- **C07 licensed VASP POTCAR:** not verified.
- **Model/provider/tools/budgets:** unbound.
- **Four hidden RealReplay input identities and independent expert review:** unbound.
- **Independent production verifier trust root:** unbound.

Do not infer a Goal-Driven system effect, successful production simulation,
scientific convergence or physical safety from grader-reference tests.
The next highest-value route is to stage and validate official core task
input bytes, keeping the native grader outside the Agent workspace, then
bind a legitimate same-model six-arm runner. This work uses no A100,
no mother-machine heavy compute and does not touch active Ti65/TC4/
Ti–B–W/recrystallization scientific owners.
