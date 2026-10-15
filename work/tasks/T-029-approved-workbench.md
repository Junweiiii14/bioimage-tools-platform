# T-029 已批准自动化工作台实施

- 状态：implementing。
- 用户2026-10-15批准T-028整套方案实施，特别要求交互动效和审美。审批门槛已解除，不重复征询普通实现选择。
- 唯一设计依据：work/evidence/T-028/UI全面审核与改版方案.md；Taste product-performs/Impeccable Operate，原生Qt，图像中心三栏。保留科学语义和全部OCR/模板/归一化能力。
- 工作树：复用t021-coordination协调，分支codex/t029-approved-workbench；原仓库dirty不动。子代理独立worktree承担平台入口(T-030)、三栏复核(T-031)、上下文工具(T-032)，根代理负责宿主集成/动效与设计系统/验证。
- 范围：apps/desktop、tools/wb、docs、work、.agent-handoff、PRODUCT.md、DESIGN.md、.impeccable。新公共契约仅在必要时扩展范围并加载规则。
- 动效：主要动作反馈100–150ms，视图连续性160–220ms，面板展开180ms；无长入场/弹跳/持续装饰循环。尊重系统减少动画及应用减少动效选项；中断切换不阻塞操作，图像像素和测量值不参与动画。
- 验收：选原图无需空目录；自动处理/实际异常状态；三栏图上调整和结果失效；OCR/模板/输出不回归；真实10图流程、1100/1440及DPI、取消/恢复、独立提交绑定审查。
- 产品检查未运行，实施未完成，不能预报通过。
