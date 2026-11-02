# 当前恢复指针

目标active、无预算：实际产品树bioimage-v0完成4.0 M1通用执行及M2真实可视编排。当前分支codex/p008-workflow-batch，最终产品HEAD53892fd9c99a7c175ae5f5b95bbc98032df1c1d5，main基线4d6ee6ce364780cad24ef09b808740846937714c；核对HEAD/dirty再接续。任务状态唯一来源为work/tasks/P-008-workflow-batch-recovery.md。

用户要求：入口一次校验，内部信任类型，不重复判空/滥用catch、不抽一次性函数、不写臆测容错；授权内连续推进，集中最终候选独审，不逐小提交审批。karpathy-guidelines已固定核验安装。用户本轮进一步追问全量测试必要性：已解释因共用运行/存储变化需最终防回归；本机/CI有重叠，后续本地先定向、最终候选CI做全量；纯文档/资源配置不额外本机全量，必需CI/断言保持。

## 已完成与保留证据

P002/P003/P005/P006/P007已正常集成，不重做。P005准确2258cd5非作者Accepted，PR52四必需CI全SUCCESS后正常merge4d6ee6c，tree同为4a50fc0738b61303c8d495cce03272845c7876e8。Windows1659pass1185.30秒/Linux1655pass4既有skip508.51秒，双侧全部隔离wheel及真实三节点/4000/重开/两步缓存通过。integration.json及runtime-review.md保留准确事实；首轮P2、旧本机F/GPU未知及旧Windows20分钟超时不销账。最终Windows总25分钟/Linux20，未改测试/断言/单测超时/必需门禁。

P004新几何方法仍独立planned，P009依赖P008完成；完整M1/M2未完成，不能以P005固定图或CLI替代。

## P008当前实现与下一步

P008已按满足的依赖激活，scope .规则回执已运行并完整读完.local/p008-context.txt全部541行，绑定新main4d6ee6c；不必重复加载，除非main/规则/范围再变。

1. 当前真实批次候选已实现：纯WorkflowBatch索引/预算、固定storage命令、父BatchSession共享同一WorkflowSession、独立样本隔离、暂停/取消/重开与父子对账；--workflow-batch CLI含manifest/validation/resume/rerun/template/template-out。模板保存真实节点/连接/参数并绑定第二批，合法分支图实际执行。中文runbooks/workflow-batch.md及版本契约已写。不是仅共享存储骨架。
2. CLI3项63.01秒（含14真实run的缓存损坏/重算链）、批次8项51.87秒（含父进程真实os._exit37后重开、ENOSPC、控制预算）、相关80项236.02秒已过。随后最后取消修正：坏源回执竞争双终态/重开加载前取消漏应用/父取消在忙存储后才传子导致提交先成功，均先原样复现再修；原失败不销账。最终相关16项50.04秒过。batch-mvp-validation.json记录每次作用范围和最终源码SHA。
3. 下一步直接冻结准确候选，一次最终独审及最终隔离wheels/正常PR/必需CI；本地不再重复全量1659套件。新wheel脚本纯批次/图恢复及真实批量4000/40、重开、样式8run、模板第二批已在323d59f全部通过。最终独审用现有/root/p002_independent_review；不要逐个小提交反复审。源码不能在wheel/test期间改动以免环境指纹失配。
4. 若检查/独审发现问题按真实反例修，保留原失败。P008候选323d59f独审Request changes：真实暂停中继续会停滞，现已限制resume入口并10项定向通过，准确53892fd已独审Accepted（独立3项30.69秒/日志SHA/diffcheck0），须新HEAD CI，整卡in_progress。P009仍planned；完成本卡并正常集成后接真实Web节点目录/增删连接/参数/保存重开模板/结果定位，不能用当前固定单图UI或CLI冒充M2。

## 并行规划写入

外部规划聊天通知正同步B012：根据数据判断、自动调整、人工纠正与方案精简。它只写docs/plans/research-platform-rd.md/.html、独立适应性说明及B012任务证据，不改P任务/registry/产品/handoff；请保留其dirty、不要提交或覆盖这些文件。等待最终具体指引后核对已授权M1/M2验收，不据预告猜科学阈值或扩展算法。当前git status已有B012 untracked，属于该规划者。

## 当前验证句柄与限制

本机最终wheel323d59f退出0，批量暂停修正后10项68.35秒退出0；当前无本机测试。PR53已ready，最终53892fd独审Accepted，quality41434643209已终止：Linux1671passed4旧skip728.40秒及全部新wheel/desktop/rulescontext通过；Windows1675pass1347.61秒+全部wheel/checkstep成功，但job总25m24超25m被cancelled，非通过。现仅Windows总时限25→30，需增量独审与新HEAD CI，native-case预期SKIPPED。先轮询这个运行，不重启；旧323d候选已自动取消。最终审查记录.local/p008-review-53892fd.md，已写入PR正文；待正常合入后随P009 closeout提交，避免纯证据提交再触发同产品全套CI。P005已合并，不再轮询旧PR52；main push产生同树CI可按需观察，不重跑同源产品。当前P008共享存储源需接完整批量，不以其4个初验当整卡。

科学留出/S1、用户体验、干净Windows/物理DPI/GPU/T002-P0及历史native UNKNOWN仍见risks/backlog；不冻结无依赖工程。原图/历史/旧dirty树/在用安装不覆盖；不扩新校正、其他实验全套、Agent、安装器正式发布/替换、外联、花费或数据上传。

P009准备：本会话已按skill运行impeccable context一次，完整输出.local/p009-ui-context.txt 506行已读（PRODUCT/DESIGN及候选surface信息）；尚未改UI/激活P009。保留现有Operate体系，无需重跑context。开始UI前需选择适用surface并按skill读craft-floor，最终有界视觉/真实WebEngine验收。
