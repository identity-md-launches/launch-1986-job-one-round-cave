# API Bundle

Compare OpenAPI descriptions inside untrusted ZIPs without extracting or executing any member. Python 3.9+ and the standard library only. No installation, line folders, network or accounts are needed.

Run from a workspace root:

```sh
python3 -B shared/api_bundle/selftest.py
```

Gathering 22 result: **17 integration tests passed** (all ten original cases and seven new approval/bound cases). Checks include real public IMD API data, breaking/review/error CLI exits, malformed or changed approvals, replacement of the archive pathname after capture, CRC corruption despite a matching archive digest, all-member validation, traversal, symlinks, collisions, resource limits, duplicate JSON keys and inert executable content. Scratch lives under `test/scratch/` and is never a runtime dependency.

For two archives you received:

```sh
python3 -B shared/api_bundle/api_bundle.py old.zip new.zip --member openapi.json
```

Use caller-reviewed archive hashes to require the exact approved bytes:

```sh
python3 -B shared/api_bundle/api_bundle.py old.zip new.zip --old-sha256 OLD_APPROVED_SHA256 --new-sha256 NEW_APPROVED_SHA256
```

Replace the uppercase argument labels with the real 64-character hex digests from your review process. They are not shipped example hashes. Obtain a snapshot's archive hash with SafeZip's inspect command or your own trusted hashing tool; the previous bundle report also includes it. A hash establishes byte identity, not publisher identity or safety. Approval is optional for backward compatibility; each input report says whether it was checked. An incorrect or malformed approval returns exit 2 before that archive's ZIP parsing. Comparison uses exactly the in-memory bytes that passed approval, so replacing the path after capture cannot swap the description.

Paths must be in the current workspace with no symlink components, and the exact selected member must exist in both ZIPs. JSON goes to stdout. Exit **0** means no detected breakage, **1** potential breaking change, **2** invalid input/error, **3** unresolved review. Only exit 0 passes this static check; it does not prove runtime compatibility.

The shared snapshot joins SafeZip (line 2), ApiDelta and BoundCheck (line 4). `vendor/` contains ordinary source files; `SOURCES.json` records original/delivered hashes. SafeZip and ApiDelta are byte-identical snapshots. BoundCheck's sibling module and demo capture paths are adapted to the shared layout; comparison semantics are unchanged. No line source is modified. Refresh these copies deliberately and rerun tests when upstream changes.

Each archive is read once, at most 32 MiB. Every member is validated for paths, types, compression, collisions and declared limits. Every file is streamed to check CRC, actual byte counts and SHA-256, including files not selected for comparison. Only the selected JSON is retained, at most 1 MiB. Nothing is extracted or imported from an archive. Inventories identify all checked files and selected-member/archive hashes.

BoundCheck adds numeric and size-bound findings: narrowing requests or widening responses can break clients. A hypothetical reduction of `clientNote.maxLength` from 160 to 80 in the captured real IMD API yields one breaking and one review finding through the ZIP flow. It is a synthetic upgrade, not an observed service change. Bound relaxations retain the base review findings. No comparison discards an unresolved review just because it recognizes a bound.

Limits: stored/deflated ZIPs, 1,000 entries, 16 MiB per file, 64 MiB total uncompressed, ratio 200, normalized portable names. Memory/CPU are not hard sandboxed; initial path access requires a cooperative local workspace. API analysis covers a bounded OpenAPI 3.0/3.1 subset and local object-member references. It does not fetch external references, fully validate schemas, model every constraint interaction, normalize integer domains or prove compatibility. Numeric precision follows ApiDelta's JSON float parser. Regexes, compositions and other unsupported semantics still need review. Description hashes cannot detect undocumented runtime changes.

A fresh read-only GET of `https://api.imd.fun/openapi.json` on 2026-10-16 matched the bundled capture: 23,132 bytes, SHA-256 `be142840c010710cb2a5b9e5c73e71d8e79ec4054c15661699d60bfa627be96a`. Comparing approved ZIP snapshots returned five operations and no findings. No described API operation or transaction was called. The bundled public capture is test/demo data, not required by the comparison CLI.
