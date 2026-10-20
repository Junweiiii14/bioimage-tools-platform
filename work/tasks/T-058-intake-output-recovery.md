# T-058：E5身份填表、导出与阶段恢复

- 状态：done（本机源码工程阶段）；base9d747ef，E4产品ff89867已通过843完整门禁/全部隔离wheel/真实OCR及绑定独审。
- 授权：沿docs/wb-execution-plan.md连续E0–E7，不设定时、不重复索批；仅最新t051树/codex/wb-e0-e7，原dirty树/输入/历史保持。
- 范围：tools/wb、apps/desktop、tests、tooling/installed_wheels.py、docs、.impeccable、PRODUCT.md、DESIGN.md、AGENT_HANDOFF.md、.agent-handoff、work/tasks/T-058-intake-output-recovery.md及work/evidence/T-058。
- 目标：按稳定Fig/蛋白行/槽位和已核验冻结run填表；有效/原始积分/待算/缺失/复核/失败区分，不按显示行号写值。完整结果输出与重复导出用新根目录，保留清单、原值/显示裁剪、Fig、CSV/XLSX、来源/算法/状态与可恢复归档。
- 设计：版本化schema14/intake_output@1及表格审计身份；保留旧1–13字节与读取语义。复用ProjectArchiveSession、verify_project_evidence及已有有界归档/无覆盖发布，不建第二成功收据；导出完成证据真实导入、CAS后才更新阶段。部分失败输出明示缺口，不能伪装完整归档成功。
- 恢复：阶段完成点重开；未知活动阶段interrupted并重新批准执行，半成品重新生成到新目录，不承诺算法内部续算。原图变化/缺失列异常；本机和外来归档运行来源保留，不注册外来PID为本机成功。
- 验收：同名蛋白/固定槽位不串值，旧归档表与结果摘要不变；重复导出、取消、迟到/保存失败、写盘不足、变源、重开/旧归档再导出；核心/性质/真实宿主/公开wheel/完整门禁及最终提交非作者独审。
- 限制：不猜样本/内参/跨蛋白对应；独立灰度/OCR保留。科学留出、干净Win10/DPI、旧原生purecall UNKNOWN不因本阶段销账；正式发布未执行。
- 当前候选：8feffce；真实宿主/恢复/故障及UI完成，独审两P2均resolved/最终绑定8fe无新P0–P2，UI disposition: ship。最终全量check0：858/623.78s、原child0、9契约、全部隔离wheel/真实OCR；实际证据见work/evidence/T-058/validation.md。
- 下一步：自动进入T059/E6性能、结构与交互收敛；科学、真实确认批次、干净Win10/物理DPI、main/安装版分别留待对应验收，不阻断独立工作。
