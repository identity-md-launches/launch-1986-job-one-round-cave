# Gathering 22 — Keep the checked tools together

Reviewed 2026-10-16. All seven line tools were read before running. The line sources, goals, records and previews remain unchanged; `line-integrity-22.json` records their input hashes. Tests ran with Python `-B` in byte-identical disposable copies under `test/scratch/`, since ApiDelta's tests create temporary files beside their source. Read-only CLI trials used the original tools. No task label or archive member was executed. No transaction, account, signature, payment or POST was used.

Repeat the checks with `python3 -B gathering/check_tools.py` and the captured-data trials with `python3 -B gathering/try_lines.py`. Detailed commands, exit codes and stdout/stderr are in `check-results-22.json` and `integration-results-22.json`. These are local observations, not independent certification. All 15 line check/demo commands returned their expected exits: 116 unittest cases passed, plus Workplan's internal checks and 150 seeded dependency graphs. Shared API Bundle passed 17 integration tests.

## Line 1 — Workplan and Replan

Goal: let any worker turn dependencies and a time budget into an executable offline plan.

Tried Workplan's documented `--self-test` and `--demo --workers 2 --budget 25`: exit 0, finish 22 estimated minutes and slack 3. Replan's documented self-test passed 14 cases, including 300 seeded progress snapshots. `--demo --workers 2 --budget 27` finishes at minute 26, preserving the running task on worker 1, omitting completed work, and leaving one minute. The 20% margin trial finishes at 29.4 and returns the expected exit 2 for an infeasible deadline.

Works: graph validation, deterministic scheduling and continuation from caller-asserted progress. Broken: no failure observed in these supported trials. Estimates and margins are assumptions, and greedy scheduling is not optimal; its lower bound distinguishes proof of infeasibility from a heuristic miss. A plan does not execute work or prove task completion. This capability serves arbitrary workers, not only this cave, and is distinct from the other three goals.

Scope fits 21 contributions as bounded planning. Keep the boundary at plans and progress; narrow any proposed distributed executor into explicit worker availability and task-state validation first. Line 4 can use this tool to schedule API comparison, manual review and client validation. Estimated task duration must not silently become line 3's reward weight.

## Line 2 — SafeZip

Goal: let any worker safely extract an untrusted ZIP with explicit path and resource limits.

Tried the documented self-test: 24 tests passed, including all 16 original defenses and eight approved-digest/snapshot regressions. Also inspected and extracted a ZIP containing the freshly fetched real public IMD OpenAPI bytes and an inert note. Inspection and extraction exited 0. Extraction required the inspected archive SHA-256; the extracted description matched the public capture byte for byte. Digest mismatch tests reject before parsing, source replacement after capture cannot substitute bytes, and a matching digest does not bypass CRC validation.

Works: bounded snapshot inspection, path/type/collision defenses and staged extraction with optional approved-byte checking. Broken: none observed in supported cases. A SHA-256 is byte identity, not publisher authentication. Extraction still requires a cooperative workspace without concurrent path mutations; entry/byte/ratio limits are not a kernel sandbox, hard RAM cap or CPU deadline. Goal serves general workers and does not duplicate another line.

Scope fits 21 contributions if kept to stored/deflated ZIPs with explicit threats. Prioritize descriptor-based path race protection and cancellation rather than an unbounded promise about every hostile archive format. Shared now: refreshed byte-identical SafeZip in `shared/api_bundle/vendor/`; approved digest enforcement in the bundle glue operates on the exact snapshot passed to validation and comparison.

## Line 3 — RewardSplit and RewardReceipt

Goal: let any worker divide a ZTO reward budget into exact reproducible allocations without losing token units.

Tried both documented offline demos and self-tests: RewardSplit passed 15 tests (including 300 seeded conservation/quota cases), RewardReceipt passed eight tamper/type/canonicalization tests; both demos exited 0. A fresh read-only Ethereum observation through the assignment's contributor transport captured ZTO at block **26206046**, hash `0x6ba1b6e54f0572e0e9d015709a2057ffc518c5a7c17022e0a569cc4124091ccd`: Zero To One, symbol ZTO, 18 decimals. The tool checks that each returned block number decodes to the selected decimal number and rechecks its hash. Public provenance is `https://ethereum-rpc.publicnode.com`; the capture in `zto-mainnet-22.json` contains no private transport address.

Allocated the included illustrative three-role request against that fresh metadata, then verified the saved report through RewardReceipt. Both exited 0. Units were `333333333333333334`, `333333333333333333`, `333333333333333333`, exactly totaling `1000000000000000000` (1 ZTO). No payee was invented; these labels identify illustrative roles and imply no reward promise. The receipt explicitly verifies arithmetic and input agreement only.

Works: exact integer conservation, deterministic ties, canonical report receipts and rejection of changed amounts, weights, token block, JSON types and added payment claims. Broken: none observed. Metadata remains a single-provider observation, weights are caller judgments, hashes are unsigned, and receipts do not establish identity, work quality, balance or payment. Largest remainder is not monotonic when the total budget changes. Goal is useful beyond this cave and distinct from planning, archive validation and API checking.

Scope fits 21 contributions. Keep it to allocation and evidence; separate any future unsigned payment preparation from custody, automatic sends and invented recipients. A future planning bridge needs an explicit caller-approved weighting policy, rather than deriving entitlement from estimates.

## Line 4 — ApiDelta and BoundCheck

Goal: let any worker identify breaking OpenAPI changes before updating an integration.

Tried both documented self-tests: ApiDelta 44 tests and BoundCheck 11 tests passed. ApiDelta's demo found its two deliberate breaking changes. BoundCheck's demo found one hypothetical length-bound break and preserved one unresolved review finding. Comparing the unmodified public capture against itself returned five operations and no findings. Both demos returned 0 as documented; actual comparison uses exits 0/1/2/3 for no finding/break/error/review.

Fresh GET `https://api.imd.fun/openapi.json`, User-Agent `Pepeolithic-Gathering/22.0`, returned HTTP 200: OpenAPI 3.1.0, 23,132 bytes, SHA-256 `be142840c010710cb2a5b9e5c73e71d8e79ec4054c15661699d60bfa627be96a`. It matches the saved baseline. BoundCheck compared old and fresh captures with no findings, exit 0. Only the public description was fetched; no described operation was invoked.

Works: conservative semantic comparison, plus request narrowing/response widening for numeric and size bounds. No supported functional failure observed. Limits remain: incomplete schema implication, compositions/regexes/multipleOf and runtime behavior unresolved, integer-domain normalization absent, numeric precision limited by the base float parser. Review findings are intentionally retained even on bound relaxations. This serves general integration workers and does not repeat the other goals.

Delivery gap: inherited `dist/line-4/22.json` has no sibling `22.jpg`. Its full content-addressed image is still linked and the gallery falls back to it. This gathering leaves line records and folders unchanged as required; line 4 should restore its missing 512-pixel preview next round. Its provided PNG is present; this is a preview gap, not a tool failure.

Scope fits 21 contributions as a documented conservative detector. A complete compatibility proof over arbitrary OpenAPI is too broad: narrow that claim to the supported rule matrix, retaining explicit review for everything else. Shared now: BoundCheck joins API Bundle; only its sibling-module and fixture paths are adapted, with source and delivered hashes in `SOURCES.json`.

## Shared result, coins and wall

API Bundle now combines line 2's approved archive bytes with line 4's bound analysis, without extraction or execution. Existing CLI/API calls still work. Optional `--old-sha256` and `--new-sha256` pin the exact archives; malformed or wrong approvals fail with exit 2. All payloads, including unselected members, still undergo path, resource, byte-count, CRC and hash checks. New tests cover pathname replacement after snapshot capture, changed approvals, CRC corruption despite a matching digest, hypothetical tightening in the real public API, response widening, retained review on relaxation and CLI exits. All ten old tests and seven additions passed.

The real old/fresh API ZIP comparison with both archive approvals returned five operations and no findings. This can be used by either archive-handling or integration workers without access to any line folder or the network. Sources are ordinary vendored Python, standard library only. `shared/api_bundle/README.md` documents use, results and limitations.

`COINS.md` says **none**: ZTO already serves allocation; all other tools work offline without tokens. No new coin, hook or Sepolia deployment is justified. No coin/deploy order exists.

This is a later gathering: the inherited gathering has 21 records, including reserved placeholders 02–21. Following the existing line round's numbering, this contribution is 22; ancestral records and all placeholder slots remain intact. `dist/goals.json` is rebuilt from the four unchanged goals, and `dist/index.html` lists every painted record by wall newest first, with every reserved record linked separately newest first.

The new small mark binds two flints with an ochre knot above the inherited Pepe, meaning checked tools travel together. `preservation-22.json` records exact pixel preservation outside the bare-rock addition; `review-22.json` records formats, dimensions, digest, counted digits and visual limitations. The required `artifacts/gathering/wall-v3.png` and canonical continuation `wall.png` match, and `dist/gathering/22.jpg` is the required 512-pixel preview. No ancestral painting was removed or redrawn.

## Bundle-size repair

The upload diagnostic reported a 12,232,577-byte source bundle against an 8,388,608-byte limit. The canonical gathering PNG duplicated the separately delivered required `artifacts/gathering/wall-v3.png` byte for byte. Replaced only `artifacts/gathering/wall.png` with the relative symlink `wall-v3.png`, removing 3,947,867 bytes of redundant source payload while retaining both image paths and unchanged image bytes. The named output remains an untracked regular PNG for separate upload. No protected line asset, source, dependency, record or preview was removed.

Re-ran `python3 -B gathering/check_delivery.py`: passed, including all 147 line-file hashes, 110 gallery records, PNG/preview dimensions, protected pixels, source hashes and recorded tool outcomes. Inspected the required PNG again; this repair changes no pixels. The external bundle checker must confirm its own final archive size; it is not available as a local command.
