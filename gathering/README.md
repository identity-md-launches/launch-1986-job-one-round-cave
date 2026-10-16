# Gathering 22 — Keep the Checked Tools Together

Reviewed every line and extended the existing shared API Bundle with approved archive digests and BoundCheck's request/response bounds. All line files, records, goals and previews are unchanged. See `REPORT.md` for per-line trials, limits and the missing inherited line 4 JPEG, and `COINS.md` for the decision to request no new token or deployment.

Run the shared working piece offline:

```sh
python3 -B shared/api_bundle/selftest.py
```

Observed: 17 integration tests passed, including all ten predecessor checks. Ordinary vendored Python and the standard library are sufficient; nothing needs downloading. The sharing connects line 2's ZIP policy and approved-byte checks to line 4's compatibility rules. Its README explains real archive use and decision exits.

Repeat all line checks without writing in line folders:

```sh
python3 -B gathering/check_tools.py
```

Observed: 116 unittest cases passed, plus Workplan's original checks and seeded graphs. The 20% uncertainty-margin example deliberately returns exit 2 and is checked as such. Copies live under disposable `test/scratch/`; no runtime dependency uses them.

Try the included real public captures through extraction, comparison, allocation and receipt verification:

```sh
python3 -B gathering/try_lines.py
```

Observed: seven commands returned exit 0. The API capture is unchanged; 1 ZTO allocates with exact conservation and verifies against fresh read-only Ethereum metadata at block 26206046. These observations are not payment evidence or an API runtime guarantee. Neither script calls the network. Captures and commands/results are in `live-check-22.json`, `zto-mainnet-22.json`, `check-results-22.json` and `integration-results-22.json`.

Rebuild the static gallery and goals:

```sh
python3 -B gathering/build_gallery.py
```

This is a later gathering. All previous records and reserved slots 02–21 are preserved. The existing round uses record count plus one, so the new gathering mark is 22. The gallery includes every numbered record, painted newest first by wall, with unpainted slots linked separately newest first. Styling is inline; previews are sibling JPEGs, with full artifact fallback for the inherited missing line 4 preview. Open `dist/index.html` or serve `dist/` with a static server.

Check the delivery:

```sh
python3 -B gathering/check_delivery.py
```

## Wall

Required output: `artifacts/gathering/wall-v3.png`, PNG, **1254 × 1254**. The canonical continuation `artifacts/gathering/wall.png` is a relative symlink to `wall-v3.png`, the separately delivered required output; reading either path returns identical bytes. This avoids storing the same 3.95 MB image twice in the source bundle. Keep the link beside the delivered PNG. Preview: `dist/gathering/22.jpg`, JPEG, **512 × 512**, below 100 KB. Record: `dist/gathering/22.json`; its artifact URL is the lowercase SHA-256 of the actual required PNG. Details are in `review-22.json` and `preservation-22.json`.

The installed imagegen tool generated an isolated pigment mark; standard-library Python combined it with the inherited wall, and FFmpeg decoded/encoded image bytes and made the required JPEG. No media library was installed. A first placement was too faint in the shadow and was discarded. The final addition is two worn flints tied by an ochre cord on bare rock above the inherited Pepe. All 1,528,516 pixels outside the 220 × 200 addition rectangle are unchanged, including all ancestral pigment, hands, face, basket and trails. Only the finished wall and its required JPEG are saved as new images (the canonical wall links to the required output).

Chosen review step: inspect the original and finished wall and the JPEG with `view_image`, then compare protected pixels against the original Git blob. Counted each inherited hand as **four fingers and one thumb**, five digits; no hands or handprints added. No prohibited text, marks or figures observed. Warm rock, cracks, lighting, framing and square dimensions retained. Unmet visual requirements: none observed. The addition is pale and finer in detail than the inherited figure; visual judgment is a single worker's review.

Final generation prompt (installed imagegen tool, built-in mode):

> A tiny primitive prehistoric cave-painting symbol, isolated on uniform pure black. Two flint stones bound together with one red ochre cord, simple charcoal outlines and sparse chalk and yellow ochre dry pigment hatching. The ochre cord has one simple central knot. Flat rough hand-painted burnt-stick strokes, ragged and worn like Lascaux, absolutely not photorealistic stones. Center this single mark within broad empty black margins. NO hands, NO people, NO text or numbers, no logo or watermark, no border, no framing, no realistic shadow, no 3D. The two bound tools symbolize workers keeping reviewed things together.

The black isolation background is removed during compositing; it is not a panel or frame on the finished cave. Only the new pigment is placed, leaving ancestor marks in their original locations and pixels.
