# 当前恢复指针

目标active、无预算：实际产品树bioimage-v0完成4.0 M1通用执行及M2真实可视编排。P008已正常集成，当前任务唯一来源work/tasks/P-009-visual-workflow-authoring.md，in_progress。M2尚未完成，不mark goal complete。

## 工作区与当前指针

- 显式workdir C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-v0；默认app cwd是旧规划树，不在旧树改产品。
- 当前分支codex/p009-visual-workflow，从main275560475d39426434416c74feeb0c2f259d1402开始；先核HEAD/dirty。B012 untracked属于另一规划聊天，保留、不stage、不覆盖。没有活动本机测试/CI观察脚本/P009审查。
- P009 task已激活，scope . context回执绑定main2755604；.local/p009-context.txt全部707行已实际读取。普通任务/交接/head变化不重载，main/规则/范围变化再真实加载。
- P001/P002/P003/P005/P006/P007/P008已done不重做；P004几何方法独立planned，不阻塞原整数图M1/M2。

## P008准确完成

PR53最终b4847a56b682e71356129e34fac59262c08659e7非作者Accepted，全4d6..b484；四必需CI SUCCESS后2026-11-02T12:27:06Z正常merge2755604。main与候选tree同98754bddc520b38bdaa8f5c7ce2c5882d9fc4f04。

最终quality41441375415：Windows job125263795311，1675passed10warnings1306.50秒；Linux job125263795009，1671passed4既有skip10warnings930.49秒。双侧全部隔离wheel含真实批量4000/40、6run、重开、样式/模板第二批；desktop/rulescontext SUCCESS，native-case预期SKIPPED。原日志.local/p008-ci-{windows,linux}-b4847a5.log，integration.json已记录SHA及精确提交。

旧53892fd Windows25m job取消（1675test/wheel/checkstep虽成功但不是CI通过）、0c33 Windows旧advanced夹具1failed1674pass均保留；Windows总时限仅25→30/Linux20，夹具仅真实保存手工注入的并发修订+等待原20秒budget内idle+assertsaved三行，独立复现/独审Accepted，无断言/预期弱化。不要重跑这些旧任务/CI。

## P009当前实际内容

- 首版后台/原生桥/Web编排已连接同一P008执行器，源文件workflow_authoring_{models,store,session,bridge}.py及web_ui/workflow_authoring.js/.css；共享AsyncStorage单所有者，不复制运行器。
- 图/目录/步骤、增删替换/连线、schema参数表单/高级JSON、保存/运行、暂停继续取消、已核验表图已实现。完整行为矩阵仍未验，不能从控件存在宣称完成。
- 最新四文件定向11passed47.73秒/exit0，日志.local/p009-authoring-connected-targeted.log；真实WebChannel两批4000.0→40.0且保存保留ROI输入DOM/焦点。store/session覆盖CAS/不完整草稿、缓存、冻结前取消/关闭无worker、提交中间结果、暂停冷重开显式继续、原生两个所有者退出排空。
- 模板workflow_template.py新增template_version1封装definition+layout；GUI导出/GUI及CLI加载器接受新旧格式。模板跨项目绑定新原图并保留位置已定向验证，新封装实际CLI进程及GUI模板新建第二批已通过，见ui-edit-validation.md。
- 失败记录/当前源码与日志摘要见work/evidence/P-009/connected-editor-progress.md及json。初始Web固定成果数、schema元组prefixItems漏实现、第二批回执未替换当前graph、精确40字符串应为40.0均已区分保留。目标Ruff/pyright/web静态通过；不是全产品类型/性能证明。
- 旧图探针仍只组件证据；最终视觉主检尚未开始，无新依赖、无P009 PR/独审/CI，不mark goal complete。

- 新增真实Web五流程最新5passed39.93秒，覆盖完整节点增删替换/错误连线解释/重开、布尔false和空数组恢复、模拟IME、GUI导出模板/另一TIFF新建+CLI启动、GUI缓存(3,0)/(0,3)/(1,2)/(2,1)及运行中新草稿焦点。来源/失败历史见P009/ui-edit-validation.md及json。最终type/Ruff/web静态通过。
- 视觉有效采集已开始：offscreen纯色、Windows readback滞后及静态RAF超时均保留。最新原生windows/--disable-gpu/active、capture-only关闭动画+500ms交付、图片非纯色及按钮像素对计算颜色核对12图通过15.42秒；.local/p009-ui-main-windows-active与.impeccable/review有效，其他目录不能作最终证据。仅首轮有效截图，仍待独立视觉审查，最多一次有效确认；无生产GPU配置修改或科学/物理DPI结论。
- 一次UI detect已运行，.local/p009-ui-detect.json只有1 backdrop advisory/0主要项，禁止再跑detector。中文操作单和模板v1兼容契约已写，不再重复建文档。

## 设计上下文与后继

本会话impeccable context一次已跑，.local/p009-ui-context.txt506行已完整实际读（含后补200–350），PRODUCT/DESIGN均为沿用T075四主题、本地NotoSansSC、40px控件的Operate扩展。已实际surface-brief read module_compare.js和craft-floor；新局部brief.impeccable/surfaces/workflow-authoring.md，不改全局DESIGN。用户已有明确授权，不按技能通用模板重问已定需求/审批。图探针截图只功能证据，不是最终视觉主检；最终完整UI一次主检+最多一次确认，detect在完成UI后一次，视觉独审按skill要求在最终候选集中做。

下一步：按impeccable既有Operate扩展范围用有效12图做fresh独立视觉审查，依据其问题一批修正/最多一次有效确认，不能重新开不必要设计采访/seed选型。保持原主题。P006口径性能（5预热+30正式，准确反馈/settled/原生ack/排空分开、超线保留）尚未做；再隔离wheel、准确提交独立代码审查/PR必需CI正常合并。无需重做完整功能矩阵或重复本地全量。根目标仍active。

P009当前只是本地工作提交，不建小步PR/逐提交审查；可运行完整候选后集中独审，局部验证/最终CI全量，不重复本机1675全套。已有独审/root/p002_independent_review可复用最终代码审查，当前idle。保留task/规则回执、P008closeout及轮转archive一起提交，别漏新未跟踪源码或误收B012。

## 外部与科学边界

另一规划聊天准备B012数据判断/参数适配/人工纠正，尚未通知最终同步；只保留其work/evidence/B-012和任务卡，不据预告猜科学阈值或扩算法。收到最终指引再核对已授权M1/M2。

科学留出/S1、用户体验、干净Windows/物理DPI/GPU/T002-P0及历史native UNKNOWN见risks/backlog，不阻塞无依赖工程。原图/历史结果/旧dirty树/在用安装不覆盖；不扩安装器正式发布或替换、其他实验全套、Agent、外联、花费或数据上传。
