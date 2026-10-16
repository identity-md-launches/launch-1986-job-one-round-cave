# Replan

Continue a partially finished job without scheduling completed tasks again or
moving a running task onto another worker. This extends Workplan's offline
dependency planning with progress snapshots and an optional uncertainty margin.
Python 3.9+; standard library only. It never executes task labels, connects to a
network, reads environment variables, or handles payments or wallets.

Run this from the repository root:

```sh
python3 -B line-1/tools/replan/replan.py --demo --workers 2 --budget 27
```

Observed result: at minute 9, reading and fixture preparation are complete,
implementation is still running on worker 1 with 10 minutes remaining, and
verification plus handoff take another 7. The remaining schedule finishes at
minute **26**, leaving **1 minute** before the deadline. Workplan's original
estimate was minute 22: the delay is reflected rather than discarded. These are
illustrative estimates, not measurements of a real job's runtime.

For your own snapshot:

```sh
python3 -B line-1/tools/replan/replan.py --input line-1/tools/replan/example.json --workers 2 --budget 27 --margin-percent 20
```

That command deliberately exits **2**: inflating all remaining estimates by 20%
gives a finish of **29.4**, exceeding the 27-minute deadline by 2.4 minutes. No
margin is added to time already elapsed. Remove the margin to reproduce the
26-minute schedule.

## Snapshot format

```json
{
  "tasks": [
    {"id": "read", "minutes": 3},
    {"id": "build", "minutes": 12, "after": ["read"]},
    {"id": "verify", "minutes": 5, "after": ["build"]}
  ],
  "elapsed_minutes": 9,
  "completed": ["read"],
  "running": [{"task": "build", "worker": 1, "remaining_minutes": 10}]
}
```

- `tasks` uses the existing Workplan format: 1–500 tasks, unique ids, positive
  finite estimates, optional prerequisite ids. Keep completed tasks in the graph
  so their dependency history can be validated. Change `minutes` for a pending
  task when its estimate changes.
- `elapsed_minutes` is required, finite and nonnegative. All output start/finish
  times are absolute minutes since this job began.
- `completed` defaults to `[]`. Completed tasks must have completed prerequisites.
  It is a status assertion, not proof of when those tasks finished.
- `running` defaults to `[]`. A running task's prerequisites must be completed;
  its worker number is pinned, and its explicit positive `remaining_minutes`
  replaces its original estimate. Record tasks with zero remaining as completed.
- Everything else is pending. Workers are interchangeable, numbered 1 through
  `--workers` (1–64, default 2). All free workers are available at the snapshot.
- `--budget` is the **original absolute deadline**, not time remaining. Thus a
  deadline of 27 and an elapsed time of 9 leave 18 minutes. Zero and expired
  deadlines are accepted. Omit the option to schedule without a deadline.
- `--margin-percent` is 0–1000 (default 0), applied once to running remaining time
  and pending estimates. Supply fresh, uninflated estimates in each new snapshot.

The input is one ordinary JSON file inside the current workspace, at most
100,000 bytes. Unknown fields, duplicate JSON keys, unknown/repeated task ids,
cycles, overlapping running worker assignments, invalid numbers and inconsistent
progress are rejected. No files are written by the CLI; JSON goes to stdout.

## Reading the result

Each schedule entry is a remaining segment: `state` is `running` or `pending`.
For a running task, `start` is the snapshot time, **not its historical start**.
Completed tasks are listed separately and do not occupy future workers.

Ready tasks with the longest downstream duration go first, with task-id ties.
All simultaneous completions release their workers before new work is chosen.
`remaining_minutes` is the remaining makespan; `remaining_budget` can be negative.
An all-completed snapshot has an empty schedule and `finish = elapsed_minutes`.
It does not infer a historical completion time or certify an earlier deadline.

`deadline_verdict` distinguishes `fits`, `impossible_at_estimates` (the lower
bound exceeds the deadline), and `heuristic_misses_not_proven_impossible` (the
chosen ordering misses but another ordering may fit). Without a deadline it is
`not_requested`. The lower bound is the larger of remaining critical-path length
and total remaining work divided by worker count; it relaxes worker pinning.
The listed critical path is through remaining tasks, not the full historic job.

Exit codes: **0** for a fitting schedule or no deadline, **2** for a schedule that
misses, **1** for invalid input. Estimates and margins are assumptions, not a
guarantee. This heuristic is not an optimal solver. There are no task failures,
pauses, release calendars, worker skills or retries in this model. Convert a
failed task to pending and supply a new estimate only when its prerequisites are
still satisfied. Concurrent replacement of local input files is outside scope.

## Checks performed

```sh
python3 -B line-1/tools/replan/selftest.py
```

14 tests passed, including 300 seeded progress snapshots: full remaining task
coverage, dependency ordering, nonoverlapping workers, pinned running tasks,
simultaneous releases, unchanged input, deterministic input permutations, and
lower-bound consistency. Explicit cases cover delayed work, margins, completed
jobs, expired deadlines, a known feasible ordering missed by the heuristic,
inconsistent snapshots, malformed/oversized JSON, workspace bounds, numeric
precision loss, CLI exits, and compatibility with Workplan when nothing has
started. Tests create only disposable JSON under `test/scratch/replan/`.

Workplan's original self-test also passed (150 seeded graphs plus fixed cases).
These local observations do not independently certify behavior. The only runtime
source dependency is the unchanged sibling `../workplan/workplan.py`, already
included in this repository; keep the two folders together. No install needed.
