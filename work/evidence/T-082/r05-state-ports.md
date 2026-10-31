# R05 显式状态端口

实施基线 `45106f9`；本文件记录未提交补丁的作者验证，准确提交及非作者审查由主任务补齐。规则回执 `rules-context.json` 的 `scope=.` 已重新运行并读取，内容不变。没有公式、原像素、持久化 schema、历史结果或导出格式变化。

## 三个切片

- **操作结果**：`FigureProjectWindow` 唯一写入 `_operation_failed` 与 `_operation_error`，对外提供只读 `operation_failed` / `operation_error`。开始操作经宿主方法清除旧结果，失败即使没有文字也明确为失败。工作台进入项目的两处判断与高级工具回执消费结果端口，不再从中文状态前缀或错误文字真值推断成功。保留原先 busy、内容、未保存与完整保存回执条件；已提交部分内容不会只因随后设置取消标志而被拒绝进入。
- **选择**：`FigureProjectView` 持有稳定 `_selected_row_id`，`select_row` 接受原生/网页选择意图，先提交有效控件编辑；未完成编辑拒绝切换并恢复旧选择投影。唯一安装方法投影到兼容表格，列表/下拉框只发意图。`selected_row`、`selected_row_id`、`selection_index`、快照与定量投影不读隐藏表格当前行。重排保留同项目、同 row_id、同 source；换源/跨项目清空。预览仍按当前源 SHA 拒绝迟到内容，显示副本不参与定量。
- **重新选址**：宿主保留明确 pending 标记及原先路径/模式数据，`can_retry_location` 同时考虑忙态、关闭与已有工作区。按钮显隐只投影可用性；网页调用宿主重试方法。取消系统目录选择保留待办；真正开始新尝试清除 pending。没有第二份重试参数或自动重试写入。

原生表格仍承载原有可编辑字段；本轮只搬迁选择权威，不声称已经移除全部原生控件。原生手动泳道选择等其他工具内部状态未扩展重构。

## 行为证据

环境：本机 Windows，锁定 Python 3.12.14 / PySide6 6.12.0；所有 Python 命令经 `uv run --locked --no-sync`。GUI 使用既有 CI 相同的进程局部 `QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu`。既有 mailbox 日志仍出现，未据此宣称 GPU 根因已修。

1. 新增 `tests/test_workbench_state_ports.py` 首批 7 项在旧产品运行：**7 failed / 3.83s / exit 1**，日志 `.local/T082/r05-red.txt`。其中 5 项直接暴露旧选择/状态文字/按钮显隐权威，另 2 项因尚无新端口而失败。修补后同批 **7 passed / 4.64s / exit 0**，日志 `r05-green.txt`。
2. 再加入空错误文字案例，先在只迁移字符串结果的补丁上运行 `-k failed_open`：**1 failed, 1 passed, 7 deselected / 3.01s / exit 1**，日志 `r05-empty-error-red.txt`。失败为空 message 被误认为成功；改为显式失败结果端口，并覆盖高级工具空错误回执。
3. 补齐桥接及定量投影在禁止读取 `table.currentRow` 时仍正确、旧源预览拒绝等后，10 项 **10 passed / 4.57s / exit 0**，日志 `r05-ports.txt`。
4. 受影响回归命令：`pytest tests/test_workbench_state_ports.py tests/test_web_bridge.py tests/test_quant_session_identity.py tests/test_project_navigation_session.py tests/test_workbench_lifecycle.py tests/test_workbench_advanced.py tests/test_figure_desktop.py tests/test_project_start.py tests/test_group_review_workbench.py -q --tb=short`，**61 passed / 45.03s / exit 0**，日志 `r05-regression.txt`。覆盖真实导入/重新选址/保存、已有取消及迟到、关闭、原生批次与网页高级回执。
5. 最后收紧 retry 的 busy / closing / workspace 可用条件并补忙态恢复断言，运行 `pytest tests/test_workbench_state_ports.py tests/test_project_start.py -q --tb=short`：**14 passed / 6.53s / exit 0**，日志 `r05-retry-availability.txt`。61 项回归发生在这次小补丁前，不能替代最终冻结集成门禁。

定向 Ruff / 严格 Pyright 已通过；初次测试文件 Optional 控件访问、私有探针及未注解 lambda 类型诊断已按真实控件断言、测试子类和明确函数修正，无 ignore / skip / xfail / 容差变化。已有测试预期及质量门禁均未削弱。

准确提交独立复核、R07 联合影响验证及最终冻结全门禁仍待主任务执行。
