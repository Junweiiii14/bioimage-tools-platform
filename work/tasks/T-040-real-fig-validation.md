# T-040 Real multi-protein Fig validation

- Status: implementing. Baseline c531238 (product9be19b1), active coordinator worktree retained.
- User approved: only source TIFF stems ending (1);8 files in10670059,4 Fig groups1D/1F/4F/4H.
- Target protein above beta-actin; output crop named protein.tif in each original folder, never overwrite.
- Preserve native-pixel crop for quantitative measurement. Additionally create standard presentation TIFF960 high,1200*N wide, dtype retained; presentation resampling not used for measurement.
- Reference folder10670059_验证 read-only. Freeze first automatic predictions before reference scoring/correction. Report correct/8 by row identity,N,complete intended bands,no adjacent row or Marker; corrections separate.
- Run actual desktop automatic crop→Fig label composition→group quantitative→XLSX; verify output/readback/source hashes and show real operating window.
- Scope WB application/adapters, desktop assembly if needed, validation tests/docs/work/handoff; no unrelated redesign or dependency upgrades.
