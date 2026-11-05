# P-015 StarDist独立核分割研究适配器

<!-- PROGRAM_TASK_META {"id":"P-015","status":"done","work_package":"W07","depends_on":["P-014"],"execution_root":"C:\\Users\\70236\\ResearchVault\\Codex-Workbench\\bioimage-plan-sync","owner":"Codex nuclei adapter","base_commit":"07838c293390b0ce209b9c1500d49d734bc393a6","head_commit":"8f00757a966d5ff7c9f9237dbfe39471d3c9719b"} -->

## 授权与边界

2026-11-06上游在收到P014正式验收后明确派发，用户持续推进/独立审查/回传授权沿用。P014 goal已关闭、新goal已创建且无预算；P014收尾b6cc389保留。已查任务/registry无重复P015，分支codex/p015-nuclei-research-adapter。原dirty树、GUI、原图、历史结果和安装不碰。

本轮只实现固定StarDist研究适配入口，不重写分割、不训练/调参、不建新执行引擎或插件框架、不做整套GUI。复用WorkflowSession/RunSession/AsyncStorage的现有取消、退出确认和结果发布。研究候选不等于正式方法科学准入。

## 实施落点

- 独立`tools/nuclei`包，外部只用`nuclei_tool.api`；参数/结果纯定义、用例、图像与模型I/O/worker适配分开，领域无Qt/数据库/进程/I/O。
- 明确的宿主注册和CLI调用既有WorkflowSession，模型/预处理由工具负责，平台不含核分割特判；不改变WB行为。
- TensorFlow仅独立固定worker环境，轻量工具导入不加载模型/联网；权重缺失或摘要错误显式失败，不偷偷下载。使用P014固定StarDist0.9.2、权重成员摘要、scale0.5、3/99.8百分位、CPU线程4/1、2x2 tiles与默认概率/NMS阈值。
- 新包同步workspace、边界/import-linter与独立wheel安装验证；依赖/锁变更解释，不放宽现有门禁。

## 完成条件

1. 输入明确仅2D单通道uint8，其他位深/通道拒绝，不静默转8bit或猜通道。公开复制灰度RGB原图若用于工程对照，须先显式说明如何生成无损单通道回归资产，不能扩大接口准入。
2. 输出原图坐标整型标签、核数、输入/方法/模型/前处理/尺度摘要及状态；合法零核与失败区分，所有资产可追溯，不覆盖原图或已完成结果。
3. 模型在独立CPU进程真实运行，与P014冻结直接调用对照；验证标签实际坐标映射而非仅shape相同。已见数据仅工程回归，不是新科学验证。
4. 取消/失败不发布部分成功，实际进程退出和资源收尾有证据；覆盖错误输入、缺失/坏摘要模型、合法空结果、原图保护和取消竞态。资源限制复用已有机制，大小/时间预算说明依据，不把预算当实测。
5. 一条可复现命令及短导航，明确固定环境准备、无隐式下载与研究状态；不扩IF强度、全细胞、统计、Agent或安装器发布，不上传私有数据/外联/花费。
6. 绑定准确产品候选只读独审、适当本地检查及必需双平台CI、正常PR集成。收尾向上游01a19bfd-f3ab-7502-86da-9f61953d1c8a（local）回传接口/运行/PR/main/边界与下一最小用户流程建议，自动接续；小收据随下一任务带入。

## 当前状态

P015已完成授权工程验收、独审、正常PR集成和正式上游回传。PR66 main a7612843e5216f0471b51be93bd3687f0b8dbc82，最终候选8f00757a966d5ff7c9f9237dbfe39471d3c9719b与main文件树一致；活动树合入实际main为528c821。后续收尾仅文档/交接，随下一正常任务带入。

完整交付与逐项核对见work/evidence/P-015/final-delivery.md、objective-audit.md。14真实Windows场景通过，9张已见公开灰度图逐像素/实例ID匹配P014，零核/缺模型/坏摘要/取消/16bit拒绝符合预期；原图SHA不变、观察后代进程均退出。默认桌面不含TF，隔离环境/模型显式准备；复用既有执行/提交，无新引擎和WB算法变更。

产品a490d2e、门禁测试95ecb02准确提交独审通过；signed TIFF、超长失败原因、venv入口解析三项已修复。新工具/宿主21项通过，4个新增传递负例；相关48项定向通过。首轮全量1717passed/4failed/exit1保留（旧契约正例数量与3项GPU画布超时）；原画布断言同CI设置定向3passed，不宣称物理GPU根因解决。最终本机完整check --all exit0、1728passed/全部wheel；最终quality42086151498 Windows1728passed、Linux1724passed+4既有skip，双平台完整check/wheel及desktop均成功；rules42086151033成功。optional native-case未运行。严格类型0errors/3研究源码缺失warnings，未降低检查。

正式验收已实际发送上游01a19bfd-f3ab-7502-86da-9f61953d1c8a（local），工具返回目标threadId且isError=false。用户要求由上游核对依赖后自动接续，不等待再次催促；下一任务编号/范围以正式派发为准。建议现有界面单图研究结果走查，仍不扩科学准入、整套GUI或发布。科学/训练重叠/患者/实验室/学生/16bit/Linux真实模型及旧目标环境缺项全部保留。
