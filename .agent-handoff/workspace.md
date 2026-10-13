# Workspace Map

## Repository Structure

- 根：AGENTS / README / CONTRIBUTING / pyproject / uv.lock / dev.py。
- docs/module-map.md：现存基础设施与规划产品模块严格区分。
- work/tasks：任务状态唯一来源；work/evidence：实际验证记录。
- .agents/skills：固定 SHA 的第三方技能；tooling/skills-lock.json 校验来源。

## Main Entry Points

产品入口不存在。开发入口为 dev.py；使用本项目 .venv 或 uv，避免系统 Python 商店别名。

## Test Entry Points

`uv run --locked python dev.py check --all`；额外桌面环境烟测见开发手册。

## Docs And Specs

原始 PDF 不变。docs/architecture.md、coding-standards.md、ai-workflow.md、research/ 与 runbooks/。

## Durable Project Context

候选产品 Python/PySide6 桌面单体＋独立 worker；治理已建设，业务未启动。兄弟项目的归档工作流不适用。

## Project Conventions

短分支与真实证据；原始数据不可覆盖；数值、协议、schema 独立版本。第三方技能安装项目范围，未改全局模型和权限。
