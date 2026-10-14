# Handoff Snapshot

- 更新：2026-10-14；上位目标 T-003 持续开发至 WB 软件完成；当前任务 work/tasks/T-005-wb-worker.md。
- 分支 feat/T-005-wb-worker，继承 feat/T-004-wb-analysis (45d0c5f)；T-005 待提交，所有产品阶段独审尚未执行。
- wb_tool.api 0.4.0：TIFF/原始剖面/手工分析/严格协议；入口 python -m wb_tool.worker 限制数值线程。
- 已验证：123 测试、4 import-linter、schema 漂移及隔离 wheel 中真实 worker；signal 10、revision 7、错误源、合作取消/错误身份、旧/重复结果与损坏消息拒绝。证据 work/evidence/T-005/validation.md。
- 取消确认只是候选，宿主还须确认进程退出。worker 不写 SQLite/工作区，不宣告 host 终态；GUI/持久化/强停未完成。
- 下一步：真实宿主生命周期、工作区输入快照/结果发布与数据库恢复，再 GUI 复核；不可复制 P0 成品冒充产品。
- T-003 最终范围仍含自动候选、归一化、批次、导出、产品验收/打包。OCR 优先可选问题未答，按先候选顺序推进，不永久排除 OCR。
- 真实 TIFF 五张仅输入烟测，认可标注集未冻结；私人摘要 .local/wb-real-input.json，原图/旧参考/PDF 不变。
- T-002 包态 GUI/ROI/DPI/p95 及干净 Windows 待办保留；PR #3 未合并，新增产品 PR 未创建；不恢复归档项目。
