# Handoff Snapshot

- 更新：2026-10-14；上位目标T-003完整WB软件；当前work/tasks/T-009-fig-ocr-table.md，implementing（后端自验完成、GUI/worker继续）。
- 分支feat/T-009-fig-ocr-table，继承feat/T-008-wb-desktop (34831e4)。所有产品阶段独审尚未执行，尚未集成main。
- 新增 tool_contracts/platform_runtime 0.1.0：不可变输入资产、草稿 CAS/历史、运行冻结、退出回执、唯一结果目录+SQLite CAS、重启 interrupted/quarantine/orphan 报告与一致性备份。平台不含 WB 字段。
- 最终完整检查164测试、7导入合约、schema漂移和三独立wheel通过。38工作区用例含3个真实宿主硬退出、同大小损坏、取消竞态、Windows junction/硬链接、真实WB worker→存储及备份恢复。证据 work/evidence/T-006/validation.md。
- wb_tool.api 0.5.0/core不加载Qt；WBDocument v1/sourceAssetRef/schema、显示专用DTO与可选Qt后台/ROI/条带/基线/曲线页面；bioimage_app中文窗口已装配，`uv run --locked --no-sync python -m bioimage_app`，静态`--worker wb`入口。真实UI拖选→signal10→存储重开、关闭自动保存、取消关闭与uint16显示独立已验证。192完整测试/9合约/4wheel5场景通过，末增延迟join反例Qt6tests通过。一回原生中止未独立重放，补线程非阻塞join后未复现，风险保留。
- T-009后端wb-tool0.6.0：RapidOCR3.9.2/PP-OCRv6与旧软件同三模型SHA；初始化前缺失/损坏守卫，CPU单线程，2048/256分块+原坐标/去重。Fig/行名未确认建议、显式绑定/有效signal写表、字面XLSX无覆盖导出已实现。199全量/9合约/4wheel5场景通过，安装产物真实离线OCR、socket禁网真实6标签与矩形解析写值、独立openpyxl读取均通过；不代表真实样本准确率。
- 下一步继续T-009：OCR专用worker协议/取消/宿主，Qt名称/位置/列与关系修正/确认、自动写表/导出，文档v2及旧v1兼容；跨图显式拼图关联必须完成。自动候选、归一化、批次、大图/缩放完善及产品打包验收也保留，不缩小目标。
- 请求/结果仍为WB工具自己的不透明文档，GUI装配通过各package.api，不导入内部、不给工具数据库连接。
- 用户2026-10-14已回复：首版也必须包含拼图Fig/行名OCR与结果表自动写入，取消先前“候选优先/OCR可后置”假设。T-001人工认可样本尚未冻结；真实TIFF5张仅输入烟测，私人摘要留.local；原图/旧参考/PDF不变。
- T-002包态GUI/ROI/DPI/p95与干净Windows待办保留；PR#3未合并，新增产品PR未创建；不恢复归档项目。
