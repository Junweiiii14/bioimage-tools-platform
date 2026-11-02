# 当前恢复指针

目标active、无预算：实际产品树bioimage-v0完成4.0 M1通用执行及M2真实可视编排。当前分支codex/p008-workflow-batch，main基线4d6ee6ce364780cad24ef09b808740846937714c；核对HEAD/dirty再接续。任务状态唯一来源为work/tasks/P-008-workflow-batch-recovery.md。

用户要求：入口一次校验，内部信任类型，不重复判空/滥用catch、不抽一次性函数、不写臆测容错；授权内连续推进，集中最终候选独审，不逐小提交审批。karpathy-guidelines已固定核验安装。用户本轮进一步追问全量测试必要性：已解释因共用运行/存储变化需最终防回归；本机/CI有重叠，后续本地先定向、最终候选CI做全量；纯文档/资源配置不额外本机全量，必需CI/断言保持。

## 已完成与保留证据

P002/P003/P005/P006/P007已正常集成，不重做。P005准确2258cd5非作者Accepted，PR52四必需CI全SUCCESS后正常merge4d6ee6c，tree同为4a50fc0738b61303c8d495cce03272845c7876e8。Windows1659pass1185.30秒/Linux1655pass4既有skip508.51秒，双侧全部隔离wheel及真实三节点/4000/重开/两步缓存通过。integration.json及runtime-review.md保留准确事实；首轮P2、旧本机F/GPU未知及旧Windows20分钟超时不销账。最终Windows总25分钟/Linux20，未改测试/断言/单测超时/必需门禁。

P004新几何方法仍独立planned，P009依赖P008完成；完整M1/M2未完成，不能以P005固定图或CLI替代。

## P008当前实现与下一步

P008已按满足的依赖激活，scope .规则回执已运行并完整读完.local/p008-context.txt全部541行，绑定新main4d6ee6c；不必重复加载，除非main/规则/范围再变。

1. 初始产品改动仅WorkflowSession支持父拥有AsyncStorage，子关闭仅退自己的准备线程，单独入口仍拥有两个服务。实际两个顺序子图/6真实run、父存储持续可用/最后关闭重开已验证；关联旧start/pause/reopen共4pass26.27秒，Ruff/Pyright0。证据P008/shared-storage.json。尚未最终独审/新wheels/新CI，无完整批量产品。
2. 下一步实现有限批次的opaque/CAS持久索引，先存子execution_id与冻结plan再派发，顺序复用同一WorkflowSession。独立样本失败继续、父暂停取消与关闭重开、父子记录未关联时对账、第二批模板绑定与依赖重算；不建立第二缓存/恢复器，不再每小步全量或独审。
3. 具体接线笔记.local/p008-integration-notes.md为设计线索，不是实现证据。批量模型/预算与新故障验收须冻结后实现；保留原始资产、RunRecord/attempt身份和P005事务语义。公共纯模型不依赖Qt/WB，宿主固定注册，不加载工作区代码。CLI/中文操作单/最终隔离wheels/准确独审/必需CI完成后才认P008done，再接P009。

## 并行规划写入

外部规划聊天通知正同步B012：根据数据判断、自动调整、人工纠正与方案精简。它只写docs/plans/research-platform-rd.md/.html、独立适应性说明及B012任务证据，不改P任务/registry/产品/handoff；请保留其dirty、不要提交或覆盖这些文件。等待最终具体指引后核对已授权M1/M2验收，不据预告猜科学阈值或扩展算法。当前git status已有B012 untracked，属于该规划者。

## 当前验证句柄与限制

没有活动本机测试或独审。P005已合并，不再轮询旧PR52；main push产生同树CI可按需观察，不重跑同源产品。当前P008共享存储源需接完整批量，不以其4个初验当整卡。

科学留出/S1、用户体验、干净Windows/物理DPI/GPU/T002-P0及历史native UNKNOWN仍见risks/backlog；不冻结无依赖工程。原图/历史/旧dirty树/在用安装不覆盖；不扩新校正、其他实验全套、Agent、安装器正式发布/替换、外联、花费或数据上传。
