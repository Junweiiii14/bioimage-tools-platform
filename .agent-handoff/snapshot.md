# Handoff Snapshot

- 更新：2026-10-14；上位目标 T-003 持续开发完整WB软件；当前阶段 work/tasks/T-008-wb-desktop.md，review（手工闭环自验完成、独审待办）。
- 分支 feat/T-008-wb-desktop，继承 feat/T-007-qt-host (32a2bae)。所有产品阶段独审尚未执行，尚未集成main。
- 新增 tool_contracts/platform_runtime 0.1.0：不可变输入资产、草稿 CAS/历史、运行冻结、退出回执、唯一结果目录+SQLite CAS、重启 interrupted/quarantine/orphan 报告与一致性备份。平台不含 WB 字段。
- 最终完整检查164测试、7导入合约、schema漂移和三独立wheel通过。38工作区用例含3个真实宿主硬退出、同大小损坏、取消竞态、Windows junction/硬链接、真实WB worker→存储及备份恢复。证据 work/evidence/T-006/validation.md。
- wb_tool.api 0.5.0/core不加载Qt；WBDocument v1/sourceAssetRef/schema、显示专用DTO与可选Qt后台/ROI/条带/基线/曲线页面；bioimage_app中文窗口已装配，`uv run --locked --no-sync python -m bioimage_app`，静态`--worker wb`入口。真实UI拖选→signal10→存储重开、关闭自动保存、取消关闭与uint16显示独立已验证。192完整测试/9合约/4wheel5场景通过，末增延迟join反例Qt6tests通过。一回原生中止未独立重放，补线程非阻塞join后未复现，风险保留。
- 下一步T-009优先：拼图Fig/行名OCR、显式关联/人工修正与结果表自动写入（用户首版必需项）；核对旧参考与完整需求，选可本地验证的识别适配。自动候选、归一化、批次、导出、大图/缩放完善及产品打包验收均须完成，不能以手工GUI代替完整目标。
- 请求/结果仍为WB工具自己的不透明文档，GUI装配通过各package.api，不导入内部、不给工具数据库连接。
- 用户2026-10-14已回复：首版也必须包含拼图Fig/行名OCR与结果表自动写入，取消先前“候选优先/OCR可后置”假设。T-001人工认可样本尚未冻结；真实TIFF5张仅输入烟测，私人摘要留.local；原图/旧参考/PDF不变。
- T-002包态GUI/ROI/DPI/p95与干净Windows待办保留；PR#3未合并，新增产品PR未创建；不恢复归档项目。
