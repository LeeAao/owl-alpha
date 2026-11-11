"""Tests for tools/owl.py. Run from the repo root: python -m unittest discover tests"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "tools" / "owl.py"

FIELDS = [
    {"key": "hours", "label": "Работа", "type": "number"},
    {"key": "did", "label": "Что сделал", "type": "text"},
    {"key": "energy", "label": "Энергия", "type": "scale"},
    {"key": "anxiety", "label": "Тревога", "type": "scale", "min": 1, "max": 5},
]


class OwlTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = dict(os.environ, OWL_DATA=self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def run_owl(self, *args, data=None, today="2026-11-12"):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT)] + list(args) + ["--today", today],
            input=json.dumps(data, ensure_ascii=False).encode("utf-8") if data is not None else b"",
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=self.env,
        )
        out = proc.stdout.decode("utf-8")
        return proc.returncode, (json.loads(out) if proc.returncode == 0 else proc.stderr.decode("utf-8"))

    def ok(self, *args, **kwargs):
        code, result = self.run_owl(*args, **kwargs)
        self.assertEqual(code, 0, result)
        return result

    def fails(self, *args, **kwargs):
        code, result = self.run_owl(*args, **kwargs)
        self.assertEqual(code, 1)
        return result

    def setup_profile(self, done=True):
        return self.ok("profile-set", data={
            "name": "Тест", "language": "ru", "fields": FIELDS,
            "rules": ["Стоп в 22:00"], "onboarding": {"done": done, "next": "week"},
        })

    def test_fresh_install_suggests_setup(self):
        status = self.ok("status")
        self.assertEqual(status["suggested_mode"], "setup")
        self.assertFalse(status["has_intake_notes"])
        self.assertIsNone(status["last_checkin"])

    def test_modes_follow_setup_and_plan(self):
        self.setup_profile(done=False)
        self.assertEqual(self.ok("status")["setup_next_step"], "week")
        self.ok("profile-set", data={"onboarding": {"done": True}})
        status = self.ok("status")
        self.assertEqual(status["suggested_mode"], "weekly")
        self.assertEqual(status["setup_next_step"], "week")  # nested keys merge, not replace
        self.ok("week-set", data={"capacity_hours": 35, "main": {"name": "Лендинг", "hours": 20}})
        self.assertEqual(self.ok("status")["suggested_mode"], "daily")

    def test_profile_rejects_unknown_key_and_bad_field(self):
        self.assertIn("unknown profile key", self.fails("profile-set", data={"colour": "red"}))
        self.assertIn("Allowed types", self.fails("profile-set", data={"fields": [{"key": "x", "type": "stars"}]}))
        self.assertIn("used twice", self.fails("profile-set", data={"fields": [{"key": "x"}, {"key": "x"}]}))

    def test_profile_null_removes_key(self):
        self.setup_profile()
        self.ok("profile-set", data={"rules": None})
        self.assertNotIn("rules", self.ok("profile"))

    def test_checkin_saves_reports_missing_and_keeps_russian(self):
        self.setup_profile()
        result = self.ok("checkin", data={"values": {"hours": 9, "energy": 2, "did": "весь день аналитика"}})
        self.assertEqual(result["saved"], "2026-11-12")
        self.assertEqual(result["weekday"], "thursday")
        self.assertEqual(result["missing"], ["anxiety"])
        self.assertTrue(result["new_day"])
        raw = (Path(self.temp.name) / "days.json").read_text(encoding="utf-8")
        self.assertIn("весь день аналитика", raw)

    def test_checkin_correction_keeps_old_value(self):
        self.setup_profile()
        self.ok("checkin", data={"values": {"hours": 8}})
        result = self.ok("checkin", data={"values": {"hours": 6, "anxiety": 4}})
        self.assertEqual(result["corrected"], ["hours"])
        self.assertFalse(result["new_day"])
        self.assertEqual(result["values"], {"hours": 6, "anxiety": 4})
        days = json.loads((Path(self.temp.name) / "days.json").read_text(encoding="utf-8"))
        self.assertEqual(days["2026-11-12"]["history"][0]["was"], 8)

    def test_checkin_errors_are_plain(self):
        self.assertIn("no check-in fields", self.fails("checkin", data={"values": {"hours": 1}}))
        self.setup_profile()
        message = self.fails("checkin", data={"values": {"work": 5}})
        self.assertIn("unknown check-in field: work", message)
        self.assertIn("hours, did, energy, anxiety", message)
        self.assertIn("from 1 to 5", self.fails("checkin", data={"values": {"energy": 7}}))
        self.assertIn("future", self.fails("checkin", data={"date": "2026-11-13", "values": {"hours": 1}}))
        self.assertIn("needs a JSON object", self.fails("checkin"))

    def test_checkin_for_earlier_day(self):
        self.setup_profile()
        self.assertEqual(self.ok("checkin", data={"date": "2026-11-10", "values": {"hours": 4}})["saved"], "2026-11-10")

    def test_week_plan_needs_main_and_keeps_earlier_versions(self):
        self.assertIn("main focus", self.fails("week-set", data={"capacity_hours": 30}))
        self.ok("week-set", data={"capacity_hours": 35, "main": {"name": "A", "hours": 20}, "second": {"name": "B"}})
        changed = self.ok("week-set", data={"main": {"name": "A", "hours": 12}})
        self.assertTrue(changed["changed_existing_plan"])
        self.assertEqual(changed["plan"]["capacity_hours"], 35)  # merged, not replaced
        week = self.ok("week")
        self.assertEqual(week["week"], "2026-W46")
        self.assertEqual(week["revisions"][0]["plan"]["main"]["hours"], 20)
        replaced = self.ok("week-set", "--replace", data={"main": {"name": "C"}})
        self.assertNotIn("second", replaced["plan"])

    def test_week_other_week(self):
        self.ok("week-set", "--week", "2026-W47", data={"main": {"name": "A"}})
        self.assertIsNone(self.ok("week")["plan"])
        self.assertEqual(self.ok("week", "--week", "2026-W47")["plan"]["main"]["name"], "A")
        self.assertIn("not a week", self.fails("week", "--week", "next"))

    def test_view_totals_unknown_days_and_usual(self):
        self.setup_profile()
        self.ok("week-set", data={"capacity_hours": 35, "main": {"name": "A", "hours": 20}})
        for day, hours, energy in (("2026-11-09", 8, 4), ("2026-11-10", 9, 4), ("2026-11-12", 9, 2)):
            self.ok("checkin", data={"date": day, "values": {"hours": hours, "energy": energy}})
        self.ok("checkin", data={"date": "2026-11-05", "values": {"hours": 5}})
        view = self.ok("view")
        this_week = view["this_week"]
        self.assertEqual(this_week["totals"]["hours"], {"sum": 26, "days_counted": 3})
        statuses = [row["status"] for row in this_week["days"]]
        self.assertEqual(statuses, ["checked_in", "checked_in", "unknown", "checked_in", "future", "future", "future"])
        self.assertEqual(view["last_week"]["totals"]["hours"]["sum"], 5)
        self.assertIsNone(view["last_week"]["plan"])
        self.assertEqual(view["usual"]["energy"]["median"], 4)
        self.assertEqual(view["usual"]["hours"]["days_counted"], 4)
        self.assertNotIn("anxiety", view["usual"])  # no data, so no "usual"
        self.assertEqual(len(view["recent_days"]), 14)

    def test_notes(self):
        self.assertIn("one of", self.fails("note-add", data={"kind": "idea", "text": "x"}))
        first = self.ok("note-add", data={"kind": "wish", "text": "забирать план из блокнота"})["saved"]
        self.ok("note-add", data={"kind": "question", "text": "что мешает стопу в 22?"})
        self.assertEqual(first["id"], 1)
        self.ok("note-close", data={"id": 2, "outcome": "отчёт горел"})
        view = self.ok("view")
        self.assertEqual([note["id"] for note in view["open_notes"]], [1])
        self.assertEqual(view["recently_closed_notes"][0]["outcome"], "отчёт горел")
        self.assertIn("no note", self.fails("note-close", data={"id": 9}))

    def test_damaged_file_is_reported_not_overwritten(self):
        path = Path(self.temp.name) / "profile.json"
        path.write_text("{broken", encoding="utf-8")
        self.assertIn("damaged", self.fails("profile-set", data={"name": "x"}))
        self.assertEqual(path.read_text(encoding="utf-8"), "{broken")


if __name__ == "__main__":
    unittest.main()
