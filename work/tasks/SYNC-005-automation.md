# SYNC-005：阶段 5/8 — 实验室版式、模板与自动处理平台

- 状态：done；最终e478a8d绑定非作者独审无P0–P2，四服务器检查SUCCESS后PR11合main5f20960731132b68e2b010c1e0141e2761242420（2026-10-19T22:29:03Z）。历史c849超时根因UNKNOWN仍保留。
- 原始产品快照：93792bc7205333f945b612ced3937a7e49db19bf；前置分支codex/stage-04-recovery，精确基线948d7684e777edcf02ceb4652a959fc73e2604eb。
- 当前产品2e5021d已独审，完整门禁642项通过；该结论不替代本历史阶段CI或独立产品审查。
- 额外差异仅规则校验前置变更、阶段任务/显式回执清单及真实历史回执重载（本阶段['T-026']）；产品快照另行逐文件验证。
- 当前回执覆盖整个PR，历史记录由显式清单逐字节及祖先关系校验；不删除旧记录、不豁免规则。
- PR保持草稿，按前置依赖审查；前置合main后需重新加载实际基线并重跑CI，不一次合入累计历史。
- 原图/参考/旧结果和未提交文件均保留本机，不上传；原生Windows间歇挂起原因UNKNOWN，离屏通过不等于交互验收。

## E7 preparation

已按原ef17基线scope .加载并读取规则/模块地图/自动流程契约。非作者旧8be1增量预审未发现新P0–P2，检查原值定量、机器建议非人工审核、失败非零、新目录和取消/代际保护；不替代实际main最终head复审和服务器门禁。将合前置冻结6963再等实际main接受后重载。主树当前Qt全量中，本树不并发Qt或重型Git测试。

## 实际main

已合实际main aac126e，scope .按真实基线重载并读取任务/BASE模块地图，当前唯一manifest保留T021–027及旧F006/F007等源记录。本地准备静态Ruff/format353/Pyright0，不并发Qt全量；最终冻结提交独审与新四服务器全量/隔离wheel通过后才merge，不把原产品532记录当新CI。

## Windows timeout and worker retirement repair

Final c849cda Windows quality39331582949/job118330834329 reached the unchanged 15 minute limit. Last test body passed test_multi_source_compute_reopen_edit_and_recompute; Python dump showed fixture windows waiting and storage workspace.close active. No native stack establishes cause: historical timeout remains UNKNOWN. Linux, desktop and rules passed; Windows cancellation is not success.

Ported the independently reviewed a811ccfd retirement repair exactly for four workers and its original four tests. Before source change: 4 failed/2.21s, actual exit1, destruction occurred on worker threads. After: worker retirement plus async storage/process/project measurements 33 passed/52.57s, actual exit0, explicit offscreen, serial with other Qt. This closes concrete ownership evidence, not the historical timeout root. Ruff check0, format357 files0, Pyright0. No deadline, expected value, skip, lockfile or numeric/schema change. Final bound review and fresh four server checks required before acceptance. Raw logs remain ignored .local/sync005-retirement-{before,after}.txt and sync005-windows-timeout.txt.

