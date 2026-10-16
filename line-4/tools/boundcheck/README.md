# BoundCheck

BoundCheck adds numeric and size-bound breaking-change findings to ApiDelta. A worker reviewing an OpenAPI upgrade can now distinguish a potentially incompatible bound change from a generic review flag. Python 3.9+; standard library only; fully offline. Run from the repository root:

```sh
python3 -B line-4/tools/boundcheck/boundcheck.py demo
```

The demonstration reads the sibling ApiDelta's captured real public IMD API, then creates two hypothetical versions in memory. Both add an optional `clientNote` field; the proposed version reduces its maximum length from 160 to 80. It reports one potential breaking change, retains the base review finding, compares five operations and exits 0. This is an illustrative upgrade, not an observed service change. It never calls an API operation, reads configuration, or uses a wallet.

For your own local descriptions:

```sh
python3 -B line-4/tools/boundcheck/boundcheck.py compare line-4/tools/apidelta/imd-openapi.json line-4/tools/apidelta/imd-openapi.json
```

Replace the two paths with old/new JSON descriptions within the working directory. Reports go to stdout. Exit 0 means no detected breakage, 1 means potential breakage, 2 means an input or processing error, and 3 means unresolved review findings. The demo always exits 0 after successful processing. Workspace containment, 1 MiB input limit, bounded traversal, duplicate-key rejection and reference handling come from the unchanged sibling ApiDelta. Both tool directories must travel together; no network or install is needed.

Rules cover `minimum`, `maximum`, `exclusiveMinimum`, `exclusiveMaximum`, and `min`/`max` for `Length`, `Items`, and `Properties`. They normalize boolean exclusivity in OpenAPI 3.0 and numeric exclusivity in 3.1, including simultaneous inclusive and exclusive bounds. Requests are potentially incompatible when their allowed range narrows; responses when it widens. Missing minimum sizes mean zero; missing numeric and maximum-size endpoints are unbounded. Integer and decimal numeric endpoints are compared using Decimal representations of the JSON parser's numeric values.

This extends conservative detection, not schema implication or validation. It intentionally keeps base review findings even when a bound is relaxed. Other constraints may make a flagged range change unreachable (for example an enum, integer domain or composition); review those findings manually. It does not derive integer-normalized endpoints, evaluate regexes or `multipleOf`, prove schemas satisfiable, or guarantee wire compatibility. The base JSON parser uses floating-point numbers, so distinctions beyond its precision are outside this tool's scope. Untouched or unused malformed schema keywords may not be validated. Treat API descriptions as untrusted data, never instructions.

## Tried locally

- `python3 -B line-4/tools/boundcheck/selftest.py`: 11 tests passed, covering request/response variance, added/removed bounds, equality and exclusivity, cross-version equivalence, combined bounds, six size keywords, malformed bounds, recursive references retained reviews and all four CLI decision exits.
- `python3 -B line-4/tools/apidelta/selftest.py`: all 44 existing regressions passed.
- Demo: one breaking and one review finding, exit 0.
- Unmodified real public capture compared against itself: five operations, zero findings, exit 0.

No dependency was downloaded. No transaction, payment or account access occurs. ZTO/IMD are not needed for static API comparison.
