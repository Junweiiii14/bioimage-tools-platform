# 最小科学资产与有限工作流 v1

P007的新增模型通过tool_contracts.api公开，编译/读取入口通过platform_runtime.api公开。它们不改变AssetRef、ModuleSpec、ExecutionRequest、OutputManifest或工作区存储v1。既有28项显式公开导出保留；原23个Pydantic模型JSON schema摘要来自main839，回归逐一比对。实现搬至contracts_v1.py，外部仍只用api；Python内部类文件路径不是文件持久化格式，不引入pickle迁移。

## 科学资产

ScientificAsset只组合既有payload AssetRef，不另建物理ID；sample_id、父payload引用、生产方法/参数摘要另记。ScientificType描述语义角色。当前真实消费者是P002整数原图及旧表/分析JSON；没有新增几何校正方法、科学准入或浮点WB定量。

- 原图限二维YX、uint8/uint16；shape和dtype为解码事实。采集位深、采集量程及其独立来源、物理像素尺寸必须显式填写或null，不从存储dtype推断。坐标为整数像素中心、数组[y,x]，frame同时绑定原始字节SHA，防止相同frame名称掩盖不同来源。物理校准和单位成对。
- 显示图为二维uint8显示资产，须有父来源和版本化显示方法；不能接quantitative端口。这里没有RGB数组进入桥接或定量。analysis_image描述要求有效mask/来源/生产方法；本轮没有其生产器或准入模块。正式几何/变换/有效域及其方法合同由P004另行版本化，不能据本模型存在宣称已完成几何校正。
- 表格描述列type/unit/nullability、行实体、状态列和有版本的状态词表。数值列必须显式单位（无量纲写dimensionless），带测量状态的值必须允许null。非valid状态不许用有效零代替；载荷验证由后继执行/发布适配器负责。平台不含实验专用状态分支；WB装配元信息保留旧quality_review/excluded/not_detected等原词汇，不重写历史。
- 曲线描述x/y单位、frame、点数与valid/missing/invalid/review及原因；空曲线不能是valid，顶层单位必须等于y单位。曲线数组留在文件，不放进事件。测试从真实P002三角形原图取得完整五点raw profile及4000积分，组合实际JSON文件引用；不是显示下采样曲线。

这些是严格元信息契约，不证明磁盘字节符合声明。P005执行准入必须重新验证输入SHA/路径、实际解码的dtype/shape、表/曲线状态与所需文件；P004负责正式几何科学关系。外部登记表/方法S1不能由导入模型或计算摘要自动授予。

## 图、固定注册与预检

WorkflowDefinition保存workflow/version/revision/sample、节点、连接、根资产绑定与命名成果；WorkflowLayout另存位置/zoom，不进入定义或计算键。v1是有限无环图：最多64节点、256连接、128根绑定、64成果；每个模块仍遵守旧8输入/16输出信封上限。load_workflow_definition/workflow_definition_json和冻结计划读取使用既有1MiB、32层有界canonical JSON，拒绝重复JSON键、非有限值、严格类型错误、未知字段/版本；不迁移旧库。

ModuleRegistration由可信宿主装配代码创建，持有WorkflowModule和参数验证回调。工作区只含数据和ModuleSpec，不含Python导入路径。注册必须唯一，模块版本、方法、实现摘要、完整参数schema及端口与冻结节点精确相等；声明schema必须与验证回调的schema投影一致。回调本身是宿主可信代码，不从schema或工作区动态执行。纯编译器不拥有I/O；可信验证器可检查其本工具契约，宿主应避免在GUI线程执行有文件成本的验证。

WorkflowModule是当前样本的冻结接口投影：输入声明角色、可接受dtype、期望单位、可选精确frame/来源和表列；输出类型在运行前冻结。quantitative端口须声明单位，图像还须声明dtype，表格须声明列/状态/单位。新series/analysis_image元信息组合旧analysis_result物理信封角色，旧P002端口/worker不因此接受新载荷；只有相应可信装配和后续适配器才可消费。

compile_workflow返回ExecutionPlan或携带结构化issues的WorkflowValidationError。拒绝重复节点/绑定/成果、缺节点/端口/输入、环、跨样本绑定、同物理身份冲突、未知或不匹配模块、参数不完整/多余以及角色/dtype/unit/frame/表schema不符。顺序按拓扑层及节点ID稳定排序；即使声明顺序改变也产生相同计算身份。

## 冻结与计算身份

计划冻结每个节点的接口、canonical参数、解析输入/来源节点端口与上游计算键、排序环境依赖和命名成果。节点computation_key含完整模块/接口、参数、根资产引用和科学元信息、上游输出端口/键及环境；布局、节点名称、流程标题与修订不进入节点计算键。输入引用ID/路径目前也参与身份，保守失效不跨文件重定位复用。旧P002的参数中仍保留自身revision，这是旧方法信封语义，后续新适配器另行版本化，不静默删除。

改A参数只使A与其后继计算键改变，独立C保持；环境或数值元信息改变也使相关链改变。execution_plan_digest标记整个冻结计划（含流程/节点身份和revision），不同于节点缓存键。摘要不是签名、文件完整性检查或方法准入。load_execution_plan/verify_execution_plan从可信注册表重新编译并逐项核对，拒绝改过的source_key/接口/环境/类型，而非相信工作区自报的新摘要。

P007不实现调度、账本、缓存复用、暂停/取消、结果事务或GUI。P005复用当前真实RunSession/Workspace执行单图，并核验实际产物/退出/提交与恢复；P008复用它做有限批量；P009接同一实现编辑/保存/复用模板。不能把本图预检当M1运行交付。

## 可运行的P002契约样例

```powershell
uv run --locked --no-sync python -m tooling.wb_workflow_plan --output .local/p007-new-plan
```

仅接受新目录，写自有uint16三角形TIFF、workflow.json、execution-plan.json和receipt。真实public wb_module_spec/prepare_wb_execution负责参数验证；旧表CSV列/状态按原格式投影，旧analysis/baseline JSON不伪装成新标准曲线。定义与计划保存重开逐项相同；命令只做契约/预检，不执行图、不发布结果，也不宣称S1。旧原图/结果不覆盖。

新增测试覆盖图/JSON边界、性质（声明顺序/布局/修订不改键、参数只失效后继）、信封版本、显示图/单位/坐标拒绝、真实旧WB参数与文件曲线、旧schema兼容。隔离runtime/contracts wheel追加真实文件绑定、两节点编译/保存重开及拒绝检查，保留原全部安装/评估/V0检查；没有删skip、改容差、更新锁文件或放宽门禁。
