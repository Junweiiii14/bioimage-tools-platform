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

| 2026-10-14 | JSON 原字节 strict 解析 + 标签/重复键预检；worker 仅产出候选 | 保持 stdlib dataclass 唯一字段，避免 bool 标签与 JSON tuple 模式问题；终态由宿主提交 | docs/contracts/wb-worker-v1.md |

| 2026-10-14 | 新平台包仅管理 opaque 文档/资产/修订/运行，结果先文件发布后 DB CAS | 实际输入/草稿/请求/结果复用；保留未知目录而不假成功或删除 | docs/contracts/workspace-v1.md |

| 2026-10-14 | 多图行计划使用独立wb_figure_project v1，旧单图v1/v2与数值协议不变；显示拼图和原值裁剪同时归档 | 防止一个source定量协议被静默改成多源/8位合成；明确人工审核和来源、不同Fig宽度允许但同Fig不拉伸 | docs/contracts/wb-figure-project-v1.md；T-012的230全量/真实10图导入重开 |
