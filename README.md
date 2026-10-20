# 生物图像工具平台

本轮[Fig顺序方案](docs/wb-fig-sequence-automation-plan.md)已实现顶部Fig名/每Fig一次N/有序蛋白配置、跨Fig连续分配、组内手选原图及一次启动；整批裁剪→拼图→原像素定量→结果按真实提交自动切页，人工问题暂停后单一继续。PR30四必需检查及两平台979项/全部wheel/OCR通过，main710bb85的新独立离线候选已构建、安装并通过三流程与PS5.1自检。摘要和验收边界见[T071交付](docs/wb-fig-sequence-delivery.md)；旧[T069交付](docs/wb-grouped-intake-delivery.md)及原图/历史/旧未提交改动保持。[迭代/证据导航](docs/iterations.md)与[交接入口](AGENT_HANDOFF.md)保留实际初败和当前任务指针。

当前WB需求以[开发规划v2](docs/wb-development-plan-v2.md)为准，实施见[E0–E7执行计划](docs/wb-execution-plan.md)：清单、固定N原值裁剪、拼图后原像素定量、稳定槽表格、导出与恢复。E0–E7工程实现、独审及主线集成已完成；两平台910项完整门禁及全部隔离wheel通过，独立测试安装候选在本机Win11通过双流程和生命周期验证，独立灰度与OCR保留。科学留出、明确样本配对、干净目标Win10和物理DPI仍待验，不代表正式发布。详见[验收索引](docs/wb-execution-acceptance.md)和T060证据。

当前阶段：**WB 本机工程测试。当前三目录85 TIFF/19执行组＋28参考组的已见开发回归已走通，979项两平台检查、独立wheel/OCR与新安装候选三流程通过；科学真值/留出、干净Win10、物理DPI和正式发布仍未完成。** 历史95 TIFF清单不改写；实际状态以[T071](work/tasks/T-071-fig-sequence-automation.md)和验证记录为准。

最初的 [V3.0 技术方案](生物图像工具平台与全AI长期迭代技术方案.pdf) 保持原样，首次提交可追溯。
当前WB采用Windows本地Python/PySide6、独立计算进程及单仓库分包；IF/IHC保留为后续单独任务。目标机验收缺口单列，已授权WB技术栈继续完成工程交付。

## 从这里开始

1. [执行规则](AGENTS.md) → [交接入口](AGENT_HANDOFF.md) → 当前任务。
2. [技术调研与决策](docs/research/2026-10-13-foundation.md)。
3. [模块地图](docs/module-map.md)、[架构](docs/architecture.md)、[代码规范](docs/coding-standards.md)。
4. [开发环境](docs/runbooks/development.md)、[工具与技能来源](docs/research/skills-and-plugins.md)。
5. [贡献流程](CONTRIBUTING.md)、[AI 开发流程](docs/ai-workflow.md)、[发布与恢复](docs/runbooks/release.md)。
6. [自动规则门禁](docs/runbooks/rule-enforcement.md)、[调研与非编码能力](docs/research-protocol.md)。
7. [WB算法入口与消费者](docs/wb-algorithm-inventory.md)、[迭代索引](docs/iterations.md)、[离线测试版里程碑](https://github.com/Junweiiii14/bioimage-tools-platform/milestone/1)。

## 可执行的基础检查

安装 uv 0.13.0，使用 Python 3.12.14（uv 自动下载），在仓库根运行：

```powershell
uv sync --locked --all-groups
uv run --locked --no-sync python dev.py doctor
uv run --locked --no-sync python dev.py check --all
uv run --locked --no-sync python dev.py smoke-env
uv run --locked --no-sync python -m bioimage_app
uv run --locked --no-sync pre-commit install
```

检查验证数值/输入/真实worker、工作区事务、Qt存储与手工界面、导入边界和四个独立wheel（五种安装场景）。便携包和目标机性能另外验收。P0见[验证手册](tooling/p0/README.md)，WB见[模块说明](tools/wb/README.md)，工作区见[存储说明](packages/platform_runtime/README.md)。不提供 `package`、`contract`、`check --scope` 的空壳成功命令。

日常启动统一使用上面的无参数命令，默认打开当前绿色 WB 工作台；历史
`--figure-project` 和 `--platform` 参数也转入同一工作台。旧 Qt 窗口仅作为明确的
`--legacy-*` 兼容工具保留，详见桌面模块说明。`dev.py check --all` 中的 Qt 测试和
安装验证默认离屏运行；直接运行 pytest 也默认离屏，不会把测试窗口弹到桌面。
Windows 也可运行本检出目录的 `Start-BioImage.ps1`；它固定使用自身所在目录，避免
终端仍在旧检出目录时启动另一个版本。直接 pytest 只有在显式设置
`QT_QPA_PLATFORM=windows` 时才运行可见的交互诊断；常规门禁始终离屏。

## 维护原则

- 原始输入、已完成结果、最初方案不可覆盖；新的算法定义和数据格式单独版本化。
- 一个明确任务、一个短分支、可复验的检查和绑定提交的审查结论。
- 全部依赖通过锁文件升级；新模块须声明边界、公开 API 与独立安装测试。
- 用户于 2026-10-13 指定使用公开仓库；项目自有代码的开放许可证尚未选定，公开可见不等同于授予开源许可证。第三方技能按各自许可证保留声明。

## 当前限制

实际环境、检查状态和剩余缺口以 [环境验收记录](docs/research/environment-validation.md) 为准。
main 已启用 GitHub rulesets：必须通过 PR 和必需检查、禁止强推与删除；规则回执机制见自动规则门禁手册。CODEOWNERS 和本地 hook 仅作补充。
