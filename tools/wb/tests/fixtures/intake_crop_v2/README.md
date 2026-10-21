# Historical automatic-crop fixtures

These synthetic JSON documents were produced by the unmodified WB package at
`941b424a2e6a2afb994737d022a7f754808b4242`, extracted with `git archive`.
They are not current policy@3 objects with renamed versions.

`source.json` uses that revision's `test_source_geometry.membrane(angle=3)`
(including its marker) and `test_intake_automatic_crop.prepared`.
`guided.json` uses that revision's `test_instrument_geometry.grouped`.
Both run public propose → automatic accept → claim/export/complete raw crop →
claim/prepare/complete Fig. They contain policy@2, source/guide geometry@1,
original-coordinate slots, synthetic asset identities and a completed Fig.
No private images or user project data are included. Synthetic TIFFs/PNG are
not required to read these frozen documents and are not committed.

Tests require the complete JSON structure to survive reading and serialization,
retain machine-vs-human provenance, and reject individually forged candidate or
companion identities. Existing history is never silently re-detected with v3.
