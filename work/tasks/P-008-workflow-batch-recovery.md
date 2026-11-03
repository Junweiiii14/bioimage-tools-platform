# P-008 M1有限批量、依赖重算与崩溃对账交付

> 历史设计引用：本卡原始4.0章节见[固定版本](../../docs/plans/research-platform-reference-v4.md)，不按新版主文同号章节解释。完成状态以本卡元数据与准确集成收据为准。

<!-- PROGRAM_TASK_META {"id":"P-008","status":"done","work_package":"W12","depends_on":["P-005","P-007"],"execution_root":"C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-v0","owner":"chat-01a199d4-dac3-7dd3-af35-cdad7d361934","base_commit":"4d6ee6ce364780cad24ef09b808740846937714c","head_commit":"b4847a56b682e71356129e34fac59262c08659e7"} -->

## 输入与前置

4.0第12.3；P005真实串行执行与可靠事件，P007冻结图/科学资产，现有RunSession和Workspace opaque文档/CAS。P004的新WB校正方法不作为原整数图工程图的前置，不宣称完整WB新自动校正完成。

## 用户可见成果

保存的流程绑定第二批合成输入后一次启动，独立样本异常隔离，正常项仍自动产生真实表/曲线和异常清单；关闭重开可定位正式成果和真实未完成状态。

## 范围与实施

platform_runtime仅通用图/账本/失效规则；实验适配在工具api与宿主固定注册，runtime不导入WB。复用Workspace单活动进程，有限批量展开后串行调度；明示节点/样本/事件/资产预算，超限拒绝。原图、旧结果、旧修订不覆盖。

复用P005单图依赖失效、复用校验、幂等恢复的同一实现和账本，不建立第二套缓存/恢复器；新增批量特有验证，并对P005可靠性行为做集成回归。在此基础上补可复现的批量身份、每节点attempt与真实RunRecord关系、幂等提交意图及重启对账。输入/科学描述/参数/方法/实现/环境/种子进入依赖键；移动节点不重算，参数变化只使后继过期，报告样式仅重做相关输出。复用前重新检查模块准入及正式资产SHA，损坏不复用。结果已提交但账本未关联时根据冻结意图及真实run对账，不能伪造PID/成功；未知执行标interrupted，重试新attempt。

## 验证与完成

真实输入校验节点→旧WB粗分析→成果发布节点，至少一个技术节点为实际可复用实现，不能仅绘WB框。合法分支图稳定拓扑顺序；坏文件/非法ROI/取消/非零退出/缺输出不变零，独立样本继续。故障注入结果提交后账本前崩溃、摘要篡改、重复/迟到事件、取消提交竞态及重开；记录实际产物和逐例预期，不用mock证明完整引擎。共享CLI入口、中文操作单、兼容回退、隔离wheel、全门禁、准确提交独审及PR/必需CI后才done；工程/科学/用户体验分别记录。

## 当前状态

2026-11-02激活：P005已PR52准确独审及全部必需CI后正常合入main4d6ee6c，P007此前完成。新分支codex/p008-workflow-batch从该main接续。尚无批量产品实现/验收；先重新加载任务规则，再复用WorkflowSession/同一存储端口接线，不建立第二执行器。不含远程调度、任意脚本、通用循环控制、其他实验算法或安装器发布。


## 真实批量候选（整卡仍in_progress）

现有同一WorkflowSession/父存储已贯通版本化批次索引、样本失败隔离、暂停/取消/关闭重开、父子未关联恢复及CLI。模板沿P007保存真实图和参数，可绑定第二批原始输入；分支图实际worker按拓扑运行，不是绘图。WB绑定只更新资产/输入元信息/源SHA，不猜ROI或新科学阈值。--rerun创建新批次，样式仅重发布，参数重分析及后继；损坏缓存该样本失败，其他样本继续，下一新批次从完好检查点重算缺项，旧资产/运行保持。

真实输入CSV4000/40、合法零0/invalid空值分别核验；批次8项51.87秒、CLI3项63.01秒、关联80项236.02秒通过。之后为两个已复现取消问题补丁：坏输入回执与取消双终态，及取消请求被父存储阻挡/重开加载前取消未应用；原失败保留，最终相关16项50.04秒通过，未弱化预期或容差。精确范围/原日志摘要/源码SHA见batch-mvp-validation.json；最终准确独审/隔离wheels/CI尚待完成，不提前done。

新增有限预算16样本/合计64节点256边/1MiB计划/256派发/128父控制（保留最后取消名额），父文档沿旧16MiB；不是性能或OS硬配额。公开纯模型不依赖WB/Qt；父索引仅指向旧WorkflowLedger，不另造结果/资产/PID。中文操作单docs/runbooks/workflow-batch.md，版本契约docs/contracts/workflow-batch-v1.md。


## 最终候选独审修正

候选323d59f四组隔离wheel全部退出0，含安装后批量4000/40、6run/重开、样式8run和模板第二批。独审真实复现P2：pausing时接受resume使父running/子paused停滞，Request changes。已明确仅完成暂停或重开awaiting_resume才接受继续；新增回归先1failed2.94秒，修复后批量整文件10passed68.35秒。无容差/预期弱化。独审自身并发pytest与作者编辑重叠的2failed8passed50.91秒不归属冻结候选、不作为新增缺陷或通过。最终修正准确提交复审及PR53修正后CI待完成。


## 最终CI资源实测

53892fd独审Accepted；PR53 quality41434643209 Linux1671passed4旧skip10warnings728.40秒、所有wheel通过，desktop/rulescontext成功。Windows1675passed10warnings1347.61秒、全部wheel及dev.py最终成功标记均实际出现，checkstep为success；但job总25分24秒，被服务器25分钟上限标cancelled，不能作为必需CI通过。现仅Windows作业总时限25→30分钟，Linux20不变，无断言/单测时限/跳过/门禁削弱；纯CI资源变更不重复本机全量。需准确增量独审及新HEAD正常CI。


## 旧网页测试夹具时序修正

资源候选0c33的CI41438503742：Linux1671pass4旧skip820.52秒/allwheels通过；Windows1failed1674passed875.13秒，旧advanced真实网页用例在手工未保存的并发修订后，与700ms自动保存竞争，下一次template_apply被宿主busy正确拒绝。实际调用自动保存回调的有界探针重现相同断言（探针1pass8.16秒表示观察到预期旧失败，不是产品通过）。仅补3行：真实保存并发修订、等待原20秒预算内hostidle、断言current_draft_saved，再原流程验证冲突/24值/保存重开导出；原断言/容差/skip/单测时限均不改。修正后该完整文件2pass8.88秒。产品代码保持53892fd，准确新提交独审/CI待完成。


## 正常集成完成

准确b4847a5全范围独审Accepted，PR53四必需CI SUCCESS后于2026-11-02T12:27:06Z正常merge275560475d39426434416c74feeb0c2f259d1402；main与候选tree同98754bddc520b38bdaa8f5c7ce2c5882d9fc4f04。最终quality41441375415 Windows1675passed10warnings1306.50秒，Linux1671passed4既有skip10warnings930.49秒，双侧全部隔离wheel含真实批量4000/40/6run/重开/样式/模板第二批通过。native-case按定义SKIPPED。旧超时/夹具失败仍保留，不冒充通过。M1工程本卡done，P009可接续；科学留出/用户体验/目标环境不代签。
