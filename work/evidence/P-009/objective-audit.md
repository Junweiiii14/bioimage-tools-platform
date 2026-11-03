# P002 → 4.0 M1/M2 交付核对

权威范围：docs/plans/phase-2-workflow-authoring.md、research-platform-rd.md第12.3/12.4及第4章；任务状态仍以各任务卡为准。本表不以“文件存在”推导功能或集成通过。最终P009候选ba07dbaf229d1f7e9f12d337fbf5ddd1d441dc0f，准确独审Accepted、四必需CI成功，PR55已正常merge6e0dcd44ae726caffa9215da49bcf569737258cd。候选和main tree均5d8a8ee43d6f384f3a148a4326072a4b1db9c0e5；原目标工程交付完成，外部验收限制保留。

| 要求 | 已检查证据与实际结果 | 当前结论 |
| --- | --- | --- |
| P002独立WB模块、准确提交独审、约定集成 | P002/review-final.md及integration.json：PR48候选a69b38e，非作者Accepted，双平台1537/1533测试及wheel，四必需CI成功，正常merge f2dc5ad，同tree | 原工程范围已完成；科学/现场不代签 |
| M1版本化ScientificAsset、端口、定义、计划及通用边界 | P007任务/review-final.md/integration.json：PR51正常merge006e9f1；tool_contracts.api与platform_runtime.api；test_workflow_contracts.py覆盖兼容/连接/冻结身份 | 已集成；不扩P004几何方法 |
| 实际输入→预检→WB分析→表/图发布；GUI/CLI共享执行器 | P008 PR53准确b4847a5及merge2755604；双平台全部wheel实际4000/40、6runs；P009实际QtWebChannel两批和模板GUI新TIFF＋独立CLI | 真实进程/持久成果，不是mock引擎 |
| 保存重开、非法图拒绝、缓存及提交后对账 | test_workflow_contracts.py；test_workflow_execution.py的serial、commit-before-association、cache及journal用例；P008及最终P009准确独审/双平台全量CI | 既有契约保留，当前完整回归通过 |
| 单样本失败隔离、非零失败不选为成果、原图/旧结果保护 | execution candidate/nonzero测试；P008批量证据；P009坏TIFF＋有效40.0真实GUI1passed9.48s，原输入字节不变 | 已定向验证，非科学准确率 |
| 模块目录、节点增删替换/连线、schema参数，重开保持 | test_graph_editing_preflight_and_saved_reopen在64c逐项保存重开add/wire、replacement、deletion；错误连线具体scientific_role原因；store用例实际错误unit拒绝freeze | 实际编辑而非只读预设图；无新增画布依赖 |
| 保存实验室模板、第二批真实输入自动出表图、新旧格式兼容 | template_version1及layout；test_gui_template_export_new_input_and_cli_share_definition；最终ba两侧全部wheel exit0，installed AUTHORING_SCRIPT实际4000/40/6runs/布局模板CLI | 真实GUI/CLI链及准确集成候选安装验证完成 |
| 布局不重算、分析只失效依赖链、样式只发布 | test_gui_dependency_reuse_and_running_draft_survives_results真实新worker/缓存数(3,0)/(0,3)/(1,2)/(2,1)；store7runs缓存旧来源 | 已定向验证，不静默改变历史数值 |
| 中间成果、暂停/继续/取消、冷重开及退出排空 | authoring_session四项真实线程/进程测试；中间成果只来自已提交run；64c35轮控制PID/RunRecord和cancelled/closed，由独审复算 | 控制确认与安全边界/实际退出时间分别报告 |
| 后台不夺焦点/旧任务不覆盖新修订、表单边界 | 真实Web保存保留DOM/focus，运行中新草稿；false/空数组恢复和模拟composition用例 | 模拟IME已验，物理输入法/用户体验待验 |
| 成果只能取实际提交资产 | 26f独审P1真实9999反例；64c shared selection准入修复；同持久反例results/open拒绝，正常缓存原source身份通过 | 修复已独立复核；原失败报告保留 |
| 四主题、1440/960/窄窗及有界视觉独审 | visual-review.md/design-conformance.md/visual-confirmation.json；一批窄窗修正后原12图确认，scored fix ship；最终4个UI源文件及13份图/索引SHA仍吻合 | 仅该视觉修正通过，不代替性能/设备验收；没有第三轮 |
| P006口径真实性能、原始数据/失败保留 | performance-final.md/json，两准确提交完整/受影响观测，5+30；26f所有node/preview及64cpreview/control分开 | 观测完成，普通点击超参考、高renderer内存原因UNKNOWN；不称预算全面达标 |
| 中文5–10分钟操作单和版本兼容说明 | docs/runbooks/workflow-authoring.md、docs/contracts/workflow-authoring-v1.md，步骤对应真实按钮/模板/执行链 | 已写；未经真实实验人员体验签收 |
| 通用存储不依赖实验工具/数值库，固定受信装配 | 首轮5e导入契约失败已修，742c同一线程/未装配拒绝独立2pass；最终ba两侧9 import contracts及无WB的隔离app安装通过 | 原门禁保留，旧失败与修复分别记录 |
| 最终准确独审、PR、全部已有门禁/隔离wheel、正常集成 | review-ba07dba-final.md；quality41495774536/rules41495774934四必需SUCCESS；Win1692passed10warnings1399.58s、Linux1688passed4旧skip10warnings945.29s，全部wheel；PR55正常merge且同tree | 工程目标完成；原失败/取消不改写成通过 |

最终核验：P002/P007/P008合并提交均实际为候选祖先；P002/P008远端PR状态及merge SHA与本地收据吻合。主线与准确审查/CI候选tree相同，未产生未经审查的产品增量。`dev.py check --all`实际顺序为policy、Ruff/format、Pyright、导入契约、web门禁、全部pytest、全部隔离wheel；两个成功日志均读到了最后成功行和实际编排安装回执。integration.json及无损压缩原日志记录准确命令、环境、提交、退出码及SHA。28份性能文件、4个视觉源文件、13份图像/索引均重新核对摘要；测试源在视觉后强化，未混称旧截图涵盖新测试源码。

可运行入口为本检出的Start-BioImage.ps1，固定其自身目录和环境；工作台顶部“工作流编排”进入MVP。当前产品源码与已集成候选一致；合入后的任务/审计/交接收尾记录保存在本地，未再推纯状态变更重启CI，也未创建额外文档PR。

独立留出S1、负责人判定、干净目标Windows、员工设备/物理DPI/GPU/实际用户体验仍待材料或现场条件；这些没有被工程通过关闭。未发布/替换在用安装器，未启动M3–M6、其他实验或Agent，未上传私有原图。已知性能限制必须随MVP交付，不通过改预算或删样本隐藏。
