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

- 按task先做有限画布探针；新增web_ui/workflow_graph.js/.css，原生DOM/SVG组件，对同一P007真实定义投影；布局与计算定义分离。
- 探针真实QtWebEngine focusProxy键盘Right发出move、Delete发delete，端口按钮发connect；定义JSON不变；3节点/2实际派生SVG路径；960×640无页面横溢，图内滚动。probe1passed2.26秒，后续几何记录轮退出0，npm check:web退出0（focusedTS仍只覆盖既有bridgepayload，不冒充全图类型证明）。
- 可复现probe work/evidence/P-009/graph_interaction_probe.py；范围/源码与logSHA见graph-probe.json；本机工件.local/p009-probe/。最初两次失败是probe键盘目标和JSobject读取序列化错误，组件源码未改，原失败log保留；offscreen/--disable-gpu仍有旧Qt/GLES诊断，不声称物理GPU通过。
- 只图组件/选择证据，**尚无完整编辑器、宿主命令/草稿保存、schema表单、编译预检回执、实际运行/结果定位连接**，不算M2。需要接同一WorkflowBatchSession/WorkflowSession，不能另造执行器或用预设动画代替。
- 原生DOM/SVG已够有限节点交互，暂不引新画布依赖。最终实际完整浏览器行为/主题/窄窗/IME/旧任务新草稿/取消排空/模板第二批/数值缓存及独审/PR/CI仍须做。

## 设计上下文与后继

本会话impeccable context一次已跑，.local/p009-ui-context.txt506行已完整实际读（含后补200–350），PRODUCT/DESIGN均为沿用T075四主题、本地NotoSansSC、40px控件的Operate扩展。已实际surface-brief read module_compare.js和craft-floor；新局部brief.impeccable/surfaces/workflow-authoring.md，不改全局DESIGN。用户已有明确授权，不按技能通用模板重问已定需求/审批。图探针截图只功能证据，不是最终视觉主检；最终完整UI一次主检+最多一次确认，detect在完成UI后一次，视觉独审按skill要求在最终候选集中做。

下一步：实现可编辑草稿及后台固定命令（沿旧Workspace opaque文档/CAS），同一确定性compile预检；实际目录/参数/连接投影接此图组件，保存/重开/模板绑定第二批，真实P008执行及核验成果链接。考虑存储单所有者，不在GUI线程导入/校验大图、编译环境或读表；UI事件不能覆盖更新草稿/焦点。代码按入口一次校验、内部信任类型、最窄I/O边界错误、无一次性抽象与臆测fallback。

P009当前只是本地工作提交，不建小步PR/逐提交审查；可运行完整候选后集中独审，局部验证/最终CI全量，不重复本机1675全套。已有独审/root/p002_independent_review可复用最终代码审查，当前idle。保留task/规则回执、P008closeout及轮转archive一起提交，别漏新未跟踪源码或误收B012。

## 外部与科学边界

另一规划聊天准备B012数据判断/参数适配/人工纠正，尚未通知最终同步；只保留其work/evidence/B-012和任务卡，不据预告猜科学阈值或扩算法。收到最终指引再核对已授权M1/M2。

科学留出/S1、用户体验、干净Windows/物理DPI/GPU/T002-P0及历史native UNKNOWN见risks/backlog，不阻塞无依赖工程。原图/历史结果/旧dirty树/在用安装不覆盖；不扩安装器正式发布或替换、其他实验全套、Agent、外联、花费或数据上传。
