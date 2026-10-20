# 生物图像工具平台

当前增量按[采集组主流程与交付计划](docs/wb-grouped-intake-plan.md)推进：采集组网格、Fig级N、来源选择和草稿接入已有自动化主链，再完成快捷键、算法盘点及新离线测试版。用户已确认执行；当前任务见[交接入口](AGENT_HANDOFF.md)。该计划的待办不表示已经完成。

当前WB需求以[开发规划v2](docs/wb-development-plan-v2.md)为准，实施见[E0–E7执行计划](docs/wb-execution-plan.md)：清单、固定N原值裁剪、拼图后原像素定量、稳定槽表格、导出与恢复。E0–E7工程实现、独审及主线集成已完成；两平台910项完整门禁及全部隔离wheel通过，独立测试安装候选在本机Win11通过双流程和生命周期验证，独立灰度与OCR保留。科学留出、明确样本配对、干净目标Win10和物理DPI仍待验，不代表正式发布。详见[验收索引](docs/wb-execution-acceptance.md)和T060证据。

当前阶段：**WB 工作台开发。已接入原图自动识别、裁图、灰度复核、拼图、导出与保存重开；8张真实原图裁图回归已通过，科学泛化、积分真值与最终发布验收仍未完成。** 实际门禁状态以当前任务和验证记录为准。

最初的 [V3.0 技术方案](生物图像工具平台与全AI长期迭代技术方案.pdf) 保持原样，首次提交可追溯。
本仓库将承载 Windows 本地桌面平台及 WB、IF、IHC 工具，采用 Python/PySide6、独立计算进程、单仓库分包的候选路线。产品选型须经 P0 打包与目标机试验后冻结。

## 从这里开始

1. [执行规则](AGENTS.md) → [交接入口](AGENT_HANDOFF.md) → 当前任务。
2. [技术调研与决策](docs/research/2026-10-13-foundation.md)。
3. [模块地图](docs/module-map.md)、[架构](docs/architecture.md)、[代码规范](docs/coding-standards.md)。
4. [开发环境](docs/runbooks/development.md)、[工具与技能来源](docs/research/skills-and-plugins.md)。
5. [贡献流程](CONTRIBUTING.md)、[AI 开发流程](docs/ai-workflow.md)、[发布与恢复](docs/runbooks/release.md)。
6. [自动规则门禁](docs/runbooks/rule-enforcement.md)、[调研与非编码能力](docs/research-protocol.md)。

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
