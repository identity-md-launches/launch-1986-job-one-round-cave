#!/usr/bin/env python3
"""Replan a bounded job from a progress snapshot; never execute its tasks."""
import argparse
import heapq
import importlib.util
import json
import math
from pathlib import Path
import sys


# Reuse the predecessor's graph validation without changing its CLI or source.
_spec = importlib.util.spec_from_file_location(
    "pepeolithic_workplan", Path(__file__).resolve().parent.parent / "workplan" / "workplan.py")
_workplan = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_workplan)


def number(value, label, zero=False):
    try:
        valid = (type(value) in (int, float) and math.isfinite(value)
                 and (value >= 0 if zero else value > 0))
    except OverflowError:
        valid = False
    if not valid:
        raise ValueError(label + " must be a finite " + ("nonnegative" if zero else "positive") + " number")
    return value


def replan(data, workers=1, budget=None, margin_percent=0):
    """Times are minutes since job start. Budget is the original absolute deadline."""
    if not isinstance(data, dict) or not {"tasks", "elapsed_minutes"} <= data.keys():
        raise ValueError("snapshot needs tasks and elapsed_minutes")
    if data.keys() - {"tasks", "elapsed_minutes", "completed", "running"}:
        raise ValueError("unknown snapshot field")
    if type(workers) is not int or not 1 <= workers <= 64:
        raise ValueError("workers must be an integer from 1 to 64")
    elapsed = number(data["elapsed_minutes"], "elapsed_minutes", zero=True)
    margin = number(margin_percent, "margin_percent", zero=True)
    if margin > 1000:
        raise ValueError("margin_percent must not exceed 1000")
    if budget is not None:
        number(budget, "budget", zero=True)
    original = {"tasks": data["tasks"]}
    # Validate all tasks, including completed ones, before pruning the graph.
    _workplan.plan(original, workers)
    tasks = {row["id"]: row for row in original["tasks"]}
    completed = data.get("completed", [])
    if (not isinstance(completed, list) or any(not isinstance(x, str) for x in completed)
            or len(set(completed)) != len(completed)):
        raise ValueError("completed must be a list of distinct task ids")
    done = set(completed)
    if done - tasks.keys():
        raise ValueError("unknown completed task")
    for task in done:
        if set(tasks[task].get("after", [])) - done:
            raise ValueError("completed task has unfinished prerequisites: " + task)
    rows = data.get("running", [])
    if not isinstance(rows, list) or len(rows) > workers:
        raise ValueError("running must be an array with at most one task per worker")
    active, occupied = {}, set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"task", "worker", "remaining_minutes"}:
            raise ValueError("running entries need task, worker, remaining_minutes")
        name, worker = row["task"], row["worker"]
        if not isinstance(name, str) or name not in tasks:
            raise ValueError("unknown running task")
        if name in done or name in active:
            raise ValueError("task is completed or repeated in running: " + name)
        if type(worker) is not int or not 1 <= worker <= workers or worker in occupied:
            raise ValueError("running workers must be distinct integers within the worker count")
        if set(tasks[name].get("after", [])) - done:
            raise ValueError("running task has unfinished prerequisites: " + name)
        active[name] = (worker, number(row["remaining_minutes"], "remaining_minutes"))
        occupied.add(worker)
    pending = sorted(tasks.keys() - done)
    factor = 1 + margin / 100
    durations = {n: number((active[n][1] if n in active else tasks[n]["minutes"]) * factor,
                           "adjusted duration") for n in pending}
    children = {n: [] for n in pending}
    indegree = {n: len(set(tasks[n].get("after", [])) - done) for n in pending}
    for n in pending:
        for dep in tasks[n].get("after", []):
            if dep not in done:
                children[dep].append(n)
    # Reuse the original planner for critical paths and a valid relaxed lower bound.
    residual = {"tasks": [{"id": n, "minutes": durations[n],
                           "after": sorted(set(tasks[n].get("after", [])) - done)} for n in pending]}
    baseline = _workplan.plan(residual, workers) if pending else None
    order, indeg = [], dict(indegree)
    queue = [n for n in pending if indeg[n] == 0]
    heapq.heapify(queue)
    while queue:
        n = heapq.heappop(queue)
        order.append(n)
        for child in children[n]:
            indeg[child] -= 1
            if indeg[child] == 0:
                heapq.heappush(queue, child)
    tail = {}
    for n in reversed(order):
        tail[n] = durations[n] + max((tail[c] for c in children[n]), default=0)
    ready = [(-tail[n], n) for n in pending if indegree[n] == 0 and n not in active]
    heapq.heapify(ready)
    free = [w for w in range(1, workers + 1) if w not in occupied]
    heapq.heapify(free)
    events, schedule = [], []

    def start(name, worker, now, state):
        finish = number(now + durations[name], "finish")
        if finish <= now:
            raise ValueError("duration is too small for the timestamp's numeric precision")
        heapq.heappush(events, (finish, name, worker))
        schedule.append({"task": name, "worker": worker, "start": now, "finish": finish,
                         "state": state, "remaining_minutes": durations[name]})

    now = elapsed
    for name in sorted(active):
        start(name, active[name][0], now, "running")
    while ready or events:
        while ready and free:
            _, name = heapq.heappop(ready)
            start(name, heapq.heappop(free), now, "pending")
        if events:
            now = events[0][0]
            while events and events[0][0] == now:
                _, name, worker = heapq.heappop(events)
                heapq.heappush(free, worker)
                for child in children[name]:
                    indegree[child] -= 1
                    if indegree[child] == 0:
                        heapq.heappush(ready, (-tail[child], child))
    lower = baseline["lower_bound"] if baseline else 0
    earliest = number(elapsed + lower, "earliest possible finish", zero=True)
    fits = None if budget is None else now <= budget
    verdict = ("not_requested" if budget is None else "fits" if fits else
               "impossible_at_estimates" if earliest > budget else "heuristic_misses_not_proven_impossible")
    return {
        "units": "minutes", "elapsed_minutes": elapsed, "workers": workers,
        "budget": budget, "remaining_budget": None if budget is None else budget - elapsed,
        "margin_percent": margin, "completed": sorted(done),
        "schedule": sorted(schedule, key=lambda s: (s["start"], s["worker"], s["task"])),
        "finish": now, "remaining_minutes": now - elapsed,
        "lower_bound_remaining": lower, "earliest_possible_finish": earliest,
        "critical_path": baseline["critical_path"] if baseline else [],
        "fits_budget": fits, "deadline_verdict": verdict,
        "slack": None if budget is None else budget - now,
        "method": "nonpreemptive longest downstream first; running tasks pinned to their workers",
    }


def demo():
    return {"tasks": _workplan.demo()["tasks"], "elapsed_minutes": 9,
            "completed": ["read-brief", "prepare-fixtures"],
            "running": [{"task": "implement", "worker": 1, "remaining_minutes": 10}]}


def read_snapshot(filename):
    root = Path.cwd().resolve()
    path = Path(filename).resolve()
    if not path.is_relative_to(root):
        raise ValueError("input must be inside the current workspace")
    if not path.is_file():
        raise ValueError("input must be an ordinary JSON file")
    with path.open("rb") as handle:
        raw = handle.read(100001)
    if len(raw) > 100000:
        raise ValueError("input exceeds 100 KB")

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key: " + key)
            result[key] = value
        return result

    return json.loads(raw, object_pairs_hook=pairs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", help="workspace-local progress JSON, at most 100 KB")
    source.add_argument("--demo", action="store_true")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--budget", type=float, help="absolute deadline measured from job start")
    parser.add_argument("--margin-percent", type=float, default=0,
                        help="inflate all remaining estimates by 0 to 1000 percent")
    args = parser.parse_args()
    try:
        result = replan(demo() if args.demo else read_snapshot(args.input),
                        args.workers, args.budget, args.margin_percent)
        print(json.dumps(result, indent=2, allow_nan=False))
        return 2 if result["fits_budget"] is False else 0
    except (ValueError, OSError, RecursionError, OverflowError) as exc:
        print("replan: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
