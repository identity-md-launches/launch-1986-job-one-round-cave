#!/usr/bin/env python3
"""Repeat offline line checks in disposable copies, never write in a line folder."""
import concurrent.futures
import json
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    root = Path(__file__).resolve().parent.parent
    scratch = root / 'test/scratch/gathering22'
    scratch.mkdir(parents=True, exist_ok=True)
    for n in range(1, 5):
        shutil.copytree(root / f'line-{n}/tools', scratch / f'line-{n}/tools', dirs_exist_ok=True)
    jobs = [
        (1, 'workplan/workplan.py', ['--self-test'], 0),
        (1, 'workplan/workplan.py', ['--demo', '--workers', '2', '--budget', '25'], 0),
        (1, 'replan/selftest.py', [], 0),
        (1, 'replan/replan.py', ['--demo', '--workers', '2', '--budget', '27'], 0),
        (1, 'replan/replan.py', ['--demo', '--workers', '2', '--budget', '27', '--margin-percent', '20'], 2),
        (2, 'safezip/selftest.py', [], 0),
        (3, 'rewardsplit/selftest.py', [], 0),
        (3, 'rewardsplit/rewardsplit.py', ['demo'], 0),
        (3, 'rewardreceipt/selftest.py', [], 0),
        (3, 'rewardreceipt/rewardreceipt.py', ['demo'], 0),
        (4, 'apidelta/selftest.py', [], 0),
        (4, 'apidelta/apidelta.py', ['demo'], 0),
        (4, 'boundcheck/selftest.py', [], 0),
        (4, 'boundcheck/boundcheck.py', ['demo'], 0),
        (4, 'boundcheck/boundcheck.py', ['compare',
            'line-4/tools/apidelta/imd-openapi.json', 'line-4/tools/apidelta/imd-openapi.json'], 0),
    ]

    def run(job):
        n, file, args, expected = job
        script = scratch / f'line-{n}/tools' / file
        command = [sys.executable, '-B', str(script.relative_to(root)), *args]
        result = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=90)
        return dict(line=n, command=command, expected_exit=expected, exit=result.returncode,
                    passed=result.returncode == expected, stdout=result.stdout, stderr=result.stderr)

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(run, jobs))
    (root / 'gathering/check-results-22.json').write_text(json.dumps(results, indent=2) + '\n')
    for row in results:
        print(('PASS' if row['passed'] else 'FAIL'), ' '.join(row['command']), 'exit', row['exit'])
    return 0 if all(row['passed'] for row in results) else 1


if __name__ == '__main__':
    sys.exit(main())
