# P020 等待条件增量独审：pass

2026-11-06，独审窗口 `01a1af0d-808e-7131-ae29-237aded27938`（local）。可将既有工程范围 pass 沿用至本准确候选；必需 CI 尚待，不表示当前可以合入。

- PR72：<https://github.com/Junweiiii14/bioimage-tools-platform/pull/72>
- Base：`1c819aeaae9813fdc29606cbad463b08a191fbab`
- 已审前候选：`c9a4d4247242c7212a28b6653ca5cba7c292cdc8`
- 本次候选：`0d83f4dc75804e90291d408302027fe590286fdf`
- 实际增量：测试等待条件及注释、3 个任务/证据文件；4 文件，30 行增加、1 行删除。
- 独立工作树：`C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-review-p020`，detached 准确 HEAD；使用自身 `.local/reviewer-venv`，未操作作者树、共享环境、旧安装或原始实验数据。

## 结论与根因

这是测试把“新宿主已空闲”误当“目标项目已打开”的等待条件缺陷。新增目标 workspace 身份约束是有效收紧，没有用等待掩盖产品提前宣告完成。

独立静态核对和受控 250ms 延迟复现一致：

1. `web_bridge.py:149–150` / `web_window.py:449–476` 替换宿主使 epoch 增加，清空宿主后发布 idle/home，再排入重开 continuation。
2. 此空窗实际为 `epoch=1, stage=idle, workspace='', project_type=WBFigureProject`；旧条件为 true，新条件为 false。实际 session 信号是“尚未打开项目”，没有宣称目标项目已保存或打开成功。
3. 排队 continuation 实际返回时为 opening、空 workspace、operation_busy=true。重开流程完成后才回到 idle、目标 workspace、原 projectId、已保存及 intake 路由。
4. 复原项目类型为 WBIntakeWorkflowProject，5 个步骤均 pending，没有 analyses/OCR/ROI 处理结果。对候选原测试本身施加同样延迟，原业务断言全部通过。

`tests/test_instrument_intake_desktop.py:158–170` 保留 epoch 增加、idle、20 秒 timeout、wait_saved、项目类型和 snapshot 断言，只增加目标 workspace 相等。结合 `web_window.py:710–756` 在内容存在、无错误且保存完成后才恢复 idle 的现有行为，该条件对本测试足够。

## 独立验证

环境：Windows / CPython 3.12.14，审查树独立 venv；`QT_QPA_PLATFORM=offscreen`，`QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu`。源文件及旧证据未改，只有 `.local` 审查探针与收据。

- 首轮命令：`uv run --locked --no-sync python -I -B -m pytest -q .local/p020-reopen-0d83f4d/test_reopen_boundary.py tests/test_instrument_intake_desktop.py::test_prepare_workflow_saves_reopens_and_returns_to_editing_without_processing tests/test_project_navigation_session.py -p no:cacheprovider --basetemp .local/p020-reopen-0d83f4d/tmp`。
- 首轮真实结果 **exit 1，1 failed / 15 passed / 15.24s**。唯一失败是审查者自写探针误要求每次 opening 都会产生 sessionStateChanged 信号；原条件提前返回的反例、完整恢复断言当时已通过，候选原测试（含延迟版本）和导航测试也通过。产品的定时信号可能合并短暂状态，不应把探针这一假设当产品契约。
- 只修正探针的观察点：在实际 continuation 返回后直接记录内部 stage，保留目标身份、恢复内容、无处理结果及 20 秒限制。未修改任何产品或仓库测试预期。初版脚本和失败说明分别保留为 `probe-initial.py`、`initial-probe-result.txt`。
- 对两项探针定向复跑，命令同上但仅 `.local/.../test_reopen_boundary.py`，新 basetemp 为 `tmp-refined`：**exit 0，2 passed / 4.16s**。没有无意义重跑已经通过的导航矩阵。
- 实际事件与准确实现路径见 `.local/p020-reopen-0d83f4d/boundary-events.json`；候选原测试在同样延迟下通过见 `exact-test.json`。短暂 opening 的证据来自实际调用返回，而非冒称定时发布信号曾出现。
- `python -m tooling.rule_context check --base 1c819ae… --head 0d83f4d…`：exit 0。
- `git diff --check c9a4d42… 0d83f4d…`：exit 0。
- 对 apps、tools、packages、依赖锁、.github、tooling、dev.py、.importlinter、.gitattributes、.agents 的同范围 `git diff --exit-code`：exit 0。生产实现、算法、科学语义和门禁相对已审候选完全无变更。
- 子审独立只读核对实际状态机与测试差异，未发现剩余实质问题；不将静态意见写成重复运行的测试。

## CI 与适用边界

旧 `c9a4d42` Windows CI 失败事实保留，不倒改为通过。新候选 PR head/base 已通过 `gh pr view 72` 独立核对；观察时 OPEN、非 draft，rules-context 和 desktop-environment SUCCESS，两项 foundation IN_PROGRESS，native-case SKIPPED。准确新候选必需 CI 通过前不得集成。

本次仅复审等待条件与相关会话回归。既有 `incremental-review-c9a4d42.md` 的工程通过范围及原始 UI/算法证据继续适用；科学/真人/OS IME/物理 DPI/目标机/安装及完整跨实验编排仍按既有未验边界记录。不重新审查未变的科学或视觉矩阵。

将本报告回传规划窗口，待准确候选 CI 完成后由规划按正常 PR 流程安排集成。审查者未合并、发布或改写作者实现；报告由上游一次归档，不要求纯收据再推产品提交。
