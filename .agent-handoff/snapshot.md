# Handoff Snapshot

- 更新：2026-10-14；上位目标 T-003 持续开发 WB 软件；当前任务 work/tasks/T-006-workspace.md。
- 分支 feat/T-006-workspace，继承 feat/T-005-wb-worker (74e6561)；本阶段待提交，所有产品阶段独审尚未执行。
- 新增 tool_contracts/platform_runtime 0.1.0：不可变输入资产、草稿 CAS/历史、运行冻结、退出回执、唯一结果目录+SQLite CAS、重启 interrupted/quarantine/orphan 报告与一致性备份。平台不含 WB 字段。
- 最终完整检查164测试、7导入合约、schema漂移和三独立wheel通过。38工作区用例含3个真实宿主硬退出、同大小损坏、取消竞态、Windows junction/硬链接、真实WB worker→存储及备份恢复。证据 work/evidence/T-006/validation.md。
- wb_tool.api 0.4.0 与静态单任务 worker已实现。UI/Qt宿主存储线程及进程树强停尚未完成；退出回执须由实际OS观察产生，不以模型替代观察。
- 下一步：Qt宿主的存储队列/进程生命周期、手工ROI/曲线复核GUI、保存重开/导出；再自动候选/归一化/批次，最终产品验收/打包。
- 请求/结果仍为WB工具自己的不透明文档，GUI装配通过各package.api，不导入内部、不给工具数据库连接。
- T-001人工认可样本尚未冻结；真实TIFF5张仅输入烟测，私人摘要留.local；原图/旧参考/PDF不变。OCR优先可选问题未答，先候选，不永久排除OCR。
- T-002包态GUI/ROI/DPI/p95与干净Windows待办保留；PR#3未合并，新增产品PR未创建；不恢复归档项目。
