# P-015 StarDist独立核分割研究适配器

<!-- PROGRAM_TASK_META {"id":"P-015","status":"in_progress","work_package":"W07","depends_on":["P-014"],"execution_root":"C:\\Users\\70236\\ResearchVault\\Codex-Workbench\\bioimage-plan-sync","owner":"Codex nuclei adapter","base_commit":"07838c293390b0ce209b9c1500d49d734bc393a6","head_commit":null} -->

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

已核分支/HEAD/clean状态，读取主计划成熟实现准则、module-map、现有契约与宿主执行接口。确定WorkflowHostModule显式注册可复用现有WorkflowSession，不新增执行引擎。规则回执已实际加载并读取，P015集成清单保留P014的b6cc389历史回执且祖先核验成功。现有WorkflowHostModule/WorkflowLaunch支持明确worker命令与codec，无需改调度器；ProcessRunner要求轻量hello先于昂贵TensorFlow导入，取消沿既有进程树终止与RunSession提交仲裁。下一步读完精确协议/输出契约片段并实现最小工具包及单节点CLI。

尚无P015产品改动或验收，不借用P014研究结果声称适配器已经完成。科学、学生、16bit、训练来源未知继续保留。
