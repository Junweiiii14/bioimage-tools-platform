# Decision Log

| Date | Decision | Reason | Evidence |
| --- | --- | --- | --- |
| 2026-10-13 | 先建治理和环境，产品 P0 仍待启动 | 用户最新范围；不把方案变成执行授权 | docs/adr/0001-foundation-before-product.md |
| 2026-10-13 | 原始 PDF 保持原样、单仓库分包 | 保留长期方案来源和可回滚历史 | 初始提交与 policy 摘要 |
| 2026-10-13 | Skills 项目安装、完整 SHA 锁定 | 可复现、可审查、降低全局上下文负担 | tooling/skills-lock.json |
| 2026-10-13 | 私有仓库不改公开性以绕过套餐 | 用户资料访问范围保持私有 | GitHub rulesets API 403 |
