# 生物图像工具平台

当前集成批次：P0本机技术探针与便携验证，保留未完成的包态交互/干净Windows/DPI缺项；本检出尚无WB正式产品入口。主产品开发在t051独立分支，本批不代表其验收或发布。

**WB需求规划：** [开发规划v2（2026-10-19）](docs/wb-development-plan-v2.md)，仪器目录→Fig/蛋白/固定N清单→明确分配→裁剪→拼图→原像素定量→表格。阶段集成不把规划或P0探针写成新主流程已完成。

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
uv run --locked --no-sync pre-commit install
```

这些命令验证治理工具与P0自动测试；真实桌面、便携包、科学结果与目标机另验。P0入口见[验证手册](tooling/p0/README.md)。本批不增加后续WB产品SDK，不提供尚未实现的package、contract、check --scope命令。

## 维护原则

- 原始输入、已完成结果、最初方案不可覆盖；新的算法定义和数据格式单独版本化。
- 一个明确任务、一个短分支、可复验的检查和绑定提交的审查结论。
- 全部依赖通过锁文件升级；新模块须声明边界、公开 API 与独立安装测试。
- 用户于 2026-10-13 指定使用公开仓库；项目自有代码的开放许可证尚未选定，公开可见不等同于授予开源许可证。第三方技能按各自许可证保留声明。

## 当前限制

实际环境、检查状态和剩余缺口以 [环境验收记录](docs/research/environment-validation.md) 为准。
main 已启用 GitHub rulesets：必须通过 PR 和必需检查、禁止强推与删除；规则回执机制见自动规则门禁手册。CODEOWNERS 和本地 hook 仅作补充。

