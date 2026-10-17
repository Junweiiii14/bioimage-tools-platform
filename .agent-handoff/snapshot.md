# Handoff Snapshot

- 更新：2026-10-17。当前任务唯一状态：work/tasks/T-042-source-only-repair.md；本轮仅任务配置，产品修复未实施。总体T-003/WB未完成科学验收。
- 活动树：C:/Users/70236/.codex/worktrees/t021-coordination/bioimage-tools-platform；分支codex/t042-source-only-repair；base b32acff，产品仍f7a6651。原主目录旧dirty与本树.impeccable/questions保留，不双向覆盖。
- 用户顺序：短膜误判/倾斜→Marker误删/自主N/独立原图lane ROI→现有工作台普通入口复验→灰度积分边界→维护精简。全部能力正式接入工作台，不靠.local脚本注入成果；语义改动与重构分开。
- 原图/旧结果不可覆盖；参考仅评分，不进入检测输入或提供N/倾角/ROI；8图是已诊断的固定回归集，不冒充独立留出验证。旧严格自动1/8=12.5%；后续参考辅助8/8和监督48值不算自动准确率。
- 工具：现有Web/Git/gh与锁定Python数值/Qt测试栈；不新增插件/MCP/依赖，不改全局设置。独审绑定未来产品提交，当前未执行。
- 配置验证见work/evidence/T-042/configuration.md：context、doctor、smoke-env、policy、gh认证和8源图SHA均exit0；12参考文件仅当前SHA清单，历史参考比对未做。隐私清单.local/t042/input-inventory.json，不提交图像。
- 下一步：阶段0冻结源输入/评分协议/旧自动证据，再阶段1完成社区维护者源码与官方文档对照，短膜阈值解耦及轮廓/倾角最小实验；修改产品前扩大context范围并读模块契约。
- 既有风险仍在：T040旧17/48边界切穿主峰、33/48下限平台；600 passed但总exit1根因UNKNOWN。未跑新产品测试/全门禁/新准确率/远程CI/PR/main/干净Windows。
- T040原执行记录见work/tasks/T-040-real-fig-validation.md；上一snapshot已完整归档.agent-handoff/archive/2026-10-17-before-T042-snapshot.md。用户已停止的原生CUA不重启。
