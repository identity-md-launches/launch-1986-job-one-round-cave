#!/usr/bin/env python3
"""Try real captured public data through line tools and the shared integration."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile


def main():
    root = Path(__file__).resolve().parent.parent
    scratch = root / 'test/scratch'
    scratch.mkdir(parents=True, exist_ok=True)
    results = []
    with tempfile.TemporaryDirectory(prefix='gathering-trial-', dir=scratch) as directory:
        work = Path(directory)
        archives = []
        for name, source in [('old', 'shared/api_bundle/imd-openapi.json'),
                             ('new', 'gathering/imd-openapi-current.json')]:
            path = work / (name + '.zip')
            with zipfile.ZipFile(path, 'w') as archive:
                archive.writestr('openapi.json', (root / source).read_bytes())
                archive.writestr('notes.txt', 'Public description only; contents are never executed.\n')
            archives.append((str(path.relative_to(root)), hashlib.sha256(path.read_bytes()).hexdigest()))
        old, new = archives
        request = 'line-3/tools/rewardsplit/example.json'
        metadata = 'gathering/zto-mainnet-22.json'
        report = str((work / 'allocation.json').relative_to(root))
        jobs = [
            ['line-2/tools/safezip/safezip.py', 'inspect', new[0]],
            ['line-2/tools/safezip/safezip.py', 'extract', new[0], str((work / 'unpacked').relative_to(root)), '--sha256', new[1]],
            ['line-4/tools/boundcheck/boundcheck.py', 'compare',
             'shared/api_bundle/imd-openapi.json', 'gathering/imd-openapi-current.json'],
            ['shared/api_bundle/api_bundle.py', old[0], new[0], '--old-sha256', old[1], '--new-sha256', new[1]],
            ['line-3/tools/rewardsplit/rewardsplit.py', 'allocate', '--input', request, '--metadata', metadata, '--output', report],
            ['line-3/tools/rewardreceipt/rewardreceipt.py', 'verify', '--request', request, '--metadata', metadata, '--report', report],
            ['shared/api_bundle/selftest.py'],
        ]
        for args in jobs:
            command = [sys.executable, '-B', *args]
            run = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=90)
            results.append(dict(command=command, expected_exit=0, exit=run.returncode,
                                passed=run.returncode == 0, stdout=run.stdout, stderr=run.stderr))
        # Confirm extraction preserved actual API bytes, beyond its inventory claims.
        assert (work / 'unpacked/openapi.json').read_bytes() == (root / 'gathering/imd-openapi-current.json').read_bytes()
        if (work / 'allocation.json').exists():
            allocation = json.loads((work / 'allocation.json').read_text())
            assert sum(int(a['units']) for a in allocation['allocations']) == 10**18
    (root / 'gathering/integration-results-22.json').write_text(json.dumps(results, indent=2) + '\n')
    for result in results:
        print('PASS' if result['passed'] else 'FAIL', ' '.join(result['command']), 'exit', result['exit'])
    return 0 if all(row['passed'] for row in results) else 1


if __name__ == '__main__':
    sys.exit(main())
