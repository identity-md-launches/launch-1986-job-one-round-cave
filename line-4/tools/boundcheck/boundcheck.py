#!/usr/bin/env python3
"""Offline OpenAPI bound-change analysis extending the sibling ApiDelta."""
import argparse
import copy
from decimal import Decimal
import importlib.util
import json
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parents[1] / 'apidelta' / 'apidelta.py'
spec = importlib.util.spec_from_file_location('apidelta_base', BASE)
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)


def number(value, keyword, integral=False):
    api.require(type(value) in (int, float), keyword + ' must be a number')
    result = Decimal(str(value))
    api.require(result.is_finite(), keyword + ' must be finite')
    if integral:
        api.require(type(value) is int and value >= 0, keyword + ' must be a nonnegative integer')
    return result


def endpoint(schema, doc, lower):
    key = 'minimum' if lower else 'maximum'
    exclusive = 'exclusiveMinimum' if lower else 'exclusiveMaximum'
    candidates = []
    if key in schema:
        candidates.append((number(schema[key], key), False))
    if exclusive in schema:
        value = schema[exclusive]
        if doc.obj['openapi'].startswith('3.0.'):
            api.require(type(value) is bool, exclusive + ' must be boolean in OpenAPI 3.0')
            api.require(not value or key in schema, exclusive + ' requires ' + key)
            if value:
                candidates = [(number(schema[key], key), True)]
        else:
            candidates.append((number(value, exclusive), True))
    if not candidates:
        return None
    if lower:
        return max(candidates)
    # A strict upper endpoint is tighter than an inclusive one at equal values.
    return min(candidates, key=lambda pair: (pair[0], not pair[1]))


def tighter(candidate, baseline, lower):
    if candidate is None:
        return False
    if baseline is None:
        return True
    a, ae = candidate
    b, be = baseline
    return (a > b if lower else a < b) or (a == b and ae and not be)


class Analyzer(api.Analyzer):
    def _schema(self, old, new, loc, direction):
        # Keep every base review finding; a new rule may promote a potential break,
        # but never silently accepts a change the base checker could not prove safe.
        super()._schema(old, new, loc, direction)
        for lower in (True, False):
            before = endpoint(old, self.old, lower)
            after = endpoint(new, self.new, lower)
            candidate, baseline = (after, before) if direction == 'request' else (before, after)
            if tighter(candidate, baseline, lower):
                key = 'minimum' if lower else 'maximum'
                self.emit('breaking', 'numeric_bound_incompatible', loc + '/' + key,
                          'Request numeric range narrowed.' if direction == 'request' else
                          'Response numeric range widened beyond the old contract.')
        for key in ('minLength', 'maxLength', 'minItems', 'maxItems', 'minProperties', 'maxProperties'):
            lower = key.startswith('min')
            def value(schema):
                return (number(schema[key], key, True), False) if key in schema else ((Decimal(0), False) if lower else None)
            before, after = value(old), value(new)
            candidate, baseline = (after, before) if direction == 'request' else (before, after)
            if tighter(candidate, baseline, lower):
                self.emit('breaking', 'size_bound_incompatible', loc + '/' + key,
                          'Request size bound tightened.' if direction == 'request' else
                          'Response size bound relaxed beyond the old contract.')


def compare(old, new):
    report = Analyzer(old, new).run()
    report['extension'] = 'boundcheck-v1'
    return report


def demo():
    old, digest = api.load(BASE.with_name('imd-openapi.json'))
    new = copy.deepcopy(old)
    schema = new['paths']['/requests/quote']['post']['requestBody']['content']['application/json']['schema']
    schema.setdefault('properties', {})['clientNote'] = {'type': 'string', 'maxLength': 80}
    old = copy.deepcopy(old)
    old['paths']['/requests/quote']['post']['requestBody']['content']['application/json']['schema'].setdefault('properties', {})['clientNote'] = {'type': 'string', 'maxLength': 160}
    report = compare(old, new)
    report['demo'] = 'Hypothetical clientNote bound change in a captured real public API; no service operation called.'
    report['capture_sha256'] = digest
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('demo')
    diff = sub.add_parser('compare')
    diff.add_argument('old')
    diff.add_argument('new')
    args = parser.parse_args()
    try:
        if args.command == 'demo':
            report = demo()
        else:
            old, oh = api.load(args.old)
            new, nh = api.load(args.new)
            report = compare(old, new)
            report.update(old_sha256=oh, new_sha256=nh)
        print(json.dumps(report, indent=2, allow_nan=False))
        return 0 if args.command == 'demo' else {'breaking': 1, 'review_required': 3, 'no_detected_breakage': 0}[report['status']]
    except (api.Invalid, OSError, ValueError, TypeError, KeyError, RecursionError) as exc:
        print('boundcheck: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
