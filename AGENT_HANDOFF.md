# Agent Handoff Index

> Entry point for durable agent handoff memory in this repository.
> Read this file first, then follow the Recovery Reading Order below.

## Maintenance Contract

- Keep this file short. It is an index and recovery route, not a work log.
- Keep task status in `work/tasks/<ID>-*.md`; snapshot stores the current pointer and next actions, replacing stale fields.
- Store durable facts, decisions, validation, backlog, risks, and archives in the dedicated files listed below.
- Keep all content factual and repository-based. Mark uncertainty as `UNKNOWN`.
- Do not include secrets, credentials, long logs, full code blocks, or chat transcript dumps.
- Before final response for any non-trivial task, update the relevant `.agent-handoff/` files.

## Handoff Layout

- `.agent-handoff/snapshot.md`: Current objective, status, next actions, active files, blockers, and open questions.
- `.agent-handoff/workspace.md`: Repository map, entry points, test commands, docs, and stable project context.
- `.agent-handoff/decisions.md`: Important decisions with reasons and evidence.
- `.agent-handoff/work-log.md`: Recent operational work log.
- `.agent-handoff/validation.md`: Validation commands/checks, results, and caveats.
- `.agent-handoff/backlog.md`: Pending work and follow-ups.
- `.agent-handoff/risks.md`: Risks, blockers, unknowns, and user/source confirmations needed.
- `.agent-handoff/archive.md`: Compressed old history that is not part of normal startup.
- `.agent-handoff/archive/`: Automatically rotated history chunks, each capped at 128 KiB.

## Size And Rotation Policy

- Snapshot soft limit: 16 KiB or 240 lines. Hard limit: 32 KiB or 400 lines.
- Work log limit: 64 KiB or 30 dated sections. Validation limit: 64 KiB or 200 table rows.
- Backlog and risks limit: 32 KiB each. Only completed backlog items may be archived mechanically; risks require Agent review.
- After updating handoff state, run the installed `agent-handoff/scripts/maintain_handoff.py --repo <repo> --compact-if-needed` when available.
- Maintenance must archive before replacing, preserve complete records, and leave unparseable or semantically unsafe content unchanged for Agent repair.

## Recovery Reading Order

1. Read this file.
2. Read `.agent-handoff/snapshot.md`.
3. Read `.agent-handoff/risks.md`.
4. Read `.agent-handoff/backlog.md`.
5. Read `.agent-handoff/validation.md` only if validation state matters for the current task.
6. Read `.agent-handoff/decisions.md` only when changing architecture, behavior, dependencies, or prior decisions.
7. Read `.agent-handoff/workspace.md` only when orientation, commands, entry points, or subproject boundaries are needed.
8. Read `.agent-handoff/work-log.md` only when recent implementation details are needed.
9. Read `.agent-handoff/archive.md` only when explicitly needed for old context.

## Current Pointer

- 当前：[P020 统一工作台与 BCA 桌面 MVP](work/tasks/P-020-unified-workbench.md)，工程验收完成（PR72），最终独审与必需CI通过；一次本地收尾后树释放，下一任务上游新窗口，详 snapshot。

- 最近完成：[P019 固定BCA单板CSV研究适配](work/tasks/P-019-bca-csv-adapter.md)。工程完成，PR71/main1c819ae、指定增量独审及必需CI通过；[最终交付](work/evidence/P-019/final-delivery.md)。本地收尾后释放共享树，由上游新窗口推进统一入口/交互。

- 最近完成：[P018 固定BCA方法与研究契约](work/tasks/P-018-bca-method-contract.md)。研究范围完成，PR70/main3947261、指定研究/增量独审及必需CI通过；[最终交付](work/evidence/P-018/final-delivery.md)。本地收尾后释放共享树，上游直接新窗口派发下一任务，科学与产品未验保留。

- 独审协议：[B021方案](docs/plans/independent-review.md)随PR69/main dc2609dd集成；按阶段审查，准确候选回传上游。

- 最近完成：[P017 BCA孔板研究](work/tasks/P-017-endpoint-assay-research.md)。研究/规划已完成，PR68/main f8f69b5、指定独审及双平台CI通过；[最终交付](work/evidence/P-017/final-delivery.md)。共享树收尾后释放，下一任务由上游新开窗口；前端阶段按[主方案第11节](docs/plans/research-platform-rd.md)。

- 最近完成：[P016 单图核分割研究用户流程](work/tasks/P-016-nuclei-single-image-flow.md)。PR67/main6bd4680、真实GUI/异常回归、准确独审及双平台CI通过，已正式回传上游自动接续；见snapshot及[最终交付](work/evidence/P-016/final-delivery.md)。

- 最近完成：[P015 StarDist研究适配器](work/tasks/P-015-nuclei-research-adapter.md)，PR66/main a761284，真实模型/独审/双平台CI及正式回传完成，见[P015交付](work/evidence/P-015/final-delivery.md)。上游已正式派发下一单图研究用户流程，先关闭P015后查重建卡/创建新goal；见snapshot，不猜编号、不扩科学准入。

- 最近完成：[P014 成熟荧光核计数方法直接调用](work/tasks/P-014-mature-nuclei-methods.md)，PR65合入main07838c2，实验/独审/双平台CI及回传完成；详见[P014交付](work/evidence/P-014/final-delivery.md)。下一任务由已收到验收回传的上游自动接续派发，不猜编号；科学缺项保留。

- 最近完成：[P013 第二实验比较与最小方法验证](work/tasks/P-013-second-experiment-discovery.md)，PR63研究/PR64正式准则及HTML已同步main cddf759，证据见[P013交付](work/evidence/P-013/final-delivery.md)。下一项由上游连续派发，优先成熟实现真实调用及训练数据重叠核验；未授予核计数科学准入。

- 最近完成：[P012 WB首次使用走查与试用准备](work/tasks/P-012-wb-first-use.md)，PR62集成，工程验收证据见final-delivery；科学/学生/目标机未验保留。用户要求由上游在回传后连续派发推进下一项。

- 最近完成：[P011 WB学生结果闭环](work/tasks/P-011-wb-student-results.md)，依据[P010调研](work/evidence/P-010/wb-discovery.md)完成工程范围并经PR60集成；科学/用户未验边界保留。5.0已合入，P002/M1/M2不重做。
- T082历史工程证据及科学/目标环境待办完整保留于其[任务](work/tasks/T-082-reliability-remediation.md)，不由V0自动关闭。
- 本轮本地工程交接：[T082 final-handoff](work/evidence/T-082/final-handoff.md)，区分冻结源码、隔离验收工件与后续交接HEAD；科学待办不由工程通过代替。
- 最近交付：[T081 R2](work/evidence/T-081/final-delivery.md)。当前源码/构建源码/主线集成/安装包区分见 [T082 baseline](work/evidence/T-082/baseline.md)。
- 旧 snapshot 保留于 `.agent-handoff/archive/T081-before-T082-snapshot.md`；原图、历史、既存 dirty 树及旧交付继续保护。
