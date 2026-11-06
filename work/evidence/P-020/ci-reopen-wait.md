# P020 Windows CI 重开等待条件

候选 `c9a4d4247242c7212a28b6653ca5cba7c292cdc8` 已独审通过，但 quality run `42201070743` 的 Windows job `127836836339` 首次失败：1 failed / 1766 passed / 10 warnings / 1196.93s。唯一失败为 `test_prepare_workflow_saves_reopens_and_returns_to_editing_without_processing` 第162行，重开时读到了空的新 WBFigureProject。Linux同候选1763 passed / 4既有skip / 10 warnings / 945.44s及后续完整wheel通过；Windows失败没有被视作全量成功。

## 根因与有界复现

`WebWorkbenchWindow._backend_closed` 现有顺序：replace_host使epoch增加；创建空host、设置idle和home路由；发布“尚未打开项目”；之后QTimer.singleShot(0, continuation)才调用open_project，进入opening，再加载原项目并回到idle。旧测试只等epoch增加和idle，会命中中间空窗。该时刻界面没有宣告项目打开/保存成功。

- 原失败测试独跑：1 passed / 5.23s，仅说明不是每次触发，未据此判作可忽略。
- 本地探针只对 `_backend_closed` 排入的0ms continuation延迟250ms，旧测试稳定失败：1 failed / 3.31s，错误同CI；未改生产文件。
- 捕获实际 `sessionStateChanged`，在旧等待提前返回后继续等待真实完成：1 passed / 3.25s，5个pending步骤和原项目恢复。顺序为：shutdown/原workspace/已保存 → idle/epoch1/空workspace/尚未打开项目/home → opening/空workspace/处理中 → idle/同workspace/同projectId/已保存/intake。此定位区分了状态机空闲与特定打开请求完成，没有用测试等待掩盖提前成功。

## 最小修正与验证

仅该测试的waitUntil增加 `window.host.workspace_path == workspace`，保留epoch增加、idle、20秒超时和所有原类型、步骤、无处理结果及snapshot断言。无生产语义、算法、数据、门禁、skip或容差变化。上游明确授权该修正并要求准确增量独审。

相同250ms探针在新条件下没有提前返回；加原测试与全部 `tests/test_project_navigation_session.py`，exit0，**15 passed / 12.56s**。日志 `.local/p020-reopen-after.log`；原失败/状态序列日志 `.local/p020-reopen-before.log`、`.local/p020-reopen-lifecycle.log`。探针脚本 `.local/p020_reopen_probe.py` 和最新状态序列 `.local/p020-reopen-lifecycle.json` 保留本机；序列文件记录最后一次修正后执行（premature_old_wait=false），不冒充旧轮产物。

本轮Ruff check/format、Pyright均exit0，无类型忽略。已有生产内容与c9a4d42完全一致，当前测试增量仍需指定复审和新候选必需CI；不盲目重跑旧候选，不降低检查条件。科学/真人/安装未验边界保持。
