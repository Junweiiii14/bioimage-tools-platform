# P-007 M1最小科学资产、连接与冻结工作流契约

<!-- PROGRAM_TASK_META {"id":"P-007","status":"in_progress","work_package":"W11","depends_on":["P-002","P-003"],"execution_root":"C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-v0","owner":"chat-01a199d4-dac3-7dd3-af35-cdad7d361934","base_commit":"dc9618e7000eb7793067556e99d50a0d0509423d","head_commit":null} -->

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
