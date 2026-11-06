import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tools import audit_plan, night_submit, smart_adaptive_night, summarize_hybrid_stats
from tools import test_format_limits


def rec(total, tag="test-hybrid-x", valid=True, note=""):
    return {
        "tag": tag,
        "note": note,
        "total_seconds": total,
        "downloads": {f"{i}.bin": total / 6 for i in range(1, 7)},
        "valid": valid,
        "config": {str(i): "origin:" for i in range(1, 7)},
    }


class StatsTests(unittest.TestCase):
    def test_valid_and_load_filter(self):
        records = [
            rec(120, tag="test-hybrid-x-r1"),
            rec(122, tag="test-hybrid-x-r2"),
            rec(999, tag="test-hybrid-x-r3", valid=False),
            rec(999, tag="load-test-hybrid-x"),
        ]
        groups, invalid, contaminated = summarize_hybrid_stats.group_records(records)
        self.assertEqual(invalid, 1)
        self.assertEqual(contaminated, 1)
        self.assertEqual(len(groups["test-hybrid-x"]), 2)

    def test_describe_and_spike_flag(self):
        stats = summarize_hybrid_stats.describe([100.0, 120.0, 140.0])
        self.assertEqual(stats["n"], 3)
        self.assertAlmostEqual(stats["mean"], 120.0)
        self.assertAlmostEqual(stats["std"], 20.0)
        self.assertGreater(stats["cv"], 0.05)

        row = summarize_hybrid_stats.row_for("test-hybrid-x", [rec(100), rec(120), rec(140)], 3, 0.05)
        self.assertIn("HIGH_CV(16.7%)", row["flags"])
        self.assertIn("MIN_FAR_BELOW_MEAN", row["flags"])
        self.assertNotIn("LOW_N", ";".join(row["flags"]))

    def test_stable_config_has_no_flags(self):
        row = summarize_hybrid_stats.row_for("test-hybrid-x", [rec(118), rec(120), rec(122)], 3, 0.05)
        self.assertEqual(row["flags"], [])

    def test_render_states_min_is_not_official(self):
        text = summarize_hybrid_stats.render(
            [summarize_hybrid_stats.row_for("test-hybrid-x", [rec(118), rec(120), rec(122)], 3, 0.05)],
            3, 0, 0, 3, 0.05,
        )
        self.assertIn("不是官方预期", text)
        self.assertIn("按均值", text)


class AuditPlanTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.results = Path(self.tmp.name) / "results.jsonl"

    def write_results(self, records):
        self.results.write_text(
            "\n".join(json.dumps(item) for item in records) + "\n", encoding="utf-8"
        )

    def test_signature_matches_all_and_partial(self):
        plan_item = {"tag": "a", "all": ["origin", {}]}
        result = rec(120)
        self.assertEqual(audit_plan.plan_signature(plan_item), audit_plan.result_signature(result))

        partial = {"tag": "b", "configs": {"6": ["origin", {}]}}
        partial_result = rec(120)
        for slot in range(1, 6):
            partial_result["config"][str(slot)] = "(inherit/default)"
        self.assertEqual(audit_plan.plan_signature(partial), audit_plan.result_signature(partial_result))

    def test_flags_low_sample_variance_spike_and_language(self):
        self.write_results([rec(100), rec(120), rec(140), rec(999, valid=False), rec(999, tag="load-x")])
        plan = [{"tag": "a", "all": ["origin", {}], "note": "min-of-N 极值红利"}]
        findings = audit_plan.audit(plan, [json.loads(line) for line in self.results.read_text("utf-8").splitlines()], 3, 0.05)
        flags = ";".join(findings[0]["flags"])
        self.assertIn("HIGH_CV", flags)
        self.assertIn("MIN_FAR_BELOW_MEAN", flags)
        self.assertIn("OVERFITTING_LANGUAGE", flags)

    def test_clean_plan_has_no_flags(self):
        records = [rec(118), rec(120), rec(122)]
        plan = [{"tag": "a", "all": ["origin", {}]}]
        findings = audit_plan.audit(plan, records, 3, 0.05)
        self.assertEqual(findings[0]["flags"], [])

    def test_missing_local_sample(self):
        plan = [{"tag": "a", "all": ["token_bucket", {"tokens": 1}]}]
        findings = audit_plan.audit(plan, [], 3, 0.05)
        self.assertIn("NO_LOCAL_SAMPLE", findings[0]["flags"])


class SchedulerTests(unittest.TestCase):
    def test_attempts_since_filters_and_sorts(self):
        since = dt.datetime(2026, 11, 7, 0, 5, 0)
        attempts = [
            {"submitted_at": "2026-11-07 00:10:00", "download_seconds": "120"},
            {"submitted_at": "2026-11-07 00:01:00", "download_seconds": "130"},
            {"submitted_at": "2026-11-07 00:06:00", "download_seconds": "125"},
            {"submitted_at": "bad", "download_seconds": "1"},
        ]
        selected = smart_adaptive_night.attempts_since(attempts, since)
        self.assertEqual([item["download_seconds"] for item in selected], ["125", "120"])

    def test_parse_and_download_seconds(self):
        self.assertIsNone(smart_adaptive_night.parse_attempt_time({"submitted_at": "bad"}))
        self.assertIsNone(smart_adaptive_night.download_seconds({"download_seconds": "bad"}))
        self.assertEqual(
            smart_adaptive_night.download_seconds({"download_seconds": "116.5"}), 116.5
        )

    def test_choose_branch_does_not_blindly_go_bypass_when_both_slow(self):
        args = SimpleNamespace(bypass_max_s2=132.0, bypass_margin=2.0, bypass_floor=138.0)
        self.assertEqual(smart_adaptive_night.choose_branch(150, 149, args)[0], "Branch_B_Fallback")
        self.assertEqual(smart_adaptive_night.choose_branch(150, 147, args)[0], "Branch_B_Fallback")
        self.assertEqual(smart_adaptive_night.choose_branch(140, 131, args)[0], "Branch_A_Bypass")

    def test_today_used_counts_failed_but_not_dry_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "submissions.jsonl"
            today = dt.date.today().isoformat()
            path.write_text("\n".join([
                json.dumps({"date": today, "status": "submitted"}),
                json.dumps({"date": today, "status": "failed"}),
                json.dumps({"date": today, "status": "dry-run"}),
                json.dumps({"date": "2000-01-01", "status": "submitted"}),
            ]) + "\n", encoding="utf-8")
            with patch.object(smart_adaptive_night, "SUBMISSIONS", path):
                self.assertEqual(smart_adaptive_night.today_used(), 2)


class NightSubmitTests(unittest.TestCase):
    def test_plan_tags_and_submitted_tags_today(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = root / "plan.json"
            plan.write_text(json.dumps([
                {"tag": "a", "all": ["origin", {}]},
                {"tag": "b", "all": ["origin", {}]},
            ]), encoding="utf-8")
            self.assertEqual(night_submit.plan_tags(plan), ["a", "b"])

            subs = root / "submissions.jsonl"
            today = dt.date.today().isoformat()
            subs.write_text("\n".join([
                json.dumps({"date": today, "status": "submitted", "note": "a | note"}),
                json.dumps({"date": today, "status": "dry-run", "note": "b | note"}),
            ]) + "\n", encoding="utf-8")
            with patch.object(night_submit, "SUBMISSIONS", subs):
                self.assertEqual(night_submit.submitted_tags_today(), {"a"})


class FormatTests(unittest.TestCase):
    def test_render_pacer_matches_production(self):
        text = test_format_limits.render_pacer(2, "token_bucket", "tokens=1")
        self.assertEqual(text.count("\n"), 2)
        self.assertFalse(text.endswith("\n"))
        self.assertEqual(text.splitlines()[0], "[timestamp:2]")

    def test_write_command_uses_printf(self):
        command = test_format_limits.write_command("token_bucket", "tokens=1")
        self.assertIn("printf '%s'", command)
        self.assertNotIn("echo", command)


if __name__ == "__main__":
    unittest.main()
