# T-071 Fig顺序分配、一键启动与整批自动导航

- 状态：本轮工程交付完成。产品独审/四必需检查后PR30精确集成main710bb85；新独立离线候选构建、安装、三流程/PS5.1/7,751载荷校验及最终非作者产物审计Accepted。最终证据随本次文档PR正常集成；二进制来源仍为冻结main710bb85。
- 用户2026-10-20已批准[T070完整方案](../../docs/wb-fig-sequence-automation-plan.md)，全文已登记active计划目标，授权持续至独审、PR集成和新离线测试版。普通实现自主，仅无法消解的数据歧义集中询问。
- 需求已落实：顶部Fig名、每Fig一次N、有序蛋白名；跨Fig连续分配完整采集组，组内手选原图；一个入口保存/校验/确认/冻结并启动。整批全部裁剪→全部拼图→全部原像素定量→统一结果；真实提交自动切页，人工问题暂停，修正后单一继续。浏览/输入/草稿保护及重开不自动运行。
- 唯一数据澄清已回答：只编号19个仪器采集组，28参考组保留单列、不占蛋白顺序；全部47组原身份保留。没有待答问题。
- 基线main6916b3a；新受管树C:/Users/70236/.codex/worktrees/wb-fig-sequence/bioimage-tools-platform。规划来源0a966e8，仅复制四份明确规划证据；旧wb-grouped-intake/codex/fig-sequence-plan和所有其他树原有dirty保持。
- 实现与兼容：grouping@2/manifest4保存顺序草稿、缺组/显式排除，旧wire不改；workflow@3整批屏障、异常全批暂停，旧策略不静默迁移；单一启动/继续保留原CAS、代际/取消保护及历史复用。平台/数值公式/原始数组/第三方依赖/门禁/技能不扩展或改写。
- 范围回执：tools/wb、apps/desktop、tests、tooling、docs、work、.agent-handoff、AGENT_HANDOFF.md、README.md、PRODUCT.md、.impeccable/surfaces、uv.lock（仅项目版本元数据）。产品PR保留T070历史回执及显式integration-context；文档收尾按main710bb重新加载T071回执，不删除旧记录。
- 产品提交依次edb5a5e、2a676e3、c9355ba、20c106f、a952555、5f2090a。非作者代码/兼容/实际数据证据复审Accepted，UI限定范围ship；局部发现与修复、验证边界见[独审](../evidence/T-071/independent-review.md)。
- 最终门禁：本机启动源a952为979/825.65s、raw child0/全部wheel/OCR/check0；5f专项及最终CI独立覆盖，Windows979/615.77s、Linux979/332.14s及全部wheel/OCR/check0。四required SUCCESS后2026-10-20T18:18:14Z正常合main710bb85de99e88a970f4d0f5613ca554b705ecf7；非作者确认tree与5f相同。
- 新交付：[T071交付记录](../../docs/wb-fig-sequence-delivery.md)。冻结main710bb构建，安装器361,622,169字节/SHA256760b3ee0d7e9c3d22f8f470185791f3c11b26f051babce2c3d4d94f57df75c94。独立AppId/目录/设置/快捷方式，旧T069仍冻结6080867、不覆盖。
- 数据保护：当前三目录104文件/85TIFF/76内容，19回归Fig/74槽，19初始真实worker和一次局部修订；其他18 Fig及旧输出保留。非作者38裁剪逐数组核对、208历史资产摘要、81阶段快照及新旧输出通过。104文件本轮初始逐项清单仅内存，持久比较用既有T069清单的对应子集，不能补称已有本轮持久启动清单。
- 原失败均保留：[验证](../evidence/T-071/validation.md)、[最终CI](../evidence/T-071/final-ci.md)、[关闭现场](../evidence/T-071/windows-close-order.md)。新诊断曾漏节流阶段、过早点击与错误原生预览前置，均保留实际失败；a541旧手动坐标偏差、历史native及Subclass抓图异常仍UNKNOWN。无测试容差/skip/忽略或门禁削弱。
- 外部验收边界：已见参照辅助开发回归，不报生物配对/科学准确率；干净Win10、物理DPI/按钮、独立真值/留出仍待验。未正式Release、未升级依赖、未扩其他工具，不恢复被用户停止的原生CUA。
