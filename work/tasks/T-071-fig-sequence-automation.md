# T-071 Fig顺序分配、一键启动与整批自动导航

- 状态：实施中。2026-10-20用户批准T070完整方案，已登记active计划目标，授权在新树持续至绑定独审、PR集成和新离线候选交付。
- 基线：main6916b3a816b9a547ffdedf032a9dba82ce119c9d；规划来源提交0a966e84c7c07ca26dd71fade4dfe27e6bb4e435；新受管树C:/Users/70236/.codex/worktrees/wb-fig-sequence/bioimage-tools-platform，分支codex/fig-sequence-automation。旧规划树/所有其他树dirty、原图、项目、历史结果和T069安装保持。
- 需求：顶部Fig名/N/有序蛋白条目，跨Fig连续分配完整采集组，手选组内来源；一个启动入口完成保存/校验/确认/冻结。整批全部裁剪→全部拼图→全部原像素定量→统一结果，真实提交驱动切页，仅人工处理时暂停，修正后断点继续。
- 范围：tools/wb、apps/desktop、tests、tooling（仅交付/诊断）、docs、work、.agent-handoff、AGENT_HANDOFF.md、README.md、PRODUCT.md、.impeccable/surfaces、uv.lock（仅本地产品版本元数据；不升级第三方依赖）。不改平台包、门禁、技能或工作流。
- 顺序：版本化草稿/纯顺序映射与兼容→正式顶部配置/选源→保存CAS/单一启动→版本化整批调度/进度导航→暂停修正/恢复/输出→实际发货UI与指定真实目录回归→冻结全门禁一次/非作者独审→四CI/精确合main→新独立安装候选/载荷与SHA/manifest/交接。
- 验收：至少两Fig的真实事件证明全部crop完成后才compose、全部compose提交后才measure；筛选不改映射，缺组/余组/空名/重复名/顺序/N/来源修改与保存重开；IME/焦点/忙态、取消和旧消息保护，人工复核期间不抢页；旧清单/账本wire及语义保持，8/16/RGB原值、历史和灰度/OCR保持。
- 权限：普通实现自主，仅无法消解数据歧义集中询问；私图不上Git/外部API，不覆盖旧包/项目/原图，不自动正式Release或扩工具。干净Win10/物理DPI/科学留出及历史native UNKNOWN继续单列。
- 证据：work/evidence/T-071；T070历史回执原样保留且绑定来源提交，最终PR使用T071唯一当前回执与显式integration-context，不删历史回执解决门禁。
