# P018 验收记录

当前候选未独审/未集成。预声明提交24373f1；实际研究脚本和研究契约以最终候选提交为准。

| 命令/动作 | 实际结果 |
|---|---|
| dev.py context --task P-018 --scope docs/research --scope work --scope .agent-handoff --scope AGENT_HANDOFF.md --record | 0，基线f8f69b5；通用规则已逐文件读取，重复handoff内容已在恢复时读完 |
| ruff format / ruff check work/evidence/P-018/run_probe.py | 0 / 0；仅本研究脚本 |
| python work/evidence/P-018/run_probe.py work/evidence/P-018/results | 0，Python3.12.14/NumPy2.5.4 |
| 同脚本 .local/p018/reproduce | 0；同目录再次运行1/FileExistsError，预期拒绝覆盖 |

尚待：规则按实际main重载、政策/计划检查、容量与diff、候选冻结、上游指定独审、正常PR必需CI。P010历史head缺项如仍出现，保留不修改历史卡。最终上游决定集成，不自合并。

追加自验：policy exit0（233产品文件扫描，无产品变更）；check_plan exit1，既存P010缺reviewed head，与P017收据同因，未修旧卡/门禁。maintain_handoff --compact-if-needed exit0、changed0/warnings0/unresolved0；git diff --check exit0。合成输出三个文件在新目录复跑及拒绝覆盖后逐字节一致。没有扩大本地产品全量测试范围。
