> 当前阅读入口（2026-11-03）：P002独立WB、P005/P007/P008通用执行及P009可视编排已工程集成；准确范围见[P009收据](../../work/evidence/P-009/objective-audit.md)和[模块地图](../../docs/module-map.md)。下文带任务编号的追加记录描述当时阶段，其中“开发中/尚待接入”不是当前待办；以对应任务卡和当前公开API为准。科学、用户、性能及目标机限制见[风险入口](../../.agent-handoff/risks.md)，不由工程完成消除。

# 文件资产与运行契约

公开入口 tool_contracts.api。不可变 Pydantic 严格模型：工作区格式、资产引用、
文档修订、运行记录、进程退出回执与恢复报告；机器 schema 从模型生成。
不含 WB/IF/IHC 参数，不加载 GUI、数值库或数据库，不在导入时访问工作区。

内部资产路径使用规范 ASCII 相对路径（显示名称保留在工具文档中），拒绝 Windows 设备名/别名；
数字不接受布尔或字符串强转；失败/中断须有原因，
只有 succeeded 可以引用结果。pid=0/code=None 表示宿主确认尚未启动；启动进程须有退出码。
退出回执由宿主 OS 生命周期观察产生，模型本身不能代替实际观察。

测试与隔离安装通过仓库根 `uv run --locked --no-sync python dev.py check --all`。

P003新增独立schema v1的数据来源/分组、冻结评估计划/观测、工程报告与D1方法登记。
公开模型不授予S1；有效零与无效空值严格分开，未知来源/材料不补为通过。
见docs/contracts/method-validation-v1.md（仓库根相对路径）。旧存储schema保持。

P007新增ScientificAsset/ScientificType、科学端口、WorkflowDefinition/WorkflowLayout与ExecutionPlan；组合原AssetRef，旧28项显式导出与JSON schema保持。新内部文件按契约职责分开，外部仍只用api。见docs/contracts/scientific-workflow-v1.md（仓库根相对路径）；模型存在不代表执行器、正式几何方法或科学准入已实现。
