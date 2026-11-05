# P-015 StarDist独立核分割研究适配器

<!-- PROGRAM_TASK_META {"id":"P-015","status":"in_progress","work_package":"W07","depends_on":["P-014"],"execution_root":"C:\\Users\\70236\\ResearchVault\\Codex-Workbench\\bioimage-plan-sync","owner":"Codex nuclei adapter","base_commit":"07838c293390b0ce209b9c1500d49d734bc393a6","head_commit":"9c9f81ed09466afdb86a8753192648a94d7111a9"} -->

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

独立nuclei_tool和显式nuclei_cli已接既有WorkflowSession，无平台/WB算法修改。固定隔离环境和模型快照、2D uint8 TIFF准入、原坐标uint32标签/核数/出处、失败原因/取消与提交结果已实现。workspace、边界、Import Linter、独立wheel检查入口和20项新增测试已补。

本机20项新增用例通过，严格类型0 errors/3个隔离研究源码缺失warnings（未忽略），11项导入契约通过。真实14场景第三轮（独审修复后）全部通过，9张原灰度图逐像素/实例ID匹配P014冻结结果；零核成功、缺模型/坏摘要失败、期限取消、16bit准入拒绝，原图SHA不变且观察到的子进程均退出。见work/evidence/P-015/real-regression.json；实际目录p015-research/regression-03不提交原图/模型。

初版Windows控制管道阻塞与NumPy native加载死锁，最小探针复现后改为非阻塞pipe；实际首次超时取消无发布，失败证据未当通过。新增开管道导入回归。私有模型快照归宿主临时目录，强退后沿既有清理；期限从输入准入后开始，预算不是性能保证。

全仓dev.py check --all正在执行（.local/p015-check-all.log）；尚待准确候选独审、必需CI/正常PR合入、收尾回传。用户再次明确自动推进意图已成功发送上游（isError=false），验收后由上游自动接续派发，不重复求批。科学、学生、16bit、训练来源未知继续保留。

首轮独审b1e348a发现两项实证问题（signed TIFF及超长失败原因），已修复并补真实反例，见independent-review.md；复审绑定新候选后才可验收。草稿PR66，rules-context首次成功；旧候选quality与本机全量仍在执行，不当新候选通过。

9c9f81e增量只读复审已通过，两项问题关闭；独立4项反例/正常路径回归通过及第三轮9份实际标签/摘要一致。当前只待全仓/最终CI与正常集成，非科学验收。
