# T081 R2 independent source review

Exact HEAD: f1e6142ab41e16c66cfeb3d33958ab3a364581b1
Base: b59123e1eedabbb9f70bc4456e8ab74956aedd4a
Verdict: Accepted
Reviewer: /root/t080_final_review (did not implement this change)

Scope: seven files in Base..c3df3a5 plus four files in c3df3a5..Exact HEAD (overlapping paths; nine files total in Base..Exact HEAD), carrying forward the full T081 source review of 81d8d87 and its identical merged tree b59123e. Exact HEAD verified; tracked worktree clean. This is source acceptance, not R2 CI or package/install acceptance.

The R1 artifact review remains Blocked and preserved at ../r1-delivery-review.md. Its actual restored draft showed 18 auxiliary TIFF sources, 9 raw TIFF crops and 4 saved Fig PNG assets incorrectly named source.json. R1's 33 passing installed cases did not cover those role/readability assertions; the present review does not retroactively pass that delivery.

The minimal fix in archive_restore._assets obtains format from explicit persisted roles: WBIntakeProject sources and WBIntakeCropProject raw_crop are TIFF; WBIntakeFigureProject image is PNG. It does not infer types from untrusted filenames, expand arbitrary sniffing or alter scientific pixels. SHA/size validation still precedes classification; ordinary metadata retains JSON; original TIFF single-page/32MP/512MiB budgets remain. PNG now verifies format/CRC and 32MP/decoded512MiB bounds. The preliminary extra 64MiB Fig compressed-file restriction was removed: existing global512MiB member cap remains and the pre-existing OCR loader independently enforces its own constraints. This avoids an unrelated new acceptance limit.

Four new tests use genuine archive export/staging, verify source/crop dtype and pixels/SHA, saved Fig preview readability, metadata JSON and misleading filenames, and reject multi-page/oversized TIFF and oversized PNG. Existing tests and gates are not weakened. The user README addition correctly explains the separate documented active-export-to-interrupted restoration behavior and new-directory retry; it does not hide the R1 image-role failure. Task/handoff/rule receipt changes accurately identify the new baseline and pending release work.

Evidence inspected: work/evidence/T-081/restore-image-roles.md records initial4 failures; then30 passes including26 existing restore cases; after removal of the extra64MiB constraint the new4 tests passed in2.11s. Enhanced actual180 source-runtime reopening passed1 test/9.41s and asserts27 readable TIFF sources,9 pixel-identical raw crops,4 PNG paths,27 thumbnails and127 source-delivery file hashes unchanged. The ignored helper first failed collection because common was unavailable (exit2); the corrected wrapper result is distinct and the failure retained. These are author execution evidence, not a reviewer Qt rerun. Reviewer performed source/evidence/diff inspection only for this increment.

No remaining blocking source findings in the reviewed increment. Required CI for this exact HEAD, normal PR merge, R2 rebuild, actual install/selfchecks/payload/source/module verification, strengthened installed restoration and final artifact review remain pending. R1 artifacts/reports stay at their original paths; no prior artifact may be relabeled as R2.

The whole development set is not proof that80% of independent laboratory projects attain100% automatic correctness. Clean Win10/all staff hardware/physicalDPI and scientific holdout limitations continue. Screenshot static capture finishes animations and does not prove natural transition timing.

## Incremental exact-HEAD review: f1e6142

Prior report preserved unchanged as independent-review-c3df3a5.md. This report carries forward its typed-image restoration review and independently reviews c3df3a5..f1e6142. Exact full HEAD verified, worktree clean. Verdict remains Accepted for source.

Four changed files: one test, its evidence, task and handoff. git diff --exit-code c3df3a5..HEAD -- apps packages tools tooling returned0: no executable product, restore fix, dependency or build/CI gate change. Thus the prior restore source analysis remains applicable.

The test adds a bounded3000ms idle/not-operation_busy wait after pausing resumed autosave, then a fresh generation edit and explicit unsaved assertion before the second close. It preserves all original busy/cancel/draft/dirty state assertions, visibility, save decision and final resources_closed check, including original3000ms cancellation and20000ms shutdown deadlines. It neither accepts confirm_busy as confirm_dirty nor forces a product state. Waiting for ongoing work to finish and then establishing a dirty project is the correct prerequisite for this second dirty-close scenario.

Inspected controlled red/green JSON and log: original failed while a real table worker remained owned; fixed case releases worker via the event loop and closes with busy=false, unsaved=false, resources_closed=true. Author evidence records1 failed/2.62s exit1, then controlled case plus original and neighboring case3 passed/3.98s exit0. This confirms the missing prerequisite under controlled resumed work, not the exact request responsible for the historical CI failure. No new Qt/test execution by this reviewer.

Old c3df Windows CI1 failed/1294 passed is retained; its Linux success cannot replace that failure. Specific historical background activity and unrelated native/GPU issues remain UNKNOWN. New exact-HEAD required CI and R2 build/install/artifact acceptance are still pending. No new blocking findings, no tracked changes by reviewer, no commit made.
