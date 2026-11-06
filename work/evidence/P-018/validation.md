# P018 验收记录

研究候选8f947b4已获指定独审pass，尚未集成。预声明提交24373f1；实际研究脚本和研究契约以最终候选提交为准。

| 命令/动作 | 实际结果 |
|---|---|
| dev.py context --task P-018 --scope docs/research --scope work --scope .agent-handoff --scope AGENT_HANDOFF.md --record | 0，基线f8f69b5；通用规则已逐文件读取，重复handoff内容已在恢复时读完 |
| ruff format / ruff check work/evidence/P-018/run_probe.py | 0 / 0；仅本研究脚本 |
| python work/evidence/P-018/run_probe.py work/evidence/P-018/results | 0，Python3.12.14/NumPy2.5.4 |
| 同脚本 .local/p018/reproduce | 0；同目录再次运行1/FileExistsError，预期拒绝覆盖 |

研究内容独审见[原文](independent-review-8f947b4.md)及[独立Decimal收据](reviewer-independent-check.json)，已逐字节复制；最终集成增量与正常PR必需CI待完成。P010历史head缺项如仍出现，保留不修改历史卡。最终上游决定集成，不自合并。

追加自验：policy exit0（233产品文件扫描，无产品变更）；check_plan exit1，既存P010缺reviewed head，与P017收据同因，未修旧卡/门禁。maintain_handoff --compact-if-needed exit0、changed0/warnings0/unresolved0；git diff --check exit0。合成输出三个文件在新目录复跑及拒绝覆盖后逐字节一致。没有扩大本地产品全量测试范围。

## B021主线合并与历史回执处理

实际main为dc2609dd79de98a63d4e8283e6c6db9e7c8e28ba（PR69）；新AGENTS/docs/ai-workflow及持续独审方案已读。合并冲突仅archive/backlog/risks/snapshot/AGENT_HANDOFF；保留主线归档索引、P018风险与当前指针，补B021入口，不改协议/产品。P017最终交付内容保留。

独审准确8f947b4/base f8f69b5的rule_context退出1（历史回执集合未完整登记）如实保留。经上游明确同意，采用dc2609dd中的P017 rules-context.json及integration-context.json原件；这两份是PR68正式集成的原始回执。0d134926收尾重载版仍完整保留在Git祖先，不删除文件、不改门禁/历史摘要，不把收尾重载误作新PR当前清单。相对实际main仅P018回执变化，因此不新增无历史差异的integration清单。

P018 context以准确dc2609dd基线重新生成，scope为docs/research、work、.agent-handoff、AGENT_HANDOFF.md，exit0。研究报告/探针/合成输入输出与已审8f947b4完全不变；不重跑数值或产品矩阵。最终提交的准确rule_context/diff/policy/容量检查及PR地址由上游候选回传记录，CI与增量结论未完成前不称通过。
