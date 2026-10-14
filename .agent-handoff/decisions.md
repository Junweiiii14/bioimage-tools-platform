# Decision Log

| Date | Decision | Reason | Evidence |
| --- | --- | --- | --- |
| 2026-10-13 | 先建治理和环境，产品 P0 仍待启动 | 用户最新范围；不把方案变成执行授权 | docs/adr/0001-foundation-before-product.md |
| 2026-10-13 | 原始 PDF 保持原样、单仓库分包 | 保留长期方案来源和可回滚历史 | 初始提交与 policy 摘要 |
| 2026-10-13 | Skills 项目安装、完整 SHA 锁定 | 可复现、可审查、降低全局上下文负担 | tooling/skills-lock.json |
| 2026-10-13 | 原先保持私有，后被用户明确公开要求取代 | 用户最新指示优先 | F-002、GitHub visibility PUBLIC |
| 2026-10-13 | 规则加载回执与必需 CI，不绕过 hook 信任 | 无需逐次人工提醒、可复验；不冒充理解证明 | docs/runbooks/rule-enforcement.md |
| 2026-10-13 | 用户授权 T-002/P0，本机先验收，干净机后续 | 最新指示取代“P0 待启动”；不扩展 T-001/WB | work/tasks/T-002-p0-validation.md |
| 2026-10-13 | 可丢弃技术探针与正式产品包分开 | 先证明 Qt/worker/standalone，不预建平台 SDK | tooling/p0/README.md |

| 2026-10-14 | 用户授权持续开发 WB；先冻结参考后产品核心 | 最新指令替代仅限 P0；无第二消费者不预建公共包 | work/tasks/T-003-wb-product.md |

| 2026-10-14 | TIFF 以元数据识别颜色轴，MINISWHITE 原值保留且要求显式极性 | 避免显示或静默反相改变定量意义 | docs/contracts/wb-reference-v1.md |

| 2026-10-14 | dtype_limits_review@1 将上下限像素标为待复核而非证明饱和 | 原始积分可检查但不直接进入有效列；不将异常伪装为零 | docs/contracts/wb-manual-analysis-v1.md |
