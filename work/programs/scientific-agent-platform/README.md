# 研发任务登记入口

当前从[交接索引](../../../AGENT_HANDOFF.md)恢复，不从已完成的P001重新开始。产品方向见[方案目录](../../../docs/plans/README.md)，旧章节号见[版本索引](../../../docs/plans/history.md)。

## 唯一状态与依赖

任务状态只在各任务卡的PROGRAM_TASK_META中；registry.json只记录路径、工作包与依赖。P002/M1/M2集成证据见[P009审计](../../evidence/P-009/objective-audit.md)。科学S1、用户、目标机及性能限制不由工程done关闭。

只读检查：`uv run --locked --no-sync python work/programs/scientific-agent-platform/check_plan.py`。它检查文件、ID和依赖，不验证权限、科学准确性或GitHub集成，也不自动激活ready任务。P004仍是独立几何方法候选。

## 新任务

从task-template.md建立任务，先核对现有ID、真实需求、依赖与授权，再登记路径。未实施为planned；不要为了路线完整创建空实现或把所有未来工作同时激活。规则加载使用实际dev.py context命令，状态变化不需要反复重出方案。

当前源码基线以main集成为准，活动工作树按任务元数据定位；旧分支与归档中的状态仅是快照。task_execution_root为`.`时只解析本检出中的卡，不代表其他未提交工作已同步。迁移证据按明确白名单和摘要接入，不覆盖别人的dirty。

B005 transfer-manifest及早期P001复制步骤属于历史，不再用于当前同步。新增独立工作树不改变产品历史任务的execution_root；分支收尾记录与代码、检查绑定。

## 5.0接续

P010是下一项待执行的需求/方法调研，planned不等于已访谈或已实施。W06/W07按调研结果拆产品任务；不无条件以新几何P004阻塞已有原值方法，但选择新几何时必须显式登记P004及科学验证依赖。已完成P卡保持，工作包依赖不是自动启动指令。
