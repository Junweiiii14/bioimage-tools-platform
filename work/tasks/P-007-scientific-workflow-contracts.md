# P-007 M1最小科学资产、连接与冻结工作流契约

<!-- PROGRAM_TASK_META {"id":"P-007","status":"in_review","work_package":"W11","depends_on":["P-002","P-003"],"execution_root":"C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-v0","owner":"chat-01a199d4-dac3-7dd3-af35-cdad7d361934","base_commit":"dc9618e7000eb7793067556e99d50a0d0509423d","head_commit":"c243933569db3ce4e9377283645c6f578ddd4b4e"} -->

## 输入与前置

4.0第3章/12.3/12.9；P002真实模块信封与成果，P003工程等价/D1/S1评估边界。原P004的WB估角/重采样另保留，本卡不以它整卡done作为通用平台前置。

## 用户可见成果

固定JSON流程可保存并由同一预检器解释节点、连接、参数及明确拒绝原因；后续CLI和GUI消费同一契约。工程样例不宣称新方法科学准入。

## 范围与不变量

只在tool_contracts公开api版本化新增ScientificAsset、连接端口描述、WorkflowDefinition及ExecutionPlan；按职责拆内部文件。组合既有AssetRef v1，复用ModuleSpec/ExecutionRequest/OutputManifest，不建立第二套物理资产身份。旧schema及协议保持；高版本拒绝，不自动迁移历史。

最小实际消费者为原始整数图像→旧WB粗模块→带状态表格/曲线成果。描述dtype、shape、axes、采集强度范围及来源、frame、单位、列type/nullability与有效/缺失/无效/复核状态；未知量显式未知，不从扩展名或float dtype猜。正式analysis_image的几何/有效域生产由P004另行版本化。

## 最小实施步骤

激活后先真实context并读模块README/API。冻结节点、边、输入绑定、参数及预期成果格式和兼容样例；固定注册的精确模块版本/实现摘要及参数schema可验证。定义不可变计划与其语义摘要，视图位置/主题不进入计算键。预检拒绝环、重复身份、未连接必需端口、错角色/单位/frame、显示图定量、未知模块/版本及不完整参数。不要接受工作区提供Python导入名。

## 验证和完成

以P002真实ModuleSpec和冻结数据运行契约正反例；独立预期来自解析样例。验证JSON预算/严格类型、旧v1读取及隔离wheel公开API。类型/边界/受影响测试与全部既有门禁；准确提交非作者独审和正常PR/必需CI后才done。本卡只完成真实消费者所需数据/图契约，不将执行器或编辑器标完成。

## 当前状态

已激活并实施契约/纯预检候选，尚未完成独审/全部必需CI与集成；执行器和编辑器留后续任务。缺科学参考只限制对应方法S1，不能填成通过。

## 2026-11-02激活

P002/P003已正常合PR48/49（main839fa52），本卡依赖满足。P006已完成原生基线并独立分支PR50待必需CI，不将其工具/证据夹入本任务。P007从实际main839独立分支codex/p007-scientific-workflow-contracts开始，先建立最小旧WB消费者所需的资产/端口/冻结图与纯预检，不提前宣称执行器/GUI完成。正式几何方法留P004。

## 基线前移及首轮实施

P006已独审/四必需CI后PR50正常合main dc9618e，P007保留自身未提交草案快进到该主线，规则回执按新base真实重载；无冲突、未丢改动。新增资产/端口/图/计划与纯编译，P002真实public API计划命令保存/重开；首轮28 tests passed/9.21秒，局部Pyright0。初次草案commit被新增wheel脚本三处行宽阻止，按格式修复，不绕过hook；尚未独审/全门禁，仍in_progress。

当前受影响组合首轮84passed/13.59秒（当时28新契约+18方法+38Workspace），新增环境/端口/真实P002曲线用例后重新核实结果；先前Pyright全范围0。23旧模型schema摘要与原v1源码/JSON相同，新API不改数值；wheel检查仅追加有限图/文件保存重开反例，保留全部原断言和门禁。

增量受影响组合已实际87passed/21.61秒（31契约+18方法+38Workspace）；Ruff、policy、9个import-linter合约、plan checker均exit0。新增曲线用真实P002 use case输出完整五点1000/2000/3000/2000/1000与4000信号，不用display数据。独立wheel与准确提交独审待执行，本阶段本地完整check --all未重跑，PR必需CI仍须完整执行。

## 冻结提交与真实独立安装验证

首个成功冻结源码6bb3168ad145a70d0851703826b4813057ae42e5。实际命令tooling.wb_workflow_plan --output .local/p007-proof-6bb3168 exit0，原图/定义/计划/receipt保持原生产字节；仅合同预检保存重开，不冒充图执行。tooling.installed_wheels准确该源实际exit0（Win11/Python3.12.14、offscreen/disable-gpu），包括新增runtime/contracts两节点文件绑定/预检/重开反例，既有科学评估、WB真实4000/提交重开、桌面和OCR等全部原检查也通过。原v1实现Git blob与新contracts_v1逐字节相同；execution.json/v1-source-preservation.json保留。

准确dc9618e..6bb3168非作者审查正在进行，后继只有证据/状态变化仍需审查；本卡转in_review绑定已冻结候选。当前不宣布最终Accepted或M1完成；本阶段本地完整check --all未重跑，正常PR必需双平台全门禁仍须通过。

## PR51冻结候选最终独审

非作者准确dc9618e..23d4056最终Accepted，产品6bb独立31passed/4.00秒及六组额外计划攻击均拒绝；四原件/receipt/旧v1 Git字节与实际wheel日志独立核对通过。PR51远端HEAD固定23d4056并已ready，规则/desktop已SUCCESS，Windows/Linux全门禁仍在执行，尚未合并；保持in_review。当前本地后继仅独审/交接记录，不推送更改远端冻结候选；待其正常集成后，真实集成收据随下一任务PR提交。

## PR51首轮Windows失败与最小交互修复范围

准确23d4056 Linux完整1596passed/4既有skip/613.11秒且新增/旧wheel均过；Windows1 failed/1599passed/929.22秒，旧manual_lanes真实pan等待40/25超5000ms，未合并。作者原样单测1passed/25.34秒，不能推断CI根因消失。受控探针：把OS鼠标放终点仍收到可信move并过；扣留初始rAF时可信事件delta40/25到达而fitImage首次panKey初始化把位移归零，4个回调未执行/naturalWidth100，确定可复现pending-layout竞态，不冒称CI当时也已定因。原日志/退出/来源SHA见ci-failure-r1.json和.local原件。

修复限定显示平移：在pointerdown采集初始offset前同步当前视图panKey，fitImage共用同一状态同步；保留原数值/ROI/原始输入。原完整测试增加扣留初始布局帧的分支，原40/25、取消恢复、原坐标ROI和1000/800数值断言、5000ms超时不改。适用scope仍为已加载的.，已读desktop README/当前实现及impeccable上下文/交互边界；不升级技能、不修复无关sidecar。旧独审23d产品结论不覆盖本UI增量，修后新准确提交独审与全部必需CI再验，不靠重跑或放宽门禁销账。

修复后普通/扣留布局两支完整手动流程2passed/17.20秒，邻近源身份/独立灰度7passed/12.76秒；保留原40/25、55/35、取消40/25与ROI/1000/800/原图/历史断言，未改5000ms或容差。新增回归修前实际exit1/8.38秒、修后0。Ruff/format（折行decorator后）、全Pyright0、web质量四反例检查0，impeccable单次机械detect0/[]。详情pan-race-regression.json和research最小实验。转in_progress等待新准确提交独审，不沿用旧Accepted宣称UI增量已审。

## 显示修复后准确候选独审

非作者准确dc9618e..dc4cc24a0248396de711b1e7f820280cc23de157 **Accepted，无新增阻断**。独立普通/延迟完整WebEngine2passed/17.23秒，实际生产函数/指针处理器12组偏移/同新视图/延迟fit/取消组合均通过；探针不替代真实Qt测试。七份回归原件和原CI完整日志SHA、规则回执/diff/plan checker/机械检测[]均核实。未改科学坐标/ROI/数值/超时/容差，保留首轮失败和受控因果限制。

转in_review绑定dc4cc24；后继仅状态/独审记录，仍复核准确新最终HEAD后更新PR51运行四必需CI。没有将旧失败重跑改成功，也不提前合并或激活P005。

## r2最终候选已派发CI

最终准确dc..c243933非作者Accepted：dc4cc后仅7文档/状态/完整归档，无源码变化，准确规则/plan/diff0。已push PR51新head c243933，quality41390321525实时in_progress、rules41390321566 SUCCESS；保持in_review，不作完整门禁通过/已合并。ci-r2-dispatch.json只证明已派发/当时状态，需实际终态。当前本地后继收据不push重启该冻结CI；四必需通过后按c243933正常合入并核对tree再done。
