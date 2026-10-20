# 契约演进规则与导航

当前已实现 `tool_contracts.api`、平台工作区、WB与桌面公开入口，实际职责见[模块地图](../module-map.md)。本页下文保留基础契约演进规则，不能将早期SDK草案说明当作当前全部能力状态。

WB导入主链从[仪器清单](wb-instrument-intake-v1.md)、[导出识别](wb-export-discovery-v1.md)进入[冻结计划](wb-intake-execution-v1.md)、[阶段调度](wb-intake-workflow-v1.md)、[裁剪](wb-intake-crop-v1.md)、[完整Fig与定量](wb-intake-figure-v1.md)、[输出恢复](wb-intake-output-v1.md)。增量及验收见[采集组计划](../wb-grouped-intake-plan.md)和[已有验收索引](../wb-execution-acceptance.md)。

契约分为工具声明、执行、视图、宿主端口和数据封套；字段草案见原 PDF。未来 Pydantic 模型为机器 schema 唯一生成源，生成 JSON Schema 提交并检查漂移，不手写两套模型。

必须定义单位、缺失/无效值、严格字段行为、版本和错误。请求/结果带 run_id、attempt_id、输入摘要和源修订。应用版本、算法版本、数据/schema 与协议分别管理。

严格旧读取器可能拒绝新增可选字段，因此“加字段”不自动意味着兼容。每次修改覆盖：旧生产者→新消费者、新生产者→支持消费者、旧文件读取/迁移、未知高版本拒绝覆盖。扩展→迁移→明确版本清理，保留弃用期限与所有消费者清单。

尚未落地的通用桌面SDK等规划模块须由就绪任务实现；不能仅凭文档声明其可运行。已有产品契约与兼容测试以各链接和模块说明为准。
