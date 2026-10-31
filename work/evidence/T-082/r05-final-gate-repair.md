# R05 最终集成门禁发现与修复

## 冻结门禁的真实结果

2026-10-28，本机 Win11、既有锁定依赖，干净提交 `44ee78c36a0edb5d6cd9bd0798bbca3e25edd4da` 执行 `uv run --locked --no-sync python dev.py check --all`，进程局部 `QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu`。结束时 HEAD 相同且工作树仍干净。

政策、Ruff、1014 文件格式、Pyright、导入边界、网页质量均通过；pytest **2 failed, 1499 passed, 10 warnings / 724.38s**，全命令 exit 1。后续独立 wheel 安装门禁未执行，不能把前半段通过当作完整通过。原始输出保存在 [final-check-44ee78c-failed.txt](final-check-44ee78c-failed.txt)，含原生 GPU/mailbox 警告；这些警告未被判定为失败原因或已修复。

## 两项具体原因

1. `tests/test_web_quant.py::test_anchored_snapshot_keeps_target_distinct_from_sampling_context` 的 `SimpleNamespace` 仍只提供旧 `selected_row()`，未提供 R05 已审的新 `selected_row_id`，因 AttributeError 在科学/ROI 断言前停止。只将该替身改为 `selected_row_id=row.row_id`；原 target/context/扩展比例断言不变，没有新增产品回退或容差。定向检查 **1 passed / 1.43s**，日志 `.local/T082/r05-final-gate-quant-fixture.txt`。
2. `tools/wb/tests/test_standard_display_ui.py::test_crop_edits_clear_only_changed_frame_and_undo_restores` 复现真实 R05 回归。历史步进无条件调用 `select_row`，即使目标已经选中，也会提前 `self._project=self.project()`，提交已变 ROI 并清除原 display frame；撤销原 ROI 随后又被视为新的几何变化。旧表格同一单元格不会发选择变化信号。修复仅在目标行身份不同的时候执行 `select_row`；完整目标行校验、无效编辑拒绝、跨行选择提交、历史游标和 finally 恢复保持。

第二项原测试独立重现 **1 failed / 2.84s**，修后原显示文件 **2 passed / 1.64s**；standard_display、ratio_crop、image_review、lifecycle、state_ports 五文件合计 **23 passed / 32.42s / exit 0**，日志 `.local/T082/r05-undo-frame-{red,green,regression}.txt`。Ruff、格式、Pyright、diff 检查通过。没有修改该测试的预期、skip/xfail、科学定义或历史数据格式。

## 复核与剩余验收

修复提交 `d1036c2bf40e7cac91c979e993d5053e148cb710` 独立复核 Accepted，4 定向测试及5组Qt临时反证通过，详见 [final-integration-review](final-integration-review.md)。仍需重新冻结完整门禁及真实构建安装。此次修复不宣称所有跨行或保存后的历史 frame 都可恢复：旧历史项只保存 ROI/N，跨行提交边界此前已存在；未借此扩写新历史框架。

跨版本升级将使用已审的旧源码 `244c5da1b03e47f6d17801912cb38003e8edab27` 构建同一可弃 acceptance 身份，再升级到通过门禁的最终源码。同包再装仅能称覆盖安装。此前新检出的 `44ee78c` 没有构建或安装，也没有通过本次完整门禁；最终验收须更新到实际修复提交。
