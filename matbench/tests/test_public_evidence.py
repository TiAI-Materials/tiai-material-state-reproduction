import copy
import json
from collections import Counter, defaultdict
from pathlib import Path
import unittest

from tiai_matbench.public_evidence import (
    EXPECTED_MODELS,
    PublicEvidenceError,
    analyze_compmat_manifest,
    exact_mcnemar_p,
    pairwise_agreement,
    validate_public_evidence,
)

ROOT = Path(__file__).resolve().parents[1]


def make_manifest():
    rows = []

    def add(campaign, model, task, guidance, trial, score, rerun=False):
        rows.append({
            "campaign": campaign,
            "model": model,
            "provider_route": "test",
            "task_or_chain": task,
            "guidance": guidance,
            "trial": trial,
            "attempt_id": f"{campaign}/{model}/{task}/{guidance}/{trial}",
            "session_id": None,
            "host": "test",
            "score": score,
            "rerun_after_infrastructure_failure": rerun,
            "record_path": f"{campaign}/{model}/{task}/{guidance}/{trial}",
        })

    full_scores = {
        EXPECTED_MODELS[0]: (1, 0),
        EXPECTED_MODELS[1]: (1, 1),
        EXPECTED_MODELS[2]: (1, 1),
    }
    reduced_scores = {
        EXPECTED_MODELS[0]: (0, 0),
        EXPECTED_MODELS[1]: (1, 0),
        EXPECTED_MODELS[2]: (1, 1),
    }
    for model in EXPECTED_MODELS:
        for task, score in zip(("T1", "T2"), full_scores[model]):
            add("full94", model, task, "full", 1, score)
        for task, score in zip(("T1", "T2"), reduced_scores[model]):
            add("reduced52", model, task, "reduced", 1, score)
        for task, scores in {
            "R1": (1, 1),
            "R2": (1, 0) if model == EXPECTED_MODELS[0] else (1, 1),
        }.items():
            for trial, score in enumerate(scores, start=1):
                add("repeat20x5", model, task, "full", trial, score)
        for guidance in ("LG", "LA"):
            for chain in ("C01", "C02"):
                scores = (1, 1)
                if model == EXPECTED_MODELS[0] and guidance == "LA" and chain == "C02":
                    scores = (0, 0)
                for trial, score in enumerate(scores, start=1):
                    add("workflow", model, chain, guidance, trial, score)

    counts = defaultdict(lambda: defaultdict(int))
    passes = defaultdict(lambda: defaultdict(int))
    reruns = Counter()
    for row in rows:
        counts[row["campaign"]][row["model"]] += 1
        passes[row["campaign"]][row["model"]] += row["score"]
        if row["rerun_after_infrastructure_failure"]:
            reruns[f"{row['campaign']}/{row['model']}"] += 1
    return {
        "summary": {
            "total": len(rows),
            "counts": {key: dict(value) for key, value in counts.items()},
            "passes": {key: dict(value) for key, value in passes.items()},
            "reruns_after_infrastructure_failure": dict(reruns),
        },
        "rows": rows,
    }


class PublicEvidenceTests(unittest.TestCase):
    def test_exact_statistics_helpers(self):
        self.assertEqual(exact_mcnemar_p(2, 2), 1.0)
        self.assertAlmostEqual(exact_mcnemar_p(5, 1), 0.21875)
        self.assertEqual(pairwise_agreement(5, 5), 1.0)
        self.assertEqual(pairwise_agreement(2, 5), 0.4)

    def test_synthetic_manifest_is_analyzed_without_outcome_selection(self):
        report = analyze_compmat_manifest(make_manifest())
        self.assertEqual(report["guidance_paired"]["task_count"], 2)
        self.assertEqual(report["repeatability"]["task_count"], 2)
        self.assertEqual(report["workflow"]["workflow_count"], 2)
        weak = report["guidance_paired"]["models"][EXPECTED_MODELS[0]]
        self.assertEqual(weak["full_passes"], 1)
        self.assertEqual(weak["reduced_passes"], 0)
        self.assertEqual(
            report["repeatability"]["models"][EXPECTED_MODELS[0]]["mixed_outcome_tasks"],
            1,
        )

    def test_summary_tampering_is_rejected(self):
        manifest = make_manifest()
        manifest["summary"]["total"] += 1
        with self.assertRaises(PublicEvidenceError):
            analyze_compmat_manifest(manifest)

    def test_duplicate_record_path_is_rejected(self):
        manifest = make_manifest()
        manifest["rows"][1]["record_path"] = manifest["rows"][0]["record_path"]
        with self.assertRaises(PublicEvidenceError):
            analyze_compmat_manifest(manifest)

    def test_frozen_public_evidence_validates(self):
        report = json.loads(
            (ROOT / "baselines" / "compmat_public_evidence_v0.8.json").read_text(
                encoding="utf-8"
            )
        )
        result = validate_public_evidence(report)
        self.assertEqual(result["status"], "PASSED")
        self.assertEqual(result["attempts"], 976)
        self.assertEqual(result["matched_attempts"], 756)

    def test_frozen_evidence_preserves_stability_and_long_horizon_findings(self):
        report = json.loads(
            (ROOT / "baselines" / "compmat_public_evidence_v0.8.json").read_text(
                encoding="utf-8"
            )
        )
        repeat = report["repeatability"]["models"]
        self.assertEqual(repeat["deepseek_v4_1_flash"]["mixed_outcome_tasks"], 11)
        self.assertEqual(repeat["gemini_3_8_flash"]["mixed_outcome_tasks"], 3)
        self.assertEqual(repeat["gpt_5_6_sol"]["mixed_outcome_tasks"], 2)
        workflow = report["workflow"]["workflow_diagnostics"]
        self.assertEqual(workflow["C03"]["LG_passes_of_9"], 6)
        self.assertEqual(workflow["C03"]["LA_passes_of_9"], 0)
        self.assertEqual(workflow["C05"]["LA_passes_of_9"], 9)

    def test_changed_source_identity_is_rejected(self):
        report = json.loads(
            (ROOT / "baselines" / "compmat_public_evidence_v0.8.json").read_text(
                encoding="utf-8"
            )
        )
        tampered = copy.deepcopy(report)
        tampered["source"]["manifest_blob_sha"] = "0" * 40
        with self.assertRaises(PublicEvidenceError):
            validate_public_evidence(tampered)


if __name__ == "__main__":
    unittest.main()
