# T-040 Real multi-protein Fig validation

- Status: completed real-data execution and validation; automatic detector/scientific acceptance NOT complete. Baseline c531238 (product9be19b1), active coordinator worktree retained.
- User approved: only source TIFF stems ending (1);8 files in10670059,4 Fig groups1D/1F/4F/4H.
- Target protein above beta-actin; output crop named protein.tif in each original folder, never overwrite.
- Preserve native-pixel crop for quantitative measurement. Additionally create standard presentation TIFF960 high,1200*N wide, dtype retained; presentation resampling not used for measurement.
- Reference folder10670059_验证 read-only. Freeze first automatic predictions before reference scoring/correction. Report correct/8 by row identity,N,complete intended bands,no adjacent row or Marker; corrections separate.
- Run actual desktop automatic crop→Fig label composition→group quantitative→XLSX; verify output/readback/source hashes and show real operating window.
- Scope WB application/adapters, desktop assembly if needed, validation tests/docs/work/handoff; no unrelated redesign or dependency upgrades.

## Observed results / scope

- First untouched automatic predictions frozen before reference-assisted geometry. Independent crop score1/8=12.5%,7fail,0unknown; no claim of general automatic success.
- Reference-assisted registration then8/8 visual crop criteria pass, NCC0.99786..0.99977. This is correction evidence, not detector test accuracy.
- Eight standardized960×1200N TIFFs written under original subfolders by protein name, dtype8/16 retained; embedded display-only provenance, quantitative loader rejects them. Original and reference SHA unchanged. Raw native samples separately exported exactly.
- Real desktop4Fig groups,2proteins/group,N8/4/8/4,48 raw values,PNG overview,4 high-res labeled TIFFs,CSV/XLSX and recoverable ZIP generated.
- Audit detected17/48 automatic-bound integrals below50% of full-window comparison because endpoints lay on slope/peak. Initial outputs preserved. Explicit supervised full isolated target windows now match48 independent source-pixel calculations. Numerical WBQuant formula unchanged; not an automatic-bound accuracy claim.
-33/48 source rectangles have lower-rail0; all24actin have substantial zero platforms. Retain clipping/linearity quality warnings, no default normalization or true abundance claim.
- New display-only standard policy/affine frames implemented T041, original quantification separate. Independent P1 split-frame duplicate-lane issue fixed by complete-row-only frame validation; sourceToOutput overlay and template-aware group bounds integrated.
- Public repository stores no private images/results. Local .local/t040 has all logs, frozen predictions, registration/profile audits and delivery pointers. Saved real project reopened visibly with 8 rows (PID32064), screenshot .local/t040/opened-desktop.png. Full check returned1 despite600 passed summary; not accepted as gate success. Isolated installed-wheels passed exit0 separately.
