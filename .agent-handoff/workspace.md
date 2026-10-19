# Workspace Map

## Repository Structure

- 根：AGENTS / README / CONTRIBUTING / pyproject / uv.lock / dev.py。
- docs/module-map.md：现存基础设施与规划产品模块严格区分。
- work/tasks：任务状态唯一来源；work/evidence：实际验证记录。
- .agents/skills：固定 SHA 的第三方技能；tooling/skills-lock.json 校验来源。

## Main Entry Points

源码桌面入口为 `uv run --locked --no-sync python -m bioimage_app`，多源项目可加 `--figure-project`。WB公开入口wb_tool.api，说明tools/wb/README.md；宿主公开入口bioimage_app.api。P0探针为p0_probe.py，开发检查为dev.py。使用本项目.venv或uv；最终Windows包仍待验收。

规则入口 `dev.py context --task <ID> --scope <目录> --record`，生成当前规则版本回执；`.github/workflows/rules-context.yml` 在 PR 校验。完整安装后本地命令加 `uv run --locked --no-sync` 保持桌面/构建依赖。

## Test Entry Points

`uv run --locked --no-sync python dev.py check --all`；额外桌面环境烟测与真实窗口验收分开记录。

## Docs And Specs

原始 PDF 不变。docs/architecture.md、coding-standards.md、ai-workflow.md、research/ 与 runbooks/。

## Durable Project Context

候选产品 Python/PySide6 桌面单体＋独立 worker；治理已建设，WB 核心已开始。兄弟项目的归档工作流不适用。

## Project Conventions

短分支与真实证据；原始数据不可覆盖；数值、协议、schema 独立版本。第三方技能安装项目范围，未改全局模型和权限。
