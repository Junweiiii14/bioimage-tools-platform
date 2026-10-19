# E7 initial live-code risk review

Non-author /root/independent_review; head ea7ed55b5d67cac8d2070b3e4d4e6472433db6b1, cumulative implementation base536f04e. Read-only review, no Qt/pytest in parallel with E6 gate.

P2 OPEN: late committed OCR decode/installation after cancel or close can replace current association. project_ocr.py _read_result.decoded emits succeeded without cancelled check; figure_window.py _start_ocr completion/installed compare generation only, set_project before save. A queued installer and a failed or in-flight save require separate guards beyond session cancellation. Reviewer reproduced both late decode success and post-cancel installer scheduling using frozen-method AST/fake-port probes (exit0); these are not real Qt verification. T060 adds actual Qt and durable-run boundary regressions before fixing.

Desired result: retain real succeeded run in immutable audit history, suppress cancelled/closing/stale association installation; protected CAS transform installs candidate only after save, failed save retains prior association, in-flight committed candidate remains historical and current draft remains old/unsaved as applicable. A later explicit retry remains available.

Actual additional paths reviewed: original TIFF load/analyze_annotations/read_project_result/tables; PID persisted before worker and actual OS receipt before terminal commit; schema14 frozen input/run/index/CAS; archive reader/restore path and content mapping; host shutdown; independent OCR/legacy routes; literal CSV/XLSX. No additional P0-P2 reported in those sampled paths. Scope is source risk review, not all code proof or installation/server/target/scientific acceptance. Historical native UNKNOWN remains.
