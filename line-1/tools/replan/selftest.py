#!/usr/bin/env python3
"""Offline checks of progress semantics, feasibility, and command line behavior."""
import copy
import json
from pathlib import Path
import random
import subprocess
import sys
import unittest

from replan import demo, replan, read_snapshot, _workplan


class ReplanTests(unittest.TestCase):
    def test_delayed_demo(self):
        result = replan(demo(), 2, 27)
        self.assertEqual(result["finish"], 26)
        self.assertEqual(result["remaining_minutes"], 17)
        self.assertEqual(result["slack"], 1)
        self.assertEqual([s["task"] for s in result["schedule"]],
                         ["implement", "verify", "write-handoff"])
        self.assertEqual(result["schedule"][0]["state"], "running")
        self.assertEqual(replan(demo(), 2, 25)["deadline_verdict"], "impossible_at_estimates")

    def test_margin_on_remaining_work_only(self):
        result = replan(demo(), 2, 27, 20)
        self.assertAlmostEqual(result["finish"], 29.4)
        self.assertEqual(result["elapsed_minutes"], 9)
        self.assertEqual(result["schedule"][0]["remaining_minutes"], 12)
        self.assertEqual(result["deadline_verdict"], "impossible_at_estimates")

    def test_done_all_and_expired_deadline(self):
        data = demo()
        data["completed"] = [row["id"] for row in data["tasks"]]
        data["running"] = []
        result = replan(data, 2, 9)
        self.assertEqual(result["schedule"], [])
        self.assertEqual(result["finish"], 9)
        self.assertEqual(result["lower_bound_remaining"], 0)
        self.assertTrue(result["fits_budget"])
        self.assertFalse(replan(data, 2, 8)["fits_budget"])

    def test_no_progress_matches_predecessor(self):
        data = {**_workplan.demo(), "elapsed_minutes": 0}
        for workers in range(1, 5):
            result = replan(data, workers)
            old = _workplan.plan({"tasks": data["tasks"]}, workers)
            self.assertEqual(result["finish"], old["finish"])
            actual = [{key: row[key] for key in ("task", "worker", "start", "finish")}
                      for row in result["schedule"]]
            self.assertEqual(actual, sorted(old["schedule"], key=lambda s: (s["start"], s["worker"], s["task"])))

    def test_running_workers_are_pinned(self):
        data = {"elapsed_minutes": 10, "tasks": [
            {"id": "active", "minutes": 2}, {"id": "ready", "minutes": 1},
            {"id": "child", "minutes": 1, "after": ["active"]}],
            "running": [{"task": "active", "worker": 2, "remaining_minutes": 7}]}
        result = replan(data, 2)
        by_id = {row["task"]: row for row in result["schedule"]}
        self.assertEqual(by_id["active"]["worker"], 2)
        self.assertEqual(by_id["active"]["finish"], 17)
        self.assertEqual(by_id["ready"]["worker"], 1)
        self.assertEqual(by_id["ready"]["start"], 10)
        self.assertEqual(by_id["child"]["start"], 17)

    def test_simultaneous_completions_release_all_dependencies(self):
        data = {"elapsed_minutes": 10, "tasks": [
            {"id": "a", "minutes": 1}, {"id": "b", "minutes": 1},
            {"id": "c", "minutes": 2, "after": ["a", "b"]}],
            "running": [{"task": n, "worker": w, "remaining_minutes": 3}
                        for n, w in [("a", 1), ("b", 2)]]}
        self.assertEqual(replan(data, 2)["finish"], 15)

    def test_inconsistent_progress(self):
        variants = [
            {"completed": ["implement"]}, {"completed": ["missing"]},
            {"completed": ["read-brief", "read-brief"]}, {"completed": "read-brief"},
            {"completed": [False]}, {"running": "implement"},
            {"running": [{"task": "read-brief", "worker": 1, "remaining_minutes": 1}]},
            {"running": [{"task": "verify", "worker": 1, "remaining_minutes": 1}]},
            {"running": [{"task": "missing", "worker": 1, "remaining_minutes": 1}]},
            {"running": [{"task": [], "worker": 1, "remaining_minutes": 1}]},
            {"running": [{"task": "implement", "worker": True, "remaining_minutes": 1}]},
            {"running": [{"task": "implement", "worker": 3, "remaining_minutes": 1}]},
            {"running": [{"task": "implement", "worker": 1, "remaining_minutes": 0}]},
            {"running": [{"task": "implement", "worker": 1, "remaining_minutes": -1}]},
            {"running": [{"task": "implement", "worker": 1, "remaining_minutes": 1, "command": "ignored"}]},
            {"elapsed_minutes": -1}, {"elapsed_minutes": True}, {"elapsed_minutes": float("inf")},
            {"elapsed_minutes": 10 ** 400}, {"extra": 1}]
        for update in variants:
            with self.subTest(update=update), self.assertRaises(ValueError):
                replan({**demo(), **update}, 2)
        for kwargs in [{"workers": True}, {"workers": 0}, {"workers": 65},
                       {"margin_percent": -1}, {"margin_percent": 1001},
                       {"margin_percent": float("nan")}, {"budget": -1}, {"budget": True}]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                replan(demo(), **kwargs)

    def test_repeated_active_and_worker(self):
        data = {"tasks": [{"id": "a", "minutes": 1}, {"id": "b", "minutes": 1}],
                "elapsed_minutes": 1}
        for names, workers in [(["a", "a"], [1, 2]), (["a", "b"], [1, 1])]:
            data["running"] = [{"task": n, "worker": w, "remaining_minutes": 1}
                               for n, w in zip(names, workers)]
            with self.assertRaises(ValueError):
                replan(data, 2)

    def test_complete_graph_still_validated(self):
        for tasks in [[{"id": "a", "minutes": 1, "after": ["a"]}],
                      [{"id": "a", "minutes": 1, "after": ["absent"]}],
                      [{"id": "a", "minutes": -1}]]:
            with self.assertRaises(ValueError):
                replan({"tasks": tasks, "elapsed_minutes": 1, "completed": ["a"]})

    def test_timestamp_precision_rejected(self):
        with self.assertRaises(ValueError):
            replan({"tasks": [{"id": "a", "minutes": 1}], "elapsed_minutes": 1e30})

    def test_heuristic_miss_is_not_proof(self):
        data = {"elapsed_minutes": 4, "tasks": [
            {"id": str(i), "minutes": minutes} for i, minutes in enumerate([3, 3, 2, 2, 2])]}
        result = replan(data, 2, 10)
        # Greedy dispatch takes 7 minutes. A feasible 6-minute arrangement exists:
        # worker 1 runs 3+3 and worker 2 runs 2+2+2.
        self.assertEqual(result["finish"], 11)
        self.assertEqual(result["earliest_possible_finish"], 10)
        self.assertEqual(result["deadline_verdict"], "heuristic_misses_not_proven_impossible")

    def test_input_not_mutated(self):
        data = demo()
        saved = copy.deepcopy(data)
        replan(data, 2, 27, 20)
        self.assertEqual(data, saved)

    def test_300_progress_snapshots(self):
        rng = random.Random(73722)
        for _ in range(300):
            tasks = [{"id": str(i), "minutes": rng.randint(1, 9),
                      "after": [str(j) for j in range(i) if rng.random() < .18]}
                     for i in range(rng.randint(1, 25))]
            workers = rng.randint(1, 5)
            original = _workplan.plan({"tasks": tasks}, workers)
            elapsed = rng.randint(0, int(original["finish"]))
            done = [r["task"] for r in original["schedule"] if r["finish"] <= elapsed]
            running = [{"task": r["task"], "worker": r["worker"],
                        "remaining_minutes": rng.randint(1, 12)} for r in original["schedule"]
                       if r["start"] <= elapsed < r["finish"]]
            data = {"tasks": tasks, "completed": done, "running": running, "elapsed_minutes": elapsed}
            result = replan(data, workers)
            reverse = {**data, "tasks": list(reversed(tasks)), "completed": list(reversed(done)),
                       "running": list(reversed(running))}
            self.assertEqual(result, replan(reverse, workers))
            by_id = {r["task"]: r for r in result["schedule"]}
            self.assertEqual(set(by_id), {t["id"] for t in tasks} - set(done))
            active = {r["task"]: r for r in running}
            for task in tasks:
                if task["id"] in done:
                    continue
                slot = by_id[task["id"]]
                self.assertGreaterEqual(slot["start"], elapsed)
                self.assertEqual(slot["finish"] - slot["start"],
                                 active.get(task["id"], {}).get("remaining_minutes", task["minutes"]))
                for dep in task["after"]:
                    if dep not in done:
                        self.assertLessEqual(by_id[dep]["finish"], slot["start"])
                if task["id"] in active:
                    self.assertEqual(slot["worker"], active[task["id"]]["worker"])
                    self.assertEqual(slot["start"], elapsed)
            for worker in range(1, workers + 1):
                slots = sorted((s for s in by_id.values() if s["worker"] == worker), key=lambda s: s["start"])
                self.assertTrue(all(a["finish"] <= b["start"] for a, b in zip(slots, slots[1:])))
            self.assertLessEqual(result["earliest_possible_finish"], result["finish"] + 1e-8)

    def test_file_and_cli_validation(self):
        scratch = Path("test/scratch/replan")
        scratch.mkdir(parents=True, exist_ok=True)
        file = scratch / "input.json"
        file.write_text('{"tasks": [], "tasks": [], "elapsed_minutes": 0}')
        with self.assertRaisesRegex(ValueError, "duplicate JSON"):
            read_snapshot(file)
        file.write_bytes(b" " * 100001)
        with self.assertRaisesRegex(ValueError, "100 KB"):
            read_snapshot(file)
        # Reject before opening; this test never reads outside the workspace.
        with self.assertRaisesRegex(ValueError, "workspace"):
            read_snapshot(Path.cwd().parent / "not-read.json")
        script = str(Path(__file__).with_name("replan.py"))
        for budget, code in [(27, 0), (25, 2)]:
            process = subprocess.run([sys.executable, "-B", script, "--demo", "--budget", str(budget)],
                                     capture_output=True, text=True)
            self.assertEqual(process.returncode, code, process.stderr)
            self.assertEqual(json.loads(process.stdout)["finish"], 26)
        file.write_text("{")
        process = subprocess.run([sys.executable, "-B", script, "--input", str(file)],
                                 capture_output=True, text=True)
        self.assertEqual(process.returncode, 1)
        self.assertTrue(process.stderr.startswith("replan:"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
