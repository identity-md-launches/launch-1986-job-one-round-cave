# Wall 22 — The Sealed Basket

The new small basket is tied shut beside the inherited guardian: keep the bytes
that were reviewed together until extraction. SafeZip now supports requiring an
approved archive SHA-256 and extracts from the very snapshot it hashed.

## Deliverables and review

- Required output: `artifacts/line-2/wall-v3.png`, PNG, 1254 × 1254,
  2,848,778 bytes. Left untracked for separate output delivery.
- Continuing wall: `artifacts/line-2/wall.png`, byte-identical PNG at the inherited
  wall path, preserving the reference for the next worker.
- Preview: `dist/line-2/22.jpg`, JPEG, 512 × 512, 77,860 bytes.
- Record: `dist/line-2/22.json`. Image digest:
  `334dc07042b4bc27e048ef11655d3496e7f81f722a56f70d8c1c3c3648249206`.

Reviewed the inherited wall before generation, the generated full wall, and the
encoded JPEG. The existing Pepe, open basket, stone arch and thorn remain in
place. The new sealed basket and two ochre pebbles occupy previously bare rock
above and to the right. Pepe retains his wide mouth and heavy-lidded eyes.
Counted both inherited hands: each has four fingers and one thumb; no new hands
or stencils were added. No letters, numbers, captions, signatures, logos,
watermarks, borders, real people or political symbols were observed. Warm rock,
major cracks, cave framing, earth pigments and square dimensions are retained.
Unmet visual requirements: none observed at this visual review. Limitation:
generative editing is not a guarantee of pixel-identical rock or ancestral
pigment outside the addition; the inherited figures visibly retain their forms
and positions. The sealed basket's weave has more detail than a thumb mark.

The built-in image editor received the inherited PNG with instructions to add
only a modest closed basket with a knotted lid and two pebble impressions on
upper-right bare rock, retain every ancestor mark, and use worn ochre, charcoal
and chalk without text. One draft was generated and retained. The image import
tool copied it into the required output path. ffmpeg encoded the 512-pixel JPEG;
no image library or other dependency was installed or added to the tool.

The image inspection tool accepted both formats and confirmed their dimensions.
The record digest was recomputed from the PNG; both wall copies match. The 21
pre-existing JSON records include unpainted placeholders. This contribution uses
22 because the assignment explicitly defines the number as record count plus
one. No previous record was changed.

## Tool verification

Run from the repository root:

```sh
python3 -B line-2/tools/safezip/selftest.py
```

Observed: 24 tests passed. All original 16 checks remain; eight new checks cover
approved-byte extraction and its failure modes. Source replacement after snapshot
capture still extracted only approved bytes. A mismatched digest was rejected
before ZIP parsing; no destination or staging directory was created. Corruption
with a matching archive hash still failed CRC verification. No network call,
transaction, credential, environment-variable read or outside-workspace input
was involved. GOAL.md remains unchanged.
