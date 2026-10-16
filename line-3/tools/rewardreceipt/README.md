# RewardReceipt

RewardReceipt checks a saved RewardSplit allocation against the exact request and token metadata used to make it. It recomputes every amount, tie break, and report field, then prints a canonical SHA-256 receipt. It uses Python's standard library and the existing line 3 RewardSplit code. Nothing is signed or sent.

From the repository root, see it work offline with the included real ZTO metadata:

```sh
python3 -B line-3/tools/rewardreceipt/rewardreceipt.py demo
```

To check your own report, first create it with RewardSplit's `allocate --input REQUEST --output REPORT`, then run:

```sh
python3 -B line-3/tools/rewardreceipt/rewardreceipt.py verify --request REQUEST --report REPORT
```

If allocation used another metadata capture, supply that same file with `--metadata PATH`. The default is the included ZTO mainnet capture at block 26205319. File reads follow RewardSplit's workspace-only and 256 KiB input limits. A mismatch or malformed input exits 2 without a receipt.

The receipt hashes canonical JSON values, so whitespace and object-key order do not change a digest. Array order and JSON value types remain significant. Keep the original request, metadata, and report with the receipt: their hashes identify the canonical values, while the receipt alone cannot recover them. The saved metadata is one public RPC observation, not an independent chain proof. This check establishes arithmetic agreement only; it cannot prove work quality, address ownership, available token balance, or payment.

Tried here: the demo verified 1 ZTO split across the three illustrative roles, and the offline tests passed. The tests reject a changed unit, weights, token block, added payment claim, numeric type substitution, and duplicate JSON keys:

```sh
python3 -B line-3/tools/rewardreceipt/selftest.py
```
