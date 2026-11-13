# CompMat-Bench Federation Adapter v0.7

This release makes the materials-science row of FederationCore executable without rerunning expensive simulations.

## Native authority

The adapter consumes the upstream `trajectories/manifest.json`. Each published attempt remains a native fixed-rule pass or fail. The adapter verifies that every row reconciles exactly with the upstream campaign/model counts, pass counts and infrastructure-rerun summary. It does not reinterpret a failed scientific task as an infrastructure failure.

The admitted upstream identity is:

- repository: `cz2014/CompMat-Bench`;
- release: `v1.0.0`;
- commit: `03fec439ca9c9b1b14ea914896886b74d3e739bc`;
- manifest blob: `de6f82bc77a35b1a01d1d03a608c58e502e36516`;
- license: CC BY 4.0.

## Public aggregate reproduction

The frozen public snapshot contains 976 reported attempts and 771 native passes. Campaign pass rates are retained separately for full-guidance tasks, reduced-guidance tasks, repeated trials and complete workflows. Seventy-nine reported rows are replacements after infrastructure failure.

The adapter reports the rerun fraction but leaves infrastructure reliability unknown because the manifest does not include the excluded original failed-launch denominator.

## Deliberate unknowns

The upstream manifest does not by itself report trajectory safety, human intervention, cost, false-completion rate or per-artifact hashes. FederationCore therefore emits explicit evidence gaps and leaves those metrics null.

## Claim boundary

This adapter establishes an executable external materials result format and upgrades materials science to Federation `EXECUTABLE`. It does not constitute a new matched TiAI-AgentBench baseline. Publication-grade comparison still requires the same agents, budgets and intervention/recovery ledger across a frozen CompMat-Bench subset and TiAI Hidden RealReplayCore.

## Resource policy

No A100, PC128 scientific core or heavy mother-machine workload is required for manifest normalization. Expensive compute remains assigned to original scientific owners and enters LiveComputeCore only when native execution changes a scientific conclusion.
