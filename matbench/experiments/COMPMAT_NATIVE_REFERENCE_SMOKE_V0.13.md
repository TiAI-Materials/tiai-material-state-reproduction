# CompMat native grader reference smoke v0.13 — one bounded official self-test

**Scope:** one actual upstream fixed-rule grader, not a TiAI Agent run.
This is an incremental native-verifier readiness check for the unchanged six-arm
192-slot protocol. It inherits the official source lock v0.11 and signed-receipt
authority gate v0.10. All 192 Agent slots remain blocked.

## Direct native result on DESKTOP-B514PPT (2026-11-13 UTC)

Frozen single-step task:
`task_202603_007_step_znmgo-strain-composition-phase-map`.

Upstream repository: [cz2014/CompMat-Bench](https://github.com/cz2014/CompMat-Bench).
Pinned commit `03fec439ca9c9b1b14ea914896886b74d3e739bc`;
task tree `f261454f7a57999e50186a906da9c747d16c1066`.

To avoid repeatedly fetching a 517 MB archive, this preflight retrieved exactly
four *official* grader/reference blobs through GitHub's Git REST API, verified
each Git blob SHA-1 over actual bytes, and executed the unmodified grader on
the original upstream reference submission and on a separately copied
submission with one physical quantity deliberately corrupted.
The real native outcomes were **reference SCORE: 1** and **corrupted SCORE: 0**,
both with exit code 0. The actual stdout digests and four file identities are
saved in `COMPMAT_ZNMGO_NATIVE_REFERENCE_RECEIPT_V0.13.json`.
No reference answers or grader runtime were exposed to a tested Agent.

Reproduce this *source-only* check (requires GitHub API connectivity):

```bash
python matbench/tools/replay_compmat_znmgo_native_smoke.py --output /tmp/znmgo-native-smoke.json
```

The reusable script isolates source grader bytes in a temporary directory,
checks Git blob content identities, runs the official scorer and a negative
control, then removes its native reference files. This is a stronger
prerequisite than a source-path pin, but it does **not** verify the release
asset's staged simulation inputs or certify an independently signed production
grader. The separate static CI tests check receipt/schema continuity and
the deliberate refusal to change Agent readiness; they do not re-execute the
native grader offline.

## Exact blockers, not success claims

The official release publishes `compmat_bench_core.zip` at 516,859,324 bytes
and SHA-256 `6be09447536a8d3e23aa9e21e3cea3864380ad1a7c841fb9970930b008f067bb`.
The publisher's `CHECKSUMS.sha256` row was obtained and matched, but PC128's
release-asset transfer timed out without independently verifying the archive.
A second download using the official `gh` CLI was observed to transfer too
slowly for the bounded native preflight; its **own** process tree was stopped,
and its incomplete archive was discarded. A sparse Git clone also failed due
to slow transfer; the small Git REST blob route completed instead. These are
transport observations, not licensing or scientific-convergence failures.

Therefore **release core verified = false**, **full staged input SHA = unknown**,
**C07 licensed POTCAR = unverified**, **external model/provider/budget/verifier
authority = unbound**, **native Agent runs = 0/192**, **legitimate READY = 0/192**.
No upstream Oracle/reference SCORE is counted as TiAI performance. Do not
launch workflow C03/C07, disclose the hidden scorer to the tested Agent or
pool this source-only smoke with pilot outcomes.

This operation used only a small CPU-native scorer and public Git API bytes
on PC128; it did not consume A100, re-run materials simulations, change
mother-machine provider settings or touch active scientific owners.
