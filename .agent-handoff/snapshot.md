# Handoff Snapshot

- 更新：2026-10-14。用户授权继续完成WB自动化软件，Goal active，无token预算；阶段自验不能标整体完成。
- 活动仓库bioimage-tools-platform，分支feat/T-014-project-measurements；产品提交79a675a（base5bea9d3），最后HEAD见git log。T-014保持implementing，任务是唯一状态源。未推送、PR、集成main或发布。
- 最新用户说明已落盘：CLX是特殊设备原图且忽略；其他设备TIFF原图，裁剪产物TIF。继续接受.tif/.tiff，保留明确选源/SHA/ROI；不按扩展或_0/_1数字后缀猜具体定量用途。CLX不再作为待决/阻塞/开发项。
- wb-tool0.11.0/app0.6.0已接通项目多源定量第一阶段：固定N/空位/一target标注，原图曲线、暗亮极性、明确闭区间和人工或端点基线，逐行真实进程、已提交结果、自动项目表/XLSX、保存重开。标注初始bounds=None，裁剪范围不自动等于积分边界。
- WBAnalysisProject为独立wb_figure_project schema v3，保存计划及终态RunRecord引用，保留v2建议；v1/v2继续读，旧单图文档不变。原图/ROI/N/空位/审核/统一高度改变使计划stale；参数编辑清除当前run；名称/排序不改变测量。无新公式，显示/候选副本不进入定量。
- ProjectMeasurementSession复用RunSession PID/退出/提交流程，所有选中行绑定同一保存revision；结果严格核对资产大小/SHA/JSON/请求。重开逐条StorageCommand(run)核对工作区运行和资产，损坏或外来引用隔离到行。取消/关闭保留已完成行并自动保存，后到批次遇generation变化只留平台历史。
- 项目UI每页200泳道，曲线资产加载/缓存64 MiB，XLSX每表200000单元格。未加载/失败/缺失为空，真实0为数字0；来源表含row/lane/band/source/revision/run。单target限制、按需大项目曲线/流式导出、统一归档仍待改进。
- 最终完整门禁退出0：262测试（72.36s）、Ruff191文件、Pyright0、9导入合约、4wheel/5隔离场景。证据work/evidence/T-014/validation.md绑定产品commit79a675a；没有独立审查或用户最终验收。收尾修复刷新结果表丢失未保存基线的隐患并加真实Qt回归。旧Qt偶发Aborted根因UNKNOWN；本阶段未复现不等于修复。
- 下一步仍在T-014：把真实拼图OCR的Fig/行名原文、人工校正和项目row_id/source关联接入多源项目。复用现有OCR进程/模型/布局和工作表能力，重复蛋白名不自动匹配，结果表必须通过明确绑定填入；保存/重开/编辑失效/来源错误都须测试。需要新schema时明确v1/v2/v3兼容，不把单图OCR已有实现当成项目完成。
- 随后明确归一化参照行/样本映射/异常分母，再补批参数/元信息导入/缩略图、统一归档/ZIP导入/直接TIFF成图、模板精修。首版核对表work/wb-acceptance.md；多源OCR与自动写表是首版必需，不能降为可选。
- T-013候选@1仍是工程建议，真实10TIFF探针未有人工真值，真实行均未审核/应用。白背景膜不明、背景误检、Marker假设等风险保留；不按任务预期趋势调整信号。
- 私人资料/模型/探针留ignored .local/requirements-review。T014界面截图为合成样本，无用户原图数值被编造。真实OCR曾Fig1C→Fig1G高置信误读，必须复核。
- 开始下一轮先读根AGENTS/handoff/风险/待办/T-014和相关契约，再核对git并运行dev.py context记录。不要恢复归档项目；不要自行启动子代理。独审、真实最终工作流、包态/DPI/干净机/物理FAT和远程CI缺项继续追踪。
