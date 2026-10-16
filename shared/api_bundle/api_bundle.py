#!/usr/bin/env python3
"""Compare OpenAPI JSON inside ZIP snapshots without extracting any member."""
import argparse
import hashlib
import hmac
import io
import json
from pathlib import Path
import re
import sys
import zipfile
import zlib

from vendor import apidelta, boundcheck, safezip

MAX_ARCHIVE = 32 * 1024 * 1024


def read_bundle(path, member='openapi.json', expected_sha256=None):
    if expected_sha256 is not None and (
            not isinstance(expected_sha256, str)
            or re.fullmatch(r'[0-9a-fA-F]{64}', expected_sha256) is None):
        raise ValueError('expected SHA-256 must be exactly 64 hexadecimal characters')
    # Snapshot once: validation and comparison see the same bytes even if the
    # source changes later. No archive pathname is ever used as an output path.
    path = safezip.local_path(path)
    if not path.is_file():
        raise ValueError('archive must be an ordinary workspace file')
    with path.open('rb') as source:
        raw = source.read(MAX_ARCHIVE + 1)
    if len(raw) > MAX_ARCHIVE:
        raise ValueError('archive exceeds 32 MiB')
    archive_sha256 = hashlib.sha256(raw).hexdigest()
    if expected_sha256 is not None and not hmac.compare_digest(
            archive_sha256, expected_sha256.lower()):
        raise ValueError('archive SHA-256 differs from approved digest')
    limits = argparse.Namespace(entries=1000, file_bytes=16*1024*1024,
                                total_bytes=64*1024*1024, ratio=200)
    selected = None
    inventory = []
    actual_total = 0
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        entries, _ = safezip.inventory(archive, limits)
        for info, name in entries:
            if info.is_dir():
                continue
            if name == member and info.file_size > apidelta.MAX_BYTES:
                raise ValueError('selected description exceeds 1 MiB')
            digest = hashlib.sha256()
            count = 0
            payload = bytearray() if name == member else None
            with archive.open(info) as stream:
                while True:
                    chunk = stream.read(65536)
                    if not chunk:
                        break
                    count += len(chunk)
                    actual_total += len(chunk)
                    if count > limits.file_bytes or actual_total > limits.total_bytes:
                        raise ValueError('streamed ZIP resource limit exceeded')
                    digest.update(chunk)
                    if payload is not None:
                        if count > apidelta.MAX_BYTES:
                            raise ValueError('selected description exceeds 1 MiB')
                        payload.extend(chunk)
            if count != info.file_size:
                raise ValueError('declared and actual member size differ')
            inventory.append({'path': name, 'bytes': count, 'sha256': digest.hexdigest()})
            if payload is not None:
                selected = bytes(payload)
    if selected is None:
        raise ValueError('selected description is missing or is a directory')
    obj = json.loads(selected, object_pairs_hook=apidelta.pairs,
                     parse_constant=lambda _: (_ for _ in ()).throw(ValueError('non-finite JSON')))
    apidelta.validate(obj)
    return obj, {'archive_sha256': archive_sha256,
                 'approved_sha256_checked': expected_sha256 is not None,
                 'member': member, 'member_sha256': hashlib.sha256(selected).hexdigest(),
                 'checked_files': inventory, 'all_payloads_crc_checked': True}


def compare(old, new, member='openapi.json', old_sha256=None, new_sha256=None):
    a, before = read_bundle(old, member, old_sha256)
    b, after = read_bundle(new, member, new_sha256)
    report = boundcheck.compare(a, b)
    report['bundle_inputs'] = {'old': before, 'new': after}
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('old', help='old workspace ZIP')
    parser.add_argument('new', help='new workspace ZIP')
    parser.add_argument('--member', default='openapi.json', help='exact member name in both ZIPs')
    parser.add_argument('--old-sha256', help='require these exact approved old archive bytes')
    parser.add_argument('--new-sha256', help='require these exact approved new archive bytes')
    args = parser.parse_args()
    try:
        report = compare(args.old, args.new, args.member, args.old_sha256, args.new_sha256)
        print(json.dumps(report, indent=2, allow_nan=False))
        return {'breaking': 1, 'review_required': 3, 'no_detected_breakage': 0}[report['status']]
    except (ValueError, OSError, RuntimeError, EOFError, zipfile.BadZipFile,
            NotImplementedError, zlib.error, RecursionError, TypeError, KeyError) as error:
        print(json.dumps({'ok': False, 'error': str(error)}, ensure_ascii=True))
        return 2


if __name__ == '__main__':
    sys.exit(main())
