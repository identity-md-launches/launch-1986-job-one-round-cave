"""Meaningful boundary/variance regressions; no network or output files."""
import copy
import unittest
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import boundcheck as b


def document(schema, version='3.1.0', response=False):
    media = {'application/json': {'schema': schema}}
    operation = {'responses': {'200': {'description': 'ok', 'content': media if response else {}}}}
    if not response:
        operation['requestBody'] = {'content': media}
    return {'openapi': version, 'paths': {'/items': {'post': operation}}}


def breaks(old, new, response=False, ov='3.1.0', nv='3.1.0'):
    report = b.compare(document(old, ov, response), document(new, nv, response))
    return [f for f in report['findings'] if f['code'] in ('numeric_bound_incompatible', 'size_bound_incompatible')]


class Tests(unittest.TestCase):
    def test_numeric_variance(self):
        for key, old, new in [('minimum', 1, 2), ('maximum', 2, 1), ('exclusiveMinimum', 1, 2), ('exclusiveMaximum', 2, 1)]:
            with self.subTest(key=key):
                self.assertTrue(breaks({key: old}, {key: new}))
                self.assertFalse(breaks({key: new}, {key: old}))
                self.assertFalse(breaks({key: old}, {key: new}, True))
                self.assertTrue(breaks({key: new}, {key: old}, True))

    def test_exclusive_equal_endpoints(self):
        for key, ex in [('minimum', 'exclusiveMinimum'), ('maximum', 'exclusiveMaximum')]:
            self.assertTrue(breaks({key: 5}, {ex: 5}))
            self.assertFalse(breaks({ex: 5}, {key: 5}))
            self.assertTrue(breaks({ex: 5}, {key: 5}, True))

    def test_30_exclusivity(self):
        self.assertTrue(breaks({'minimum': 1}, {'minimum': 1, 'exclusiveMinimum': True}, ov='3.0.3', nv='3.0.3'))
        self.assertFalse(breaks({'minimum': 1, 'exclusiveMinimum': True}, {'exclusiveMinimum': 1}, ov='3.0.3'))

    def test_combined_bounds(self):
        self.assertFalse(breaks({'minimum': 10}, {'minimum': 10, 'exclusiveMinimum': 5}))
        self.assertFalse(breaks({'maximum': 5}, {'maximum': 5, 'exclusiveMaximum': 10}))

    def test_added_removed(self):
        self.assertTrue(breaks({}, {'minimum': 0}))
        self.assertFalse(breaks({'minimum': 0}, {}))
        self.assertTrue(breaks({'maximum': 4}, {}, True))

    def test_sizes(self):
        for key in ('minLength', 'maxLength', 'minItems', 'maxItems', 'minProperties', 'maxProperties'):
            a, c = (2, 3) if key.startswith('min') else (3, 2)
            self.assertTrue(breaks({key: a}, {key: c}))
            self.assertFalse(breaks({key: c}, {key: a}))
            self.assertTrue(breaks({key: c}, {key: a}, True))
        self.assertFalse(breaks({}, {'minLength': 0}))

    def test_invalid_values(self):
        for schema in ({'minimum': True}, {'maxLength': -1}, {'minItems': 1.5}, {'exclusiveMaximum': False}):
            with self.assertRaises(b.api.Invalid):
                breaks({}, schema)
        with self.assertRaises(b.api.Invalid):
            breaks({}, {'exclusiveMinimum': True}, nv='3.0.3')

    def test_recursive_reference(self):
        old = document({'$ref': '#/components/schemas/N'})
        old['components'] = {'schemas': {'N': {'properties': {'child': {'$ref': '#/components/schemas/N'}, 'name': {'maxLength': 5}}}}}
        new = copy.deepcopy(old)
        new['components']['schemas']['N']['properties']['name']['maxLength'] = 3
        self.assertEqual(sum(f['code'] == 'size_bound_incompatible' for f in b.compare(old, new)['findings']), 1)

    def test_review_preserved(self):
        result = b.compare(document({'pattern': 'a'}), document({'pattern': 'b'}))
        self.assertEqual(result['status'], 'review_required')

    def test_cli_decisions(self):
        root = Path('test/scratch')
        root.mkdir(parents=True, exist_ok=True)
        script = str(Path(__file__).with_name('boundcheck.py'))
        with tempfile.TemporaryDirectory(dir=root) as directory:
            old = Path(directory) / 'old.json'
            new = Path(directory) / 'new.json'
            old.write_text(json.dumps(document({'maxLength': 10})))
            def run(schema):
                new.write_text(json.dumps(document(schema)))
                return subprocess.run([sys.executable, '-B', script, 'compare', str(old), str(new)],
                                      capture_output=True, text=True, timeout=10)
            self.assertEqual(run({'maxLength': 10}).returncode, 0)
            result = run({'maxLength': 5})
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result.stdout)['counts']['breaking'], 1)
            self.assertEqual(run({'maxLength': 20}).returncode, 3)
            self.assertEqual(run({'maxLength': -1}).returncode, 2)

    def test_demo_and_capture(self):
        self.assertEqual(b.demo()['counts']['breaking'], 1)
        obj, _ = b.api.load(b.BASE.with_name('imd-openapi.json'))
        self.assertEqual(b.compare(obj, obj)['counts'], {'breaking': 0, 'review': 0, 'info': 0})


if __name__ == '__main__':
    unittest.main()
