# T081 R2 actual delivery independent artifact review

Exact HEAD: f1e6142ab41e16c66cfeb3d33958ab3a364581b1
Verdict: Accepted
Reviewer: /root/explain_crop_gates
Reviewer is artifact implementer: false
Review completed: 2026-10-24, Asia/Shanghai

This acceptance binds the actual R2 stage and ZIP below. The reviewer did not author or run the build, installer, payload checker, staging or publisher. The reviewer previously contributed the stronger ignored actual-restoration test; its exact bytes were independently accepted by /root/t080_final_review in helper-final-review.md. This review independently reads the resulting installed files, restored image pixels and delivered archives. It does not replace source review or claim that the reviewer authored none of the earlier T081 product work.

## Artifact identity

- Stage: C:/Users/70236/.codex/worktrees/wb-lab-installer/bioimage-tools-platform/.local/T081/package/r2/staging-f1e6142ab41e
- ZIP: C:/Users/70236/.codex/worktrees/wb-lab-installer/bioimage-tools-platform/.local/T081/package/r2/WB-f1e6142ab41e.zip
- Archive SHA256: 8581bc080464a8300aeba1eaca8e7c270840d42ba4110c1ee09be295a28705db
- Archive size: 397078977 bytes.
- Stage: 201 regular files, 404489016 total file bytes; no symlink/reparse entries.
- Installer: BioImage-WB-Lab-Windows-x64-f1e6142ab41e-Setup.exe, 383952574 bytes.
- Installer SHA256: d4ff255ad422cc183b98c46dc39b6486035b9b79b4b438803d9baa46429c2d36
- Staging receipt SHA256: 189d3b5ba65743bbc895cae138a70f059e23c5ce309ec94ee2d4fcbdcbe3da0c

## Findings and evidence

No remaining blocking artifact finding was identified in this exact stage/ZIP. The R1 Blocked report and artifacts remain historical and are not relabeled by this decision.

1. Source and CI binding: actual worktree HEAD is the full commit above and tracked/untracked status is clean. The exact-head independent source report digest matches release-gate.json. All four named required checks are COMPLETED/SUCCESS, bound to this commit: desktop-environment, foundation (ubuntu-latest), foundation (windows-latest), and rules-context. Gate URLs identify PR43 runs 40005831584 and 40005831722. This review inspected the collected records, not a fresh remote CI execution.

2. Build and actual installation: build exit is 0; external/internal build manifests identify wb-laboratory, BioImageTools.WB.Laboratory, x86_64, CPython 3.12.14 and the exact source/uv.lock SHA. The actual installer log ends with installation succeeded and no reboot. Installation receipt records actual exit 0 into C:/Users/70236/AppData/Local/Programs/BioImage WB 实验室版. Both old and new retention sentinel files still match their before-install hashes. The installer in the stage, release output and actual-install receipt is byte-identical.

3. Installed bytes: independently rehashed all 7793 built payload files and the corresponding actual installed files, all 209 current source files recorded in the payload audit, and all 163 installed product/Qt modules observed by the acceptance run. Every hash agrees; module paths remain inside the installation and match the built payload. The installed isolated interpreter record reports pytest absent before development test-harness injection. No product code was imported from the development checkout in the recorded module audit.

4. Real selfchecks and installed acceptance: both fresh selfcheck diagnostic reports have passed status and no errors; their copied and live report hashes agree. The two modes cover offline OCR/worker/save/reopen and crop/gray/results/supervision workflows. Actual selfcheck process exit is 0. The installed acceptance process exit is 0; its JUnit contains 37 tests, 0 failures, 0 errors and 0 skips, elapsed 53.902 seconds (text log 53.91 seconds), with zero module-origin failures. Cases include folder drop validation, unreviewed visible table export, rotation, batch crop barrier, complete delivery restore, typed-image limits and actual 180 restoration. The log retains 10 deprecation warnings and two Chromium mailbox messages; they are not hidden or represented as zero diagnostic output.

5. Actual 180 restored content: independently read the saved restored draft and files without Qt. It retains workflow@5 and N [4,2,5,4]. All 27 TIFF sources match their recorded hashes and dimensions, all 9 TIFF raw crops exactly equal the specified original pixel rectangles, and all 4 Fig PNGs match recorded hashes/dimensions, pass PNG CRC verification, and fully decode as single-frame PNGs. The installed test observed 27 ready thumbnails and an unchanged source-delivery tree. The screenshot SHA is f322f5f0a8e7c9dc47d4890fede6bd7e0e6aad82abd8d18539091069e694f64c. Visual inspection shows the results page, 9 proteins/4 Fig, visible complete-project/complete-montage/gray-table controls, real populated values with missing cells kept as dashes, and the footer reporting 0 thumbnail failures. The yellow output-interrupted notice is the existing recovery contract requiring a new output destination; the user guide describes it. It is not evidence of a failed crop or a new successful export after restoration. This reviewer did not rerun Qt or the user algorithm.

6. Delivery ZIP and readable files: independently rehashed all 201 actual stage files and every uncompressed outer ZIP member; sizes/hashes and member set match the staging receipt exactly. ZIP CRC verification succeeds. There are no duplicate/case-colliding names, absolute paths, parent traversal, drive-qualified components or symlink members. The SHA256 file manifest and SHA256SUMS text list agree with their documented nonrecursive scope. Installer-check scripts contain the exact installer hash and propagate the PowerShell exit code. Maintenance receipts in the stage are byte-identical to the actual acceptance, gate, installation, payload, practice and selfcheck receipts.

7. Source archive and private-data separation: the source ZIP has 387 file members, each matching the exact commit's Git blob bytes, except the single explicitly eol=crlf path tooling/windows_test_selfcheck.cmd whose only change is the repository-mandated LF-to-CRLF conversion. No global newline normalization was used. Archive comment contains the exact HEAD. There are no ignored .local paths. Practice files match the installed acceptance's full practice tree; its 23-member recovery ZIP has exactly the two known synthetic source hashes 13e976733a7d6e6ac419aaea74afc4496ab9ff86d75b1801754adb5f39fa5a6a and ca8f44bf6708307ef4800d44c29b582f9a9d8762ab9be27da0027f8bdd61045f. None of the 27 private 180 source hashes occurs in staged files or nested practice archive content. The stage contains only the installer, tracked source/license material, bounded receipt metadata, user guides and the generated synthetic practice; actual-180 restored files/screenshots are not included.

8. Publication helper binding: publish_local.py SHA256 is 0bffb2dcc92eb89b4c843f33fe5204c02030999c188b94adb7fb26227a31453e, matching the final independent helper review. publish_expand.ps1 SHA256 is c6b9eb3b4c3f3c466b404f4be1250abdafd04cccc1f6d01d789d037cd04426f3. The publisher requires this exact archive hash and structured nonauthor review receipt before copy, creates fresh desktop paths, invokes system Windows PowerShell Expand-Archive, compares the extracted full tree and runs the extracted installer checksum check before writing delivered status. Those publication operations have not been executed by this reviewer and remain the next required step.

## Reviewer commands and evidence files

All commands ran in the wb-lab-installer worktree on the current Windows workstation. They were read-only against source, installations, original/private results and stage/archive inputs; only new ignored review/audit files were written. No Qt, test suite, install, extraction, publication, deletion, commit or tracked edit was performed by this review.

- `.venv/Scripts/python.exe -I -X utf8 .local/T081/package/r2/independent_artifact_audit.py`: first exit 1, preserved as independent-artifact-audit.log. The reviewer initially compared a Git-archived .cmd with raw LF Git blob bytes; the repository explicitly specifies eol=crlf. This was an inspection-method failure, not package pass evidence. It did not reveal a product mutation and did not change a product/test/build/CI gate.
- The same audit command after adding a narrowly scoped git check-attr eol=crlf check: exit 0, preserved as independent-artifact-audit-v2.log. All other source members still require exact Git blob hashes. Structured result: independent-artifact-audit.json, SHA256 d0b3ff73a6d9707d75145d36d6aa564de49f3930792eca035b16d16e09d6e085.
- A separate read-only manifest/sums inspection returned exit 0, confirmed 404489016 total stage bytes, exact textual checksums and the JUnit case list. Local screenshot was viewed directly.
- Installer/build/selfcheck/acceptance exit codes above are the actual author-run records inspected here; they are not reviewer executions.

## Limits retained

This is acceptance of a complete offline laboratory package for the declared Windows 10 1809+/Windows 11 x64 target and this verified workstation. It does not assert that every staff computer, clean Windows 10, physical Explorer/OLE, hardware DPI/GPU configuration, or independent scientific project has passed. The package guides explicitly retain these limits and first-install selfcheck/practice steps. The 80% independent-project scientific target has no held-out ground truth and remains unproven. Unsigned installer/unit IT handling and preservation of original data/history are stated in the guide. The unrelated historical native shutdown diagnosis remains UNKNOWN.

Accepted permits the parent to perform the already authorized fresh local desktop publication with the reviewed helper. It does not itself claim Windows-native ZIP extraction/publication has completed, merge PR43, authorize public upload, or remove old delivery/data.
