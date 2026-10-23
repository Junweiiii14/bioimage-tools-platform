# Installed diagnostics and E7 distribution v1

## Laboratory distribution (T079)

The mutually exclusive `--laboratory` build profile packages the same locked runtime
and four wheels. Identity `BioImageTools.WB.Laboratory`, channel `wb-laboratory`,
settings `BioImageTools/Laboratory`, executable `BioImageWB.exe`, per-user directory
`Programs/BioImage WB 实验室版` and mandatory desktop/Start-menu shortcuts are distinct
from the historical test channels. The window says `BioImage · WB 实验室版`.
Installer schema2 manifest identifies the exact source commit, lock, wheels and
runtime. This is a distribution identity, not a claim of universal-machine or
scientific acceptance. Product schemas, algorithms and existing settings remain unchanged.

Shipped `环境自检.cmd` runs Windows PowerShell 5.1 `selfcheck.ps1` using only the
private executable. It serially checks independent grayscale/OCR and the current
supervision workflow with unique reports under
`%LOCALAPPDATA%/BioImage-WB-Laboratory/Diagnostics`. It holds a real process handle,
requires exit0 and report phase `passed`, and reports a 180-second timeout as failure.
It never scans or terminates unrelated processes. Synthetic data and software
rendering diagnostics do not certify physical GPU/DPI/input or clean target Windows.
The installer has no blanket user-data deletion rule and performs no old-version
removal; the explicitly authorized local cleanup is a separate audited operation.

See T079 for actual build/install/uninstall/reinstall verification and limitations.

Normal application entry remains unchanged. Two explicit diagnostic switches accept a **new** report path and refuse overwrite:

- `--verify-installation <new-report.json>`: existing independent grayscale, real durable worker, offline OCR, failure/reopen/cancel and shutdown checks.
- `--verify-intake-installation <new-report.json>`: `intake_installed@1`, report schema1. Owned synthetic uint16 images in a temporary Chinese directory, confirmed stable Fig/row/slot mapping, explicit N=8/source-coordinate crop review, exact uint16 crop pixels, real worker commits, 16 result slots, complete output, reopen, new repeated export, imported archive evidence and output-only recovery, DOM/WebChannel and exact-owned shutdown. Flat inputs are expected not_detected with no measurement; the diagnostic never labels them valid zero. Source/report files outside its new owned outputs are not changed.

Reports are engineering evidence. Neither switch establishes scientific accuracy, actual instrument throughput, clean target-Windows or physical DPI/input acceptance. Exit0 requires all required checks and actual normal shutdown, not just creation of a report. Parent verification must additionally retain actual OS process exit and descendant evidence.

`python -m tooling.build_runtime_candidate --iscc <fixed compiler> --gcc <fixed compiler> --execution-test` builds the E7 candidate from a committed clean checkout. The existing command without this flag retains the T048 distribution and schema1 manifest. E7 manifest schema2 adds fixed distribution/channel/settings identity and a candidate-only acceptance statement. Four wheels, lock, private CPython, WebEngine/OCR/models, original qml/include exclusion and source/licenses are retained; no dependency upgrades or new pruning.

E7 identity: `BioImageTools.WB.E7Test`; channel `wb-execution-test`; settings `BioImageTools/E7Test`; current-user default directory `Programs/BioImage WB E7 测试版`; unique desktop/Start menu labels. It must not upgrade Platform/Candidate/Win10Test or the T047/T048 AppIds. E7 PS5.1 selfcheck runs both switches serially with isolated private interpreter/limited PATH and distinct reports in `BioImage-WB-E7-Test/Diagnostics`, propagating failure. Installer uses lowest privileges, x64 and Windows build17763 minimum; no file associations, external process termination or user-project deletion.

Actual build, installed workflow and target-machine acceptance live in T060 evidence. This contract describes implemented interfaces and does not itself claim the package has passed.

## Grouped intake candidate (T069)

`--verify-grouped-intake-installation <new-report.json>` reuses the real intake diagnostic with an explicit grouped branch, `grouped_intake_installed@1`. It saves an unknown-N/unselected-source draft without inventing executable rows, explicitly completes stable grouping and N=8, then runs the same original-pixel/worker/output/reopen/archive checks. A real Qt shortcut opens the shipped settings dialog, the normal WebChannel saves a custom binding, and a fresh preference reader must reload the exact saved map. Existing diagnostic flags retain their previous behavior. All inputs/settings are new owned temporary files; no user project is changed.

The mutually exclusive `--grouped-intake-test` build profile has identity `BioImageTools.WB.GroupedIntakeTest`, channel `wb-grouped-intake-test`, settings `BioImageTools/GroupedIntakeTest`, and default current-user directory `Programs/BioImage WB 采集组测试版`. Mandatory desktop/Start menu labels say 采集组测试版; prior installers/settings are separate. Schema2 manifest records this identity and candidate-only limitations. Its PS5.1 selfcheck serially runs independent grayscale/OCR and grouped diagnostics with distinct reports under `BioImage-WB-GroupedIntake-Test/Diagnostics` and propagates the actual process failure. Installation performs no old-version removal or user-data deletion. Actual source/installed checks are recorded in T069, not implied by this interface description.

Schema1 reports add optional `failed_phase` and `shortcut_probe` evidence. The grouped key check waits for the rendered page's matching project/epoch, idle state, focus and existing input/modal/IME guards before its single native key. Window-capture observations record the real event before production propagation guards. This does not relax the 120-second diagnostic limit, shortcut protection or exact persisted-binding checks.
