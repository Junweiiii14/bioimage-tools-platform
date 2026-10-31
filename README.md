# 生物图像工具平台

## 研发与任务入口（2026-10-31）

[研发总方案3.0与HTML](docs/plans/README.md) · [第一阶段V0](docs/plans/phase-1-v0.md) · [公开开发数据](docs/plans/development-data.md) · [任务依赖](work/programs/scientific-agent-platform/README.md)。新路线包含10类实验，当前启动范围是V0旧WB独立运行；下方保留已有实验室产品使用说明。方案发布不表示新功能或本地T082已合入main。

当前交付入口：[T079实验室离线发行](work/tasks/T-079-laboratory-offline-delivery.md) → [实验室部署说明](docs/wb-laboratory-delivery.md) → [交接索引](AGENT_HANDOFF.md)。本轮收拢T074–T077的曲线、整版拼图、界面系统、文件夹拖入与未审核导出整改，并提供包含运行环境的Windows x64安装器。

历史版本及证据保留，旧检查不作为本轮通过证明。实验室发行的实际安装验证、源码集成和目标机限制以T079记录为准；科学留出、干净Win10与物理DPI验收另列。开发范围保持WB，IF/IHC不自动扩展。

实验室使用者运行随附Setup.exe即可安装，包含私有Python、Qt/WebEngine、本地OCR模型和VC运行库，无需开发环境或Office。安装目标为Windows10 1809+或Windows11的x64机器，按当前用户安装；首次部署运行开始菜单环境自检并用合成练习素材核对流程。构建配方为 `python -m tooling.build_runtime_candidate --laboratory --iscc <固定编译器> --gcc <固定编译器>`；只从干净提交构建，安装器通过实验室交付包分发，不自动公开上传二进制。

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
