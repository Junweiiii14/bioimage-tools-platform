# P002 → 4.0 M1/M2 交付核对

权威范围：docs/plans/phase-2-workflow-authoring.md、research-platform-rd.md第12.3/12.4及第4章；任务状态仍以各任务卡为准。本表不以“文件存在”推导功能或集成通过。当前P009候选64c02d9，PR/必需CI/合入尚待，不能宣告总目标完成。

| 要求 | 已检查证据与实际结果 | 当前结论 |
| --- | --- | --- |
| P002独立WB模块、准确提交独审、约定集成 | P002/review-final.md及integration.json：PR48候选a69b38e，非作者Accepted，双平台1537/1533测试及wheel，四必需CI成功，正常merge f2dc5ad，同tree | 原工程范围已完成；科学/现场不代签 |
| M1版本化ScientificAsset、端口、定义、计划及通用边界 | P007任务/review-final.md/integration.json：PR51正常merge006e9f1；tool_contracts.api与platform_runtime.api；test_workflow_contracts.py覆盖兼容/连接/冻结身份 | 已集成；不扩P004几何方法 |
| 实际输入→预检→WB分析→表/图发布；GUI/CLI共享执行器 | P008 PR53准确b4847a5及merge2755604；双平台全部wheel实际4000/40、6runs；P009实际QtWebChannel两批和模板GUI新TIFF＋独立CLI | 真实进程/持久成果，不是mock引擎 |
| 保存重开、非法图拒绝、缓存及提交后对账 | test_workflow_contracts.py；test_workflow_execution.py的serial、commit-before-association、cache及journal用例；P008准确独审/CI，P009单一存储所有者 | 既有契约保留；最终P009 CI还需通过 |
| 单样本失败隔离、非零失败不选为成果、原图/旧结果保护 | execution candidate/nonzero测试；P008批量证据；P009坏TIFF＋有效40.0真实GUI1passed9.48s，原输入字节不变 | 已定向验证，非科学准确率 |
| 模块目录、节点增删替换/连线、schema参数，重开保持 | test_graph_editing_preflight_and_saved_reopen在64c逐项保存重开add/wire、replacement、deletion；错误连线具体scientific_role原因；store用例实际错误unit拒绝freeze | 实际编辑而非只读预设图；无新增画布依赖 |
| 保存实验室模板、第二批真实输入自动出表图、新旧格式兼容 | template_version1及layout；test_gui_template_export_new_input_and_cli_share_definition；64c全部wheel exit0，installed AUTHORING_SCRIPT实际4000/40/6runs/布局模板CLI | 真实GUI/CLI链及当前候选安装验证完成 |
| 布局不重算、分析只失效依赖链、样式只发布 | test_gui_dependency_reuse_and_running_draft_survives_results真实新worker/缓存数(3,0)/(0,3)/(1,2)/(2,1)；store7runs缓存旧来源 | 已定向验证，不静默改变历史数值 |
| 中间成果、暂停/继续/取消、冷重开及退出排空 | authoring_session四项真实线程/进程测试；中间成果只来自已提交run；64c35轮控制PID/RunRecord和cancelled/closed，由独审复算 | 控制确认与安全边界/实际退出时间分别报告 |
| 后台不夺焦点/旧任务不覆盖新修订、表单边界 | 真实Web保存保留DOM/focus，运行中新草稿；false/空数组恢复和模拟composition用例 | 模拟IME已验，物理输入法/用户体验待验 |
| 成果只能取实际提交资产 | 26f独审P1真实9999反例；64c shared selection准入修复；同持久反例results/open拒绝，正常缓存原source身份通过 | 修复已独立复核；原失败报告保留 |
| 四主题、1440/960/窄窗及有界视觉独审 | visual-review.md/design-conformance.md/visual-confirmation.json；一批窄窗修正后原12图确认，scored fix ship | 仅该视觉修正通过，不代替性能/设备验收 |
| P006口径真实性能、原始数据/失败保留 | performance-final.md/json，两准确提交完整/受影响观测，5+30；26f所有node/preview及64cpreview/control分开 | 观测完成，普通点击超参考、高renderer内存原因UNKNOWN；不称预算全面达标 |
| 中文5–10分钟操作单和版本兼容说明 | docs/runbooks/workflow-authoring.md、docs/contracts/workflow-authoring-v1.md，步骤对应真实按钮/模板/执行链 | 已写；未经真实实验人员体验签收 |
| 最终准确独审、PR、全部已有门禁/隔离wheel、正常集成 | 准确2755604..64c非作者Accepted、当前全部wheel exit0；无P009 PR；本地不重复全pytest，最终双平台required CI运行check --all | PR/CI/合入尚未完成 |

独立留出S1、负责人判定、干净目标Windows、员工设备/物理DPI/GPU/实际用户体验仍待材料或现场条件；这些没有被工程通过关闭。未发布/替换在用安装器，未启动M3–M6、其他实验或Agent，未上传私有原图。已知性能限制必须随MVP交付，不通过改预算或删样本隐藏。
