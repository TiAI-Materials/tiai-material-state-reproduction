# Native authority gate v0.10 — no scores from self-signed digests

Status: **evaluator security hardening, not a real Agent evaluation.**
The v0.8 protocol and v0.9's 192 registered slots remain unchanged.
Current true state without model/provider/input/verifier bindings remains
**0 dispatched / 192 blocked / zero TiAI verified effect estimates**.

## Why this is publication-critical

The original v0.9 PilotLedger accepts a `receipt_id -> SHA-256` index
provided separately from the agent ledger. This proves only content
consistency. An agent, or a compromised common controller, could produce
both the purported receipt and index without ever running the native
scorer. The previous structural audit also used the string
`ELIGIBLE_FOR_SEPARATE_STRATIFIED_ANALYSIS` after 192 such records.

This release makes the old `pilot_ledger audit` **structural only**: it
never promotes a set of submitted digest-index records into an empirical
system-effect estimate. No existing run, budget, task, mode, native
verifier, or v0.8 preregistration is changed.

## Independently attested audit

`python -m tiai_matbench.attested_pilot` requires:

- immutable protocol and plan identities, including `slot_set_digest`;
- the entire run ledger, all 192 slots including failures and omissions;
- an independent native verifier's receipt index, with native pass/fail;
- independent issuer sealed SHA-256 digests for each run ledger entry and
  each artifact hash map;
- a verifier-owned HMAC-SHA256 key and pinned `key_id` supplied **only
  in the auditor process**, never through the tested agent, agent tools,
  GitHub repository or provider logs.

The authority bundle fields are:
`schema`, `issuer_id`, `key_id`, `protocol_sha256`,
`slot_set_digest`, `native_receipt_index`, `run_ledger_sha256`,
`artifact_sha256_by_run`, and `hmac_sha256`. Its MAC covers the
canonical JSON of every field except `hmac_sha256`. The native
verifier must create the bundle from its independently observed
execution, never from an agent self-report.

Example audit command (not runnable without real independent inputs):

```bash
PYTHONPATH=matbench/src python -m tiai_matbench.attested_pilot \
  --protocol matbench/experiments/matched_goal_driven_protocol_v0.8.json \
  --plan pilot_plan.json --ledger pilot_runs.jsonl \
  --authority native_authority.json \
  --verifier-key-file /secure-verifier-only/hmac.key \
  --expected-key-id frozen-verifier-key-id \
  --output independent_audit.json
```

A valid MAC **only authenticates the bundle's issuer**. It does not
prove scientific truth if the issuer is compromised, nor verify actual
artifact bytes unless the isolated signer rehashes them from native
output. In particular, an HMAC cannot replace the CompMat fixed-rule
grader, the Hidden RealReplay oracle, physical safety evidence, or
human-expert adjudication. The signer must never be given to agents.

## Effect-eligibility gates

Even an authenticated bundle does not admit a system-effect estimate
unless all 192 preregistered runs are valid under the original structural
auditor and independent receipt index. A further completeness check
requires observed wall-time, input/output tokens, CPU/GPU usage and
monetary cost plus GDS, VWR, HLF and FCR per run. Missing data remain
explicitly reported. FRR can remain not applicable if no fault occurred,
and physical trajectory safety must not be inferred from a task pass.

After these gates, output says `matched_effect_analysis_eligible=true`,
not that the Goal-Driven mechanism has won. A separate stratum-wise,
task-level paired analysis with uncertainty and expert adjudication is
still mandatory. Test-generated signatures or fixtures are never actual
native benchmark runs.

## Deterministic tests

```bash
PYTHONPATH=matbench/src python -m unittest discover \
  -s matbench/tests -p test_attested_pilot.py -v
```

Ten synthetic/adversarial cases: valid partial, unsigned authority,
forged digest index, wrong key/key ID, absent key, modified telemetry,
modified artifacts, modified plan, missing cost and mock-complete 192-run
bundle. The last proves only evaluator logic; every key, receipt, model
and outcome in the fixture is synthetic.

This scope uses only Python's standard library on ordinary CPU. It does
not consume A100 hours or rerun Ti65/TC4/Ti–B–W/recrystallization owners.

## Real blockers

An authorized evaluator must still provision a genuinely independent
trust root and issuer, verified input assets for all twelve registered
tasks, the same real provider/model/tool/budget bindings across all
six arms, and native CompMat/RealReplay verifier execution. Until then
**0 authenticated real agent runs** exist. Never replace these
requirements with an internally signed mock bundle.
