# P018 最终增量独审

2026-11-06；审查窗口 `01a1af0d-808e-7131-ae29-237aded27938`。**结论：pass（准确研究/集成增量）；历史回执覆盖问题已关闭。** PR70仍须准确候选必需CI成功后由上游安排正常集成，本报告不宣称CI已完成或科学准入。

- PR：https://github.com/Junweiiii14/bioimage-tools-platform/pull/70
- Base：`dc2609dd79de98a63d4e8283e6c6db9e7c8e28ba`
- Candidate：`bff711c1df1b42fee6de99985f16ce616c3b01a8`
- 原研究独审：`8f947b4e67fbf53bcd926b37a1a2f56b8e5343ea`
- 检出：独立`bioimage-review-p018`；tracked干净，未修改开发树。

## 独立核对

1. 研究报告、README、run_probe.py及全部三份结果相对原独审候选git diff exit0；登记增量也未变。原数值、来源及软件研究范围pass可沿用，本轮没有重跑未变化的数值或产品矩阵。
2. AGENTS、ai-workflow、plans、P017全部证据及两份历史回执、产品、锁与门禁相对实际main diff exit0；未混入B021本地收尾7a0d718。没有删回执、弱化门禁或修改受保护算法。
3. 原始独审Markdown和JSON经Git换行归一化后与主审`.local`原件完全相同；原署名、旧基线/候选、第一次规则失败及科学/产品/CI未验边界保留。报告内容归一化SHA256为`ee552fe65c1b4d2f35bfa25d209f6ddb1ec60e109f7cd0416c2cb1a528e4968e`，JSON为`8f35d501db4a93bc2a66e2766ca7f6e947eecc7e3b7db38713ab19915c7fb170`。
4. 当前P018回执与任务卡base均为dc2609dd。相对该base，仅`work/evidence/P-018/rules-context.json`一份回执变化，没有额外历史receipt差异；不需要虚构integration清单。0d134926仍为候选祖先，原收尾加载版本可追溯。
5. 主审实际执行 `uv run --locked --no-sync python -m tooling.rule_context check --base dc2609dd79de98a63d4e8283e6c6db9e7c8e28ba --head bff711c1df1b42fee6de99985f16ce616c3b01a8`，exit0；原`Integration must list every extra historical receipt exactly`问题已在当前base/head关闭。未改写旧exit1为成功。
6. 准确base..head `git diff --check` exit0；独立只读子审核对增量亦无阻断。审查时GitHub PR70实际base/head一致，rules-context与desktop-environment已成功，Windows/Linux质量检查仍在运行。

## 下一步与边界

没有新增阻断发现或要求开发代码整改。保持候选不变，完成必需CI，由上游安排正常合入并核对main与已审树。后续如果相关文件变化，仅复审受影响增量。科学、真实板、LoD/LoQ、真人、产品CSV/GUI、安装/目标机等原未验项仍保留，研究pass不替代这些结论。

独立核对JSON在审查树`.local/incremental-check-bff711c.json`。本报告交回上游；不为纳入本次小收据重推冻结候选/重启CI，后续正常任务或本地收尾按真实来源保存即可。
