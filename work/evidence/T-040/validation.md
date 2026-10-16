# T-040 real-data validation

Baseline c531238; product head f7a6651; Windows, locked Python3.12 environment.
Task is actual dataset execution and truthful scientific/UX validation, not a claim that automatic detection is solved.

## Evidence

- Pure API first pass frozen `.local/t040/first-automatic.json`; actual desktop first pass also saved with immutable output ZIP/project.
- Independent reference score1/8(12.5%); seven wrong N, Marker inclusion, missed or clipped tilted bands. No unknowns.
- Second phase explicitly reference-assisted:8 registered frames, NCC0.99786..0.99977, original/reference dtype consistent;
  all8 visual criteria pass. Quantitative lane rectangles use shared non-overlapping original integer x boundaries and per-lane y;
  no rectified/interpolated array enters measurement.
- Eight named presentation TIFFs published with no replacement,960high/1200Nwide, original dtype and provenance.
  Display-marker admission test rejects all8 as quantitative originals. Native exports reread equal original array slices;
  original/reference hashes unchanged.
- `.local/t040_finish.py` exit0: real desktop four Fig,48values, font asset, label composition, affine overview/lane mapping,
  group curves, workbook/CSV,4 labeled TIFFs, complete ZIP and screenshots. Inputs explicitly only `(1).tiff`.
- Independent profile audit confirms initial48values reproduce persisted automatic bounds/baselines;17 below half of full
  window. Global peak remains within bounds, but endpoints are incorrectly on slope/plateau. Thus not an Excel export bug.
- `.local/t040_supervise.py` exit0:48 revised observations use explicit complete isolated reference windows and linear endpoint
  baselines, exact WBQuant trapezoidal formula, retained quality and edit provenance. Independent full-window max error0.
  Initial exports and runs preserved; revised files use a new supervised subdirectory.
- Workbook XML reread:48numeric cells agree with current full-precision values within1e-7; ZIP inspector verifies8rows,
  analyses, display frames and standard style roundtrip. Source scalar/dtype identities remain original.
-33/48 rectangles contain exact lower rail0, all24actin show broad clipped platforms; no claim of restored linear abundance,
  reference historical Excel equality or normalization.15valid/33quality_review statuses preserved.

## Product checks

- T04188 targeted tests passed; subsequent complete-row affine frame guard31 targeted passed.
- Independent review identified P1: split segments could reuse whole-row frame under partial lane claims. ba6814f rejects
  any DisplayFrame not spanning1..N; original reproduction now passes. Final independent review throughf7a6651 no new findings.
- Web affine scale/rotation/out-of-range probe passed; Node syntax,Ruff,Pyright passed. Existing native manifest hash retained.
- Full `dev.py check --all` exit1; log `.local/t040/check-all.log`. Ruff,format,Pyright,9 import contracts passed; pytest printed600 passed in374.59s but parent returned1 before installed-wheels. Shutdown/exit cause UNKNOWN; full gate NOT passed. Isolated `python -m tooling.installed_wheels` separately passed exit0; log `.local/t040/installed-wheels.log`. This does not retroactively change fullcheck exit1.
- No package/dependency/threshold-test weakening; display policy explicit and old defaults unchanged.

## Boundaries / remaining

First automatic crop and peak/baseline planning are inadequate on this case. Reference-assisted and supervised results
are separated and do not raise automatic success. General deskew, periodic-slot inference and robust baseline work remain.
Private real images are not committed. No remote CI,PR/main or clean Windows/package acceptance in this task.

Actual saved desktop reopened: PID32064,visible=true,8rows; visually checked `.local/t040/opened-desktop.png`, four Fig groups and real source-mapped curves. Independent product review c531238..f7a6651 and independent eight-source/reference/48-cell audit completed; no private originals committed.
