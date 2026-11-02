# 当前恢复指针

- 当前任务：[P002](../work/tasks/P-002-wb-headless-module.md)，状态唯一来源在任务卡。P001已完成并正常合入main；不重复合并或重启旧CI。
- 执行树 `C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-v0`，分支 `codex/p002-wb-headless-module`，base `29930f62a0b158189b76e0fad7d090d632f149d6`，worker/存储增量HEAD `725fc6aef8df192f46fdceb122f6ff669251dd72`。旧主目录dirty、T082原树及安装不修改。
- P001 PR47最终候选f4bd81e经准确提交独审及四必需CI通过；Windows1503 passed，Linux1499 passed/4既有skip；main合并树与候选一致。关闭记录及review-final.md已随P002激活记录提交。
- P002已加载全仓规则回执 `work/evidence/P-002/rules-context.json`。本轮新增模块契约、原WB适配、静态对照worker、CSV/来源成果及RunSession存储准入；AssetRef v1及旧storage schema保持。详细文件见git状态与P002任务。
- 2026-10-31本轮组合验证34 passed/21.99秒（工作区TEMP，exit0），真实进程成功重开、manifest后退出7、输出缺失/同尺寸篡改、取消及旧运行/存储回归；Ruff/Pyright/policy通过。初始默认TEMP权限失败和修复验证如实在任务记录。
- p001_review对29930f62..725fc6a提出P1发布绑定遗漏；当前修复通过payload_kind强制匹配，missing_binding回归通过，尚待新提交独审。旧审查不能写Accepted。
- 2026-11-02新增共享ComparisonSession、CLI、薄GUI及中文docs/wb-v0-acceptance.md。最新CLI/RunSession组合16 passed/56.81秒（.local/p002-final-target-a.txt），Pyright零错误；真实工作台2 passed/5.64秒，局部视觉ship/documenter No changes（详情任务卡）。wheel门禁仅追加同一用例独立安装验证。
- 2026-11-02新执行者01a199d4-dac3-7dd3-af35-cdad7d361934已在产品HEAD78403be接手，真实goal active、无预算，证据work/evidence/B-010/goal-state.json。从旧聊天原生命令记录确认完整门禁completed/exit0（890398ms、1537 passed）及五例冻结生成exit0；接手又对原五工作区实际重开及校验全部保留成果摘要，证据P-002/recovery-verification.json。未重写冻结运行。
- 下一步：非作者p002_independent_review已对29930f62..2591309独审Accepted，独立34项测试与输入篡改/证据核验通过，报告P-002/review-final.md。PR48待四必需CI与正常集成。4.0文档同步须随正常规则回执及阶段集成清单保留。P002为in_review，尚无集成结论，不标done。旧句柄不作为成功依据。
- 最新候选a69b38e810b4fefe1d38fae845c582d17ff56aae：首次PR48 Windows/Linux因两份Markdown Python示例各缺空行在Ruff阶段失败，已最小格式修复和HTML重建；ci-format-fix.json保留前后摘要。独立审查者已核实Accepted可沿用到29930f62..a69b38e（仅文档/证据变化，无产品变化）。当前必需CI run41372266645进行中，rules-context及desktop-environment已通过，foundation Windows/Linux待结果；勿将in_progress当通过。
- 等CI期间仅准备B011及P007–009 planned卡，registry/P004/P005依赖拆分在工作区尚未提交，绝不能推入P002已审PR。先完成PR48，再新分支按新main重新加载B011规则和审查集成。P003/P006仍planned；P004几何方法不作为M1原整数图整卡前置。科学/现场缺项保留。
- 真实goal已get确认active、无token预算。用户明确允许回传目标状态/提交号/执行树，已向原聊天01a19004-3b85-7a30-bc08-c9e59a79d209回传以上状态；无需重复索要同一许可。
- T082科学/目标环境待办、历史失败和冻结源码/安装证据完整保留；原snapshot逐字节归档见archive/P001-before-adoption-snapshot.md。P003–006仅按V0必需范围接入，不因部分实现自动整卡完成。

## 2026-11-02 新用户授权与执行移交

4.0方案已由B010同步到本树，准确源摘要见work/evidence/B-010/transfer-manifest.json。当前产品任务仍P002，不因同步而标完成。新聊天将使用gpt-6.1-sol/medium与真实goal接手，先当前验收，再M1通用执行、M2可视编排；详见docs/plans/phase-2-workflow-authoring.md。旧聊天目前idle/interrupted，不应与新聊天同时写本树。此段优先于历史“仅V0”范围说明。B010同步是本地改动，提交/独审/集成由新执行者正常处理；勿删除旧回执解决CI。
