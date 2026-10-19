# WBQuant 1.4.3 supervision policy v1

## Scope and compatibility

New web workflows explicitly select `quant_policy=wbquant_1_4_3@1` and
`geometry_policy=independent_lanes@1`. Missing fields retain `legacy_bounds@1`
and `fixed_grid@1`; no old plan is automatically recalculated. These named policies
are persisted in requests, automatic provenance and immutable results. The existing
`profile_integral@1` numerical formula and project schema 8 remain unchanged.

The MIT reference snapshot lives at `wb_tool/domain/wbquant143`, with LICENSE and
original source SHA256 in SOURCE.json. Only numerical code is statically imported.
No plugin/module paths are loaded from user files. Its scalar/NumPy annotations and
formatting are frozen rather than mass-rewritten: Ruff excludes this exact directory
(including explicit hook filenames via force-exclude); Pyright ignores only this
third-party snapshot. The typed application/domain/adapters wrappers, tests and
all existing product code retain strict checking. SciPy 1.18.1 was already locked;
it is now an explicit WB runtime dependency so an isolated wheel can run detection.

## Algorithm

The reference full `quantify_image` is used, including automatic border insets,
weak-peak suggestions and cross-lane frame consensus. Default prominence fraction
0.05, width 3, distance 5 and smoothing sigma 0 are unchanged. Detection and peak
support use the reference rules; measurement reuses original row means and
`profile_integral@1`, never preview pixels. RGB conversion remains integer BT.601.

All included peaks are retained in vertical order (`target`, `target-2`, ...).
Excluded frame counts, weak candidates, original/effective ROI coordinates and
boundary warnings remain in `detection_notes`; missing detection is not zero.
The project does not infer protein identities from multiple peaks. Light-polarity
support explicitly reflects original intensity around the original dtype maximum
before applying the dark-band reference policy.

The old program required identical lane dimensions. Independent geometry permits
integer widths to differ (e.g. 236/3 gives 78,79,79 pixels), preserving lane identity,
left-to-right order, containment within the original crop and no overlaps. Effective
ROI after reference border exclusion is stored in original coordinates; original
ROI is recorded in notes when changed. It is not a resampled display rectangle.

## Edits and background work

`update_quant_lane(project,row_id,lane_id,roi=...,bounds=...,baseline=...,band_id=...)`
clears the current run and synchronizes machine provenance without claiming human
review. A geometry change discards prior peak boundaries and marks replan required.
`replan_quant_lanes(path,project,row_id,cancelled=...)` loads the verified original
in a background caller, rebuilds changed lanes and persists the exact request before
measurement. Parameter-only edits retain other lanes and other bands.

## Tables

`wbquant_table_rows` is the authoritative grouped Signal matrix for UI and CSV.
CSV headers: 组序、组名、条带、泳道 1 ...; group ordinal is 第 1 组.
Every included Signal is ordered vertically, including finite measurements carrying
warnings, matching old export semantics. Such values do not become `valid` values
for normalization. Stale, failed, cancelled or mismatched run assets stay blank.
Numbers are formatted to two decimals at CSV/display export, not rounded in storage.
CSV formula-like labels use the repository's reversible `text:` protection.

Excel's 灰度分析 sheet follows the old two-text-column layout: group name in column A,
label in B, numbers from C; per-group headers, A-column merges and one spacer row;
freeze A/B only (`C1`), numeric `0.00`. Audit details remain separate, including
individual band statuses and detector warnings. Existing detailed exports remain.
Automatic output additionally includes `gray_analysis.xlsx` and `.csv`; publishing
never overwrites inputs or completed outputs.

## Evidence / limits

Independent original-package outputs for five synthetic cases are frozen in
`tests/fixtures/wbquant143.json`: single peak, double peak, black frame, flat image,
16-bit weak signal. Tests compare effective ROI, boundaries, baseline and integrated
Signal, with abs 1e-10 / rel 1e-12 (float64 rounding tolerance, not biological accuracy).
Both specified real RGB8 originals were also compared to the original package's
`quantify_lane` at identical ROIs: all 8 Signals match within 1e-10. The original
`quantify_image` rejects the 1px unequal-width grid; cross-lane numerical behavior is
covered separately by equal-width synthetic cases using its complete image entry.
No broad detection accuracy or biological normalization claim follows from these cases.

## Fig display-order follow-up

`ordered_quant_rows(project)` is shared by grouped tables and host snapshots. It
follows figure_order, then each source row's first composition (line, position),
with original rows order as fallback. A wrapped/split source row appears once;
actual displayed segments still require explicit manifest mappings in the UI.

Automatic crop recalculation preserves a valid existing composition and column
positions. A single full-row segment can update its last_lane when N changes,
with `layout_target_row_lane_count_updated_other_rows_preserved` provenance. An
invalid multi-segment configuration fails explicitly and leaves the passed immutable
project untouched; no other row is reset. During import only this structural check
permits not-yet-located rows. Normal rendering still requires valid original ROIs.
