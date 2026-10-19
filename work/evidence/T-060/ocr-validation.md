# E7 OCR guarded installation validation (incremental)

Base5e3459a, source risk head ea7ed55. Actual Qt regression before fix: .local/t060-ocr-before.txt, 2failed/1passed/32.23s/exit1 (cancel-decode and close-decode replaced old association; edit-decode already blocked). Existing tests were not changed to manufacture this failure.

Fix: cancelled session cannot emit usable succeeded OCR while late read/decode finishes; host completion/preview/installer reject cancel/close/stale generation. Candidate installed through existing save(transform, install_guard) CAS, not before successful save. Failed save preserves old current association; queued CAS may commit immutable history, but cancellation suppresses its installation and leaves current draft unsaved. Loaded evidence updates only after accepted save. RunRecord OS receipts/history remain untouched. Generic guarded-save messages now name operation/draft rather than intake-only plan.

- New six decode/install × cancel/close/edit regressions: 6passed/55.84s/exit0 (.local/t060-ocr-late-after.txt), real Qt, actual OCR workers/OS exits/committed runs, real held background decode/installer, original source bytes unchanged. Closed/reopened stored draft retains previous OCR, succeeded late run retained.
- Six encode/queued-CAS-before-write/queued-CAS-after-write × cancel/close, plus save failure/explicit retry: 7passed/74.50s/exit0 (.local/t060-ocr-cas-after.txt). Before CAS queue, stopped encode publishes no candidate; after queue, historical committed candidate remains readable but current/latest-on-close retain old association. Failed save preserves prior visible state; explicit retry commits new OCR. Existing grace/timeouts not altered.
- Focused Ruff/types0. Initial new-test types rejected unknown base-model .ocr and protected field access; tests use narrowed public document and visible OCR pane instead of adding ignores or exposing internals. Assertions still verify exact prior run association and durable history, not text-only equality.

Original OCR/other save consumers, final full gate and non-author fix review are pending; E7 not complete. Candidate/remote work not yet accepted.
