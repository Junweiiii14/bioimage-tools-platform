# E7 source diagnostic and packaging preparation

Implemented profile not yet an accepted installed product. Existing builder default remains T048/schema1; explicit --execution-test uses separate fixed E7Test identity and schema2 manifest. No lock/dependency upgrade/new resource pruning. Existing qml/include exclusion unchanged. New CLI diagnostic/report v1 is additive and isolated.

- Source intake v1, actual0/8.031s, basic batch/reopen/export/DOM/shutdown. Expanded v2 also proves exact uint16 crop pixels, non-vacuous 8x2 missing-result semantics and archive imported history/output-only resume: actual0/8.796s, 14 required checks. .local/t060-intake-source-v{1,2}.{json,txt}. These are source/venv reports (isolated_imports=false), not package evidence.
- Existing report negative: CLI exit1/FileExistsError, SHA before/after identical; .local/t060-intake-existing-report.txt. No report overwrite.
- Initial new diagnostic type check found nonexistent source.filename; corrected to declared IntakeSource.original_name. Initial E501 lines formatted without changing checks. Focused Ruff/Pyright passed after correction; no ignores or test expectation changes.
- Source reports include WebEngine GPU/context stderr, retained alongside actual process exits; not treated as scientific/native-root proof.
- OCR fix original failures and successful regressions/review in ocr-validation.md. Actual build/installation, non-admin lifecycle, private runtime/module/descendant evidence and remote PR checks pending.

Distribution constructor isolation regression: four real WebWorkbenchWindows with test-only INI substitution verify Candidate/Win10Test/E7Test/Platform namespace selection without accessing user registry:4passed/3.13s/actual0; Ruff/Pyright0. PS parser0; actual installed PS5.1 execution remains pending.
