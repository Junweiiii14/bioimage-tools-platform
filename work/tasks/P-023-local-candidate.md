# P023 本机独立交付候选

<!-- PROGRAM_TASK_META {"id":"P-023","status":"in_progress","work_package":"W13","depends_on":["P-022"],"execution_root":"C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-plan-sync","owner":"chat-01a1b120-a7b5-77f0-a129-d782b3435b55","base_commit":"b13e71aa5aaebe91edecde44f386fc20ef693b19"} -->

2026-11-06 上游派发，起始干净 HEAD a6210780bddf49fc45c1037e61a7d4b174b92e07，保留 P022 一次收尾。

## 范围

复用既有私有 CPython、锁定 wheel 和原生启动器，准备独立目录候选，包含三工具、现有编排和可选工具设置。核 worker/模型复用固定已验证环境；提供准确源码版本、入口、配置和实际体量。不替换旧安装、快捷方式、关联、历史或用户设置；不公开发布、不签名、不下载大模型，不实现聊天卡片预览。

## 验收

隔离候选真实桌面入口（无开发 PYTHONPATH）：版本、三工具发现、各一合法公开/合成输入经真实 worker 到正式结果、关闭及冷重开；固定图模板入口和一次复用；重启设置及核环境缺项提示。仅验证交付新增风险，不重跑未变科学矩阵。保留 Linux 关闭 UNKNOWN 和科学/真人/干净 Windows 未验。

冻结准确 candidate/base、PR、候选路径及证据回传上游安排固定独审；通过独审及必需 CI 后正常合并，一次收尾释放共享树。本窗口不开始下一任务。
