# P-007 M1最小科学资产、连接与冻结工作流契约

<!-- PROGRAM_TASK_META {"id":"P-007","status":"planned","work_package":"W11","depends_on":["P-002","P-003"],"execution_root":"not_activated","owner":null,"base_commit":null,"head_commit":null} -->

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

尚未实施或验证；P002/P003未done前不激活。缺科学参考只限制对应方法S1，不能填成通过。
