# T-052 规划核验

- 日期2026-10-19；环境Windows/PowerShell；实际源码树t051-instrument-intake；HEAD536f04eed4de72d9a9a7c8eb6b7afbf065f7be15，产品65ff278。
- 原ResearchVault树bb5601a/feat/T-021-laboratory-figure-layout有既存dirty；只读核对，未覆盖。首次尝试旧handoff指向的t021-coordination/bioimage-tools-platform失败（不是Git检出且snapshot不存在），随后以git worktree list找到真实T051树，未修复旧树。
- 阅读T050需求v2、T051任务/契约、最新handoff、模块README及架构约束；抽查AutomaticWorkflow、automatic_export、figure_image_export、figure_export。旧链定位后定量，多格式调用各自渲染得到源码支持；没有逐文件全仓审计或科学准确率结论。
- PowerShell Measure-Object -Line盘点非空行：figure_window2269、figure_view1661、web_bridge758；不是复杂度/缺陷数量或物理总行数。
- context --task T-052 --scope docs --scope work/tasks/T-052-repository-optimization-plan.md --scope work/evidence/T-052 --scope .agent-handoff --record：退出0；已读取当前与基线规则，包含显式分阶段集成要求。规则回执保留。
- T051的801测试/9契约/全部wheel与独审为已有证据，本轮未重跑。全门禁、安装包、真实仪器留出、科学真值、干净Win10/DPI、独立规划审查、远端PR/CI实时核验均未执行。
- 本轮改动限执行规划、任务、规则回执及交接；没有产品、算法、schema、依赖锁或门禁变更；未提交/推送/发布，未创建定时任务。

## 本轮文档检查

- dev.py policy退出0（输出boundary scan 135 files）；仅表示现有离线policy通过。
- 新规划本地链接存在性、E0–E7完整性与用户确认条件检查退出0；git diff --check退出0。
- maintain_handoff.py --repo . --compact-if-needed退出0，unresolved=0；自动轮转1段旧work-log并更新archive索引，历史先归档后整理。
