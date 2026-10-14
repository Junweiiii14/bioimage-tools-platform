# Handoff Snapshot

- 更新：2026-10-14。用户提供WB资料后明确继续，暂停已解除。Goal active，目标完整WB自动化软件；无token预算。不能因某阶段自验完成而标goal complete。
- 当前分支 feat/T-012-figure-project，base cfe0c56；T-012实施/作者自验完成，任务review待独审；最新commit查git log。T-013-crop-candidates.md ready。没有推送/PR/main集成。
- wb-tool0.9.0/app0.4.0：现有单图定量/ROI/曲线/基线、真实离线OCR/Fig行名复核/显式跨图工作表/XLSX/v1-v2重开、固定N网格/原值单框TIFF均保留。新T-012独立多原图项目文档和窗口：批量导入SHA去重、Fig/蛋白/N/空位/备注/行ROI与审核、排序/模板保存复用、后台PNG拼图及ZIP原图/原值TIFF/来源记录、工作区重开。入口原WB按钮或 --figure-project。
- 最新完整dev.py check --all退出0：230测试（63.06s）、Ruff170文件、Pyright0、9导入合约、4wheel5场景。新12用例覆盖真实Qt操作/关闭重开与模板复用、解析像素/无静默拉伸、重复标签/空位/缺图/审核、损坏/取消/无覆盖。详情work/evidence/T-012/validation.md。
- 另用用户项目10张真实TIFF实际批量导入/保存重开，10个不同SHA与外部原文件摘要前后相同。没有擅自选择仪器导出模式、确认蛋白身份或真实ROI；真实样本准确率尚未验收。
- T-012项目不是旧单图v2升级：独立wb_figure_project v1 / tool_id wb-figure。API延迟加载Pillow/Qt，锁文件只本地版本及对已锁Pillow的extra声明。旧v1/v2读取契约不变。当前一个行一个连续矩形，同Fig等宽/N、批次等高，PNG显示为BT.601/uint16整除257；原样本另存。项目级OCR/定量/归一化尚未接通，ZIP导入/直接TIFF成图/跨workspace模板库/横向分段仍缺。
- 下一步T-013：按规则/研究协议冻结膜/左Marker/固定N网格/候选条带行的自动建议与反例，接入当前项目复核；保存算法参数/建议快照、可切换/调整/恢复、保留空位。用户源类型未明时继续显式选图，不能按后缀/位深猜源或按任务单趋势优化检测。
- 首版完整验收矩阵work/wb-acceptance.md；持续补项目级OCR/自动表、灰度工具衔接/归一化、Excel/文件名元信息、批参数/缩略图、统一归档和产品打包。手工多图流程不是自动化目标完成。
- T-008/T-010偶发Qt native Aborted根因UNKNOWN。T-011四轮36探针未复现；入口本地Qt/Python日志和qFatal线程栈落盘已自验，不能称为修复。T-012全量没有复现。下次错误先读日志，不反复无假设压力重跑。
- 新资料/私人预览/OCR/真实项目探针/截图都留ignored .local/requirements-review，不提交私有材料。真实OCR曾Fig1C高置信误读Fig1G，短编号布局@2仍须人工复核。用户首版OCR/自动写表要求不降级。
- 待用户说明无后缀/_0/_1 TIFF及CLX的导出身份和定量来源。所有产品阶段独审未执行；真实标注/最终Windows包态交互/DPI/干净机/物理FAT及远程CI验收缺项保留。
- 下一轮先读根规则/此索引/风险/待办、T-013和目标API，再核对git并运行dev.py context。平台无WB字段、跨包只走api、原图/历史结果不可覆盖，不恢复已归档项目。
