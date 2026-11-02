# 研发方案入口

- **当前主方案3.0**：[完整研发总方案](research-platform-rd.md) · [HTML](research-platform-rd.html)。13章覆盖现有代码、10类实验流程、界面风格、编辑与重算、模块/Agent、分期成果及验收。
- **第一阶段V0**：[执行说明](phase-1-v0.md) → [P-001基线接入](../../work/tasks/P-001-platform-baseline-adoption.md) → [P-002独立WB切片](../../work/tasks/P-002-wb-headless-module.md)。发布文档不等于这些任务已完成。
- **开发数据**：[来源与用途说明](development-data.md) · [17条机器登记](../../work/evidence/B-007/public-development-data.json)。原图、RDML/FCS小样和安装包不随Git公开提交。
- **长期状态**：[任务依赖入口](../../work/programs/scientific-agent-platform/README.md)，状态唯一来自任务卡。
- **历史**：[B006研发方案2.0](archive/research-platform-rd-v2.md)、[B005治理补充](scientific-agent-platform.md)。历史规划中的旧接口名/章节不覆盖3.0。
- **构建HTML**：[可移植构建说明](renderer/README.md)。仓库版本使用已有字体；本地便携版内嵌字体。

产品基线：本次GitHub发布基于main的18b5cf6；方案审计的是本地T082提交dfc48ed（截至核验比该main多28提交）。不得把文档发布解释为T082已远端集成、安装器替换或科学/目标机验收通过。P001负责核实并接入真实产品基线。

## GitHub 任务导航

[第一阶段 V0（#44）](https://github.com/Junweiiii14/bioimage-tools-platform/issues/44) · [阶段里程碑](https://github.com/Junweiiii14/bioimage-tools-platform/milestone/2) · [依赖维护索引（#45）](https://github.com/Junweiiii14/bioimage-tools-platform/issues/45)。任务执行状态仍以仓库任务卡为准；历史日志 #6 保留原时间语境。


## 2026-11-02 4.0接续（优先于上述历史阶段限制）

当前主方案已同步4.0。P002先按原范围验收，随后持续推进M1通用执行与M2可视编排，见docs/plans/phase-2-workflow-authoring.md（仓库根相对路径）。旧3.0/V0终点说明保留为历史；任务依赖由新执行者按4.0拆卡登记，不从文档推断产品已实现。HTML继续用docs/plans/renderer/build.mjs；不使用旧规划树的本机B009构建器。
