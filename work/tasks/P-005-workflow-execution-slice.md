# P-005 工作流与事件协议的最小可靠执行切片

<!-- PROGRAM_TASK_META {"id":"P-005","status":"in_progress","work_package":"W04","depends_on":["P-002","P-007"],"execution_root":"C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-v0","owner":"chat-01a199d4-dac3-7dd3-af35-cdad7d361934","base_commit":"006e9f143c830f5e13be2932e8ac37a9f3a05ed1","head_commit":null} -->

## 执行状态

机器元数据是本卡状态的唯一字段；planned表示尚未执行。B-008发布方案和修订任务卡不等于本任务已经实施。激活时核对编号、授权范围和前置任务，把执行权威移交到正确产品树；记录实际execution_root、owner及base/head，源副本改为带目标路径和提交的只读指针，不同时更新两套状态。

## 输入

P-002独立WB模块及实际契约、既有RunSession/Workspace/CAS与worker协议；B-007第3/5/6/12.4章冻结运行身份、事件、编辑与提交语义。

## 允许范围

最小串行引擎/事件契约及旧WB用例适配、故障注入；不一次实现任意DAG、远程调度或新校正方法，不自动扩展本次V0交付。

## 执行步骤

1. 消费P-002冻结的ModuleSpec、ExecutionRequest、OutputManifest及现有AssetRef，按B-007命名演进ScientificAsset、ExecutionEvent、WorkflowSpec；不定义第二套资产/结果身份。冻结输入、方法/实现摘要和参数；workflow_run_id、node_id/attempt_id、真实RunRecord.run_id及草稿generation分别记录。
2. 首版串行拓扑调度，复用Workspace单活动进程约束；宿主拥有版本化账本，先沿既有opaque文档/CAS保存，不先做SQLite DDL迁移。定义worker_seq与宿主全局event_seq、有界消息/背压、资产引用及可靠状态事件；预览可合并但终态/关键状态不可丢。
3. 用旧WB方法和确定性夹具贯通开始、步骤、中间结果、节点边界暂停、取消和提交。pausing停止派发，当前节点终态且进程退出后才paused；取消先于提交则不成功，提交先完成则返回已完成。worker manifest不直接宣告成功，宿主确认退出/校验/提交/账本登记后再通知。
4. 故障注入覆盖崩溃、磁盘满、manifest后非零退出、底层已提交但账本未关联、迟到/重复事件和关闭重开；通过幂等提交意图及真实run对账。中断节点重试为新attempt，不声称恢复任意算法内存现场。
5. 只重算依赖受影响节点；冻结输入/科学描述及载荷摘要、方法/实现、参数、环境和种子的缓存键；复用仍检查准入。修改先形成草稿，应用时到节点边界，新revision创建新计划，旧结果不可覆盖；后续EditIntent/Preview/Receipt沿第6章单请求CAS与操作幂等。
6. 新校正资产接线先依赖P-004契约及其具体实现任务；本任务旧方法引擎切片不冒充完整V2新自动旋转闭环。通过真实进程/存储集成与绑定提交独审，保留旧入口回退及后续切片边界。

## 验收与退出

真实旧用例完成与失败可观察；节点边界暂停、取消/提交竞态和重开恢复无伪成功；事件版本/预算、身份、缓存及依赖重算有反例证据；本卡只证明引擎切片，完整V2另需V1资产实现和交互整合。

## 失败与待决处理

新API与数据迁移跨度过大则拆任务；不靠伪PID或放松Workspace提交证明运行。旧方法成功不能给V1/V2/V3或W03/W06自动记完成。

## 用户可见验收安排

按B-007第5/6/12.4/13.3节提供可观察步骤、暂停/调整/继续、取消和重开恢复操作；尚未接真实引擎的前端替身不算体验通过。未取得用户或科学确认写待验，不代签。

## 验证和审查记录

产品实施和验收未运行；B-008仅修订任务卡。实施后记录命令、退出码、环境、base/head、样本/资产摘要、独立预期、真实结果、未覆盖项及审查者。产品检查按实际目标树已有命令执行，不发明dev.py子命令。产品变更须绑定准确提交独审；约定集成完成前保持in_review，未经发布不写已发布。

## 继续入口

本卡未完成步骤为继续位置；主依据为docs/plans/research-platform-rd.md第3/5/6/12.4章，B-005仅作治理历史。修改规则或范围后重载context，收尾更新任务与handoff。

## 2026-11-02 4.0依赖拆分（尚未实施）

保留原P002依赖，新增P007科学资产/冻结图契约前置。本卡以旧原值WB粗模块与至少一个真实技术节点贯通固定图串行执行、节点边界暂停/取消、持久提交及幂等恢复；本卡完成单个固定图的依赖失效、复用校验和幂等恢复及既定反例；P008复用这些实现扩展有限多样本隔离、跨样本身份/预算并做完整M1工程交付，不建立第二套账本/缓存/恢复器，P009另做M2。原本卡的事件/缓存/重试反例不删除，不以P008分拆为由省略既定可靠性验收；新几何仍依P004具体实现，不假称新WB方法完成。

## 2026-11-02激活

前置P002/P007已通过准确独审、PR48/51与全部必需CI正常集成，当前base main006e9f1。分支codex/p005-workflow-executor从保留P007本地交接收据后与main正常合并的14c0153开始；原样保护既有证据/原图/历史，P007收尾记录随本分支提交。不再等待科学/目标机材料，也不将它们补为通过。

实际范围：同一有限图/同一RunSession与Workspace/CAS贯通真实输入校验、旧WB数值分析、带状态表/完整曲线发布；先单图串行，账本/缓存/重开/节点边界暂停取消和既定故障反例完整实现，P008复用它扩有限批量，P009接同一执行器。旧worker和旧UI入口保留。所有前端/后台/CLI状态只在实际退出、校验、正式提交和账本登记后完成。

实施前先冻结版本化事件/ledger/技术节点与验证设计。注意既有模块成果总预算16MiB，不能用复制大型原TIFF作为校验节点输出；小型校验凭据绑定原AssetRef，分析节点须核对它与原输入的身份和实际类型。现只有只读架构笔记.local/p005-design-candidate-20261102.md，非既定实现或准入。本卡尚无产品实现/验收成绩。

## 执行与验收设计冻结

work/evidence/P-005/execution-test-design.json冻结单图真实三节点、身份/状态、当前环境准入、预算和12类成功/故障实验。v1新增上限256 attempts、128 controls、4096 critical events为有限执行的防失控预算，不是性能成绩；实现必须预留终态容量，不能丢关键状态。沿用64节点/256连接/1MiB图、旧8/16端口、16MiB成果/文档预算，未改既有门禁或科学预期。原图通过引用传递，校验输出为小凭据，避免大型TIFF复制使既有预算失真。

计划冻结不等于实现；P005产品/测试尚未执行。下一步具体实现版本化ledger/事件模型和纯状态转移，再接同一异步存储/RunSession，按真实实验逐项检验后独审/PR。

## 账本组件实施（整卡未完成）

2026-11-02新增版本化WorkflowLedger与纯转移及8项组件测试，详细真实成绩/首轮失败见work/evidence/P-005/journal-component.md。关联P007/Workspace共77pass；真实两节点子进程退出与存储提交/重开仅为组件夹具，不是生产三节点WB图。取消最后名额保留、科学计算键与原物理输入双重匹配纳入新v1契约。未改旧公式/schema/测试门禁。下一步存储线程接线、共享RunSession/正式worker与冻结故障矩阵，准确提交独审/正常PR与必需CI仍需完成。

首版26f准确组件独审Request changes（图generation/新节点document revision混用）已保留；修为新节点document0、冻结plan保留generation，并补真实plan7准备回归。AsyncStorage固定workflow操作已接现有存储线程，真实run/manifest/缓存字节核验与CAS、ENOSPC后重开唯一run、GUI响应屏障测试已加入；11项组件/存储测试及受影响99项通过，完整说明见journal-component.md。GraphSession/正式WB三节点/当前环境认证及完整故障矩阵仍未实现，新head独审待做；未标整卡done/未PR集成。

第二版8bb独审确认上述P1已修，但新P2：封装匿名hello漏来源attempt/run，可刷新CAS后错误关联新attempt；Request changes及独立11pass保留journal-review-r2.md。后继补worker/started/finish/abandon来源绑定，新增真实失败重试旧hello/finish反例；作者最终12新测试/受影响100pass27.19s，Ruff/Pyright0，新准确提交仍须复审。整卡继续in_progress。
