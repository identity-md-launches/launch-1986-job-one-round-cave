#!/usr/bin/env python3
"""Verify a RewardSplit report against its inputs and print a review receipt."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1] / "rewardsplit"
SPEC = importlib.util.spec_from_file_location("rewardsplit", ROOT / "rewardsplit.py")
rs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rs)


def canonical_bytes(value):
    """Encode JSON data with stable key order while preserving value types."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def digest(value):
    """Hash a data object independent of JSON whitespace and key order."""
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def verify(request, report, metadata):
    """Return a receipt only if this is exactly RewardSplit's recomputed report."""
    expected = rs.allocate(request, metadata)
    if canonical_bytes(report) != canonical_bytes(expected):
        raise rs.Invalid("report differs from the exact allocation recomputed from the supplied request and metadata")
    if not isinstance(report, dict):
        raise rs.Invalid("report must be an object")
    return {
        "schema": "rewardreceipt-v1",
        "result": "verified exact RewardSplit allocation",
        "token": expected["token"],
        "budget_units": expected["budget_units"],
        "contributors": len(expected["allocations"]),
        "request_sha256": digest(request),
        "metadata_sha256": digest(metadata),
        "report_sha256": digest(report),
        "scope": "offline arithmetic and input agreement only; no work, identity, balance, signature, or payment verified",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("demo", help="verify a fresh allocation of the included ZTO example")
    check = sub.add_parser("verify", help="verify a saved RewardSplit allocation report")
    check.add_argument("--request", required=True, help="original RewardSplit input JSON")
    check.add_argument("--report", required=True, help="saved RewardSplit allocation JSON")
    check.add_argument("--metadata", default=str(ROOT / "zto-mainnet.json"),
                       help="the same token capture used to allocate")
    args = parser.parse_args(argv)
    try:
        if args.command == "demo":
            request = rs.read_json(ROOT / "example.json")
            metadata = rs.read_json(ROOT / "zto-mainnet.json")
            report = rs.allocate(request, metadata)
        else:
            request = rs.read_json(args.request)
            metadata = rs.read_json(args.metadata)
            report = rs.read_json(args.report)
        print(json.dumps(verify(request, report, metadata), indent=2, ensure_ascii=True))
    except (rs.Invalid, OSError, ValueError, OverflowError) as exc:
        message = str(exc) if isinstance(exc, rs.Invalid) else type(exc).__name__
        print("rewardreceipt: " + message, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
