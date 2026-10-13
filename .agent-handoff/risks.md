# Risks, Blockers, And Unknowns

## Current Blockers

- GitHub 私有仓库 rulesets API 返回套餐限制 403，服务器保护未生效。不要改为公开绕过。

## Current Risks

- P0 仍未进行，Qt/worker/standalone 和真实数据行为不因环境安装而成立。
- AST 边界检查仅检查直接导入；首个真实包必须启用 import-linter 与隔离 wheel 测试。
- 本任务作者自验不是独立审查；后续产品变更须有绑定 head 的审查证据。
- Python 3.12 生命周期至预计 2028-10，P0 需评估长期基线。

## Unknowns / Confirmations Needed

- 发布编译器最终路线、真实样本、签名/许可证、目标机性能和数据迁移：未实现产品阶段的待验证事项。
