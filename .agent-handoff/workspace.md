# Workspace Map

## Repository Structure

- 根：AGENTS / README / CONTRIBUTING / pyproject / uv.lock / dev.py。
- docs/module-map.md：现存基础设施与规划产品模块严格区分。
- work/tasks：任务状态唯一来源；work/evidence：实际验证记录。
- .agents/skills：固定 SHA 的第三方技能；tooling/skills-lock.json 校验来源。

## Main Entry Points

当前活动检出为 `C:/Users/70236/.codex/worktrees/wb-fig-sequence/bioimage-tools-platform`，收尾分支codex/fig-sequence-delivery；二进制冻结main710bb85。桌面“BioImage WB（Fig 顺序自动化测试版）”指向 `%LOCALAPPDATA%/Programs/BioImage WB Fig 顺序自动化测试版`，见[T071交付](../docs/wb-fig-sequence-delivery.md)。旧T069/6080867采集组安装、原规划树dirty及其他历史树保持；旧入口名称不证明其指向最新版本，启动前核对目标，不自动改写旧入口。

在本活动检出中，`Start-BioImage.ps1`固定自身检出；源码命令 `uv run --locked --no-sync python -m bioimage_app`、历史 `--figure-project` / `--platform` 均进入绿色WebWorkbenchWindow，旧原生窗口仅显式 `--legacy-*` 兼容诊断使用。WB公开入口wb_tool.api，说明tools/wb/README.md；宿主公开入口bioimage_app.api。P0探针为p0_probe.py，开发检查为dev.py。使用对应检出的.venv，禁止从历史树启动并当作当前产品；本机Win11候选通过不代表干净Win10/物理DPI/科学验收已完成。

规则入口 `dev.py context --task <ID> --scope <目录> --record`，生成当前规则版本回执；`.github/workflows/rules-context.yml` 在 PR 校验。完整安装后本地命令加 `uv run --locked --no-sync` 保持桌面/构建依赖。

## Test Entry Points

`uv run --locked --no-sync python dev.py check --all`；额外桌面环境烟测与真实窗口验收分开记录。

## Docs And Specs

原始 PDF 不变。docs/architecture.md、coding-standards.md、ai-workflow.md、research/ 与 runbooks/。

## Durable Project Context

候选产品 Python/PySide6 桌面单体＋独立 worker；治理已建设，WB 核心已开始。兄弟项目的归档工作流不适用。

## Project Conventions

短分支与真实证据；原始数据不可覆盖；数值、协议、schema 独立版本。第三方技能安装项目范围，未改全局模型和权限。
