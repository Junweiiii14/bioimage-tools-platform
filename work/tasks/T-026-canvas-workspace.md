# T-026 Canvas workspace subtask

Status: implemented; pending parent integration and independent review.

Scope: source-stage left source/actions, middle editable image, right review; original-pixel crop move/resize, zoom and pan; automatic host action signals. Advanced metadata table remains available. User explicitly authorized parallel worktrees and agents. No numerical algorithm change.

Changes: existing crop move/resize emits original-pixel half-open coordinates at release. Live preview retains lane count; blank image events do nothing; unchanged clicks do not invalidate results. Wheel zoom and middle-button pan are display-only. Existing manual first-draw legacy layout behavior remains; resizing a previously saved crop can enable independent row-height layout.

Validation (Windows/Python 3.12/locked shared environment, local source PYTHONPATH): 19 source/workflow/evidence/laboratory Qt tests passed in 22.75s. Legacy figure/single-window suite initially 16 passed and one failure from first-draw promotion causing stale composition after N edits; fixed promotion to existing saved crops only; failing test passes 1.80s. Final combined run below. Ruff and strict pyright targeted checks pass (pyright extraPaths used to avoid shared environment installed source path). Impeccable detector [] (native Python not web markup). Actual Qt screenshots at .local/t024-canvas/source-{1440,1100}.png inspected, no horizontal clipping. Screenshots use explicitly synthetic test fixtures and do not prove scientific accuracy.

Test expectation updates: old table visible by default assertion replaced with visible source list plus reachable advanced table; old left-only parameter position replaced with left-source/center-image/right-review geometry. No numerical expectation or tolerance weakened. New mouse-mapping checks allow 1 original pixel due integer device-point rounding; source clamp has exact equality.

Parent integration: connect automatic_requested, automatic_export_requested, import_directory_requested; disable full view while busy. Preserve schema8 automatic_rows after project reconstruction when core helper lands, and display machine/human statuses separately. Full repository gates and independent commit-bound review delegated to parent.
Final combined source/workflow/evidence/laboratory/figure/single-window run: 36 passed in 41.03s; exit 0. Final targeted Ruff, strict pyright and git diff --check exit 0. Full gates not run in subtask.

协调收拢：已集成产品16f3877；T-024全门禁532通过，独立绑定审查通过。子任务本地交付完成，后续用户试用/PR集成由T-024统一跟踪。


## T-043 历史回执真实重载

原回执提交16f38777d8bf8262b429e4004413937dd55b0195的规则指纹不匹配（Head rules changed or nested rules were omitted; reload context）。旧 Git 版本保留；本次按当前阶段规则重新加载，仍使用原记录基线与范围，不将旧记录记为通过。
