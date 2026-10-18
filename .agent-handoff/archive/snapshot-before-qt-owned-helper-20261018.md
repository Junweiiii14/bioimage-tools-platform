# Handoff Snapshot

- 更新2026-10-18。任务work/tasks/T-044-wb-workflow-and-integrals.md，review；本地实现/独审和PR15同步完成，CI012精确fixture修正已审查并推送，最终远端734门禁待实际结果。
- 活动检出C:/Users/70236/.codex/worktrees/t021-coordination/bioimage-tools-platform，codex/t044-wb-workflow-and-integrals，基线d11552c，最新产品a72e7102891df287e3484f20f3724612779b53f5。核对实际HEAD/dirty，不为旧指针切历史代码。
- 当前入口Start-BioImage.ps1/桌面当前开发绿色WebWorkbenchWindow，-I核验模块和资源路径；旧ResearchVault树不作当前入口。用户PID33256不动，停止的CUA不恢复。
- 21工作树59分支、6干净历史树原位锁定，原dirty/原图/旧结果保留。.impeccable/questions四文件未提交并外置核SHA，见.local/t044/untracked-backup.json。

## 已完成

- 首页及已有项目folder_sources@1/可见报告/明确补入，同Fig字面分组/β字体；目标锚定5–25%背景；独立灰度ROI/N/极性/多泳道曲线与人工边界；绑定当前行审核回存PNG/原值TIFF/最后JSON；质量原因集中；123产品Python文件审查与最小去重，兼容schema1–8/API保留。
- 733 passed in 525.53s、pytest child0/全部隔离wheel/dev0，.local/t044/check-final-core-boundary.*。先前8e4de82核心wheel缺PIL失败保留；a72e710延迟可选依赖独审11项3.31秒0，隔离API/目录发现0，无阻断。
- 最终正常Web8源/8worker/4Fig/8回存/保存重开关闭实际0，.local/t044/final-workbench-20261018T062442Z/validation.json；产物独审exit0，源SHA和回存像素/映射、成图与已评分前轮相等。参考像素未读、无结果注入。N8,8,4,4,8,8,4,4；裁图回归1/8→8/8仅开发集。积分13有效35复核（背景不足21→2，零值风险33保持），不是积分准确率。
- 31旧文件作者前后SHA一致，前态仅RAM，独审不可复算；current-ledger只作未来基线。各阶段绑定独审见任务/final-delivery.md。
- detector已恰好一次、视觉初6/确认8截图完成，勿再运行；离屏resize部分视口陈旧/DOM空不算全DPI，设计sidecar/PRODUCT待更新。

## 同步与下一步

- 已safe push并创建/attach草稿PR #15：https://github.com/Junweiiii14/bioimage-tools-platform/pull/15，base stage-08=d11552c；main仍221a2df，原9草稿链保留。工作树不删除/移动，当前4未提交文件不入Git。
- 407083e全引用外置bundle verified，SHA1a40a4da10723b86026348741892296fbe4baf14ac0b125379b8341758b1cf2a，原34未提交文件再次核SHA一致。最后文档提交也将新建bundle；最新索引.local/t043/backup-final.json，当前4文件备份.local/t044/untracked-backup.json。Git不含忽略原图/旧结果。
- 仅文档后继，不改产品。收尾完成后按PR最终HEAD看Windows/Linux/rules/desktop远端CI；本快照提交时运行中，不声称通过。如失败按日志修复，不弱化门禁；无新失败不重跑本地全检。
- issue6开发日志记录本轮结果/PR/备份/CI真实状态；最后给用户简单专业维护汇报（docs/maintenance-plan.md）。任务review指待按依赖阶段集成main，不是正式产品发布。历史原生UNKNOWN、科学真值/留出、恢复和最终Windows/DPI/包仍待后续。

## CI012 当前优先项

3e5cee3/run39104680503 Linux约29% OCR用例SIGSEGV，debugger255，wheel未跑；GDB非主线程587 QWidget析构，具体对象/历史全部根因仍UNKNOWN。test_wb_desktop fixture只有close/wait未destroy。受控真实窗口+holder环，后台GC未dispose进程Aborted/3，先GUI销毁0；只修本fixture拥有窗口的close/wait之后deleteLater/waitinvalid，无全局GC或Qt清理。新断言旧红1/2.87秒，新11项25.58秒0、类型/Ruff/格式0。见ci012-fixture-lifetime.md，需提交绑定独审、safe备份/push、远端734完整验证；产品a72代码不变，无理由重复8图/截图。issue6日志已明确更新失败，不当通过。Windows旧run仍待实际状态。

## CI012审查后最新指针

ab6a68e only tests/docs，无产品差异；独审1项1.96秒0关闭P2，原11项独审24.94秒0。原run39104680503 Windows733passed575.75秒和全部wheel/dev成功，Linux29% SIGSEGV使整run失败；均已保存日志。不取消真实失败。ab已外置bundle verified/SHA0842f55b468becb38ed9345d45b3b840e006a688202ee83f581eb5d852217e1f，再核34原未提交一致，safe push。此文档后继也会重新备份和push，不再改产品/测试；最终HEAD/CI run/开发日志链接见.local/t044/github-delivery.json及PR15/issue6。下一步只看最终PR的rules、Windows/Linux734和desktop实际结果；失败按证据继续，成功后给维护汇报，任务review表示待依赖集成main，不要求合main。不要因旧快照pending重复实现/验证。

## CI012同类fixture最新后继

等待925的734远端期间发现/只读确认三共享fixture同类遗漏：test_figure_desktop、test_project_measurements、test_automatic_workflow各自拥有窗口在原关闭等待后精确deleteLater/waitinvalid，28项85.63秒0；WB/Figure两类主线程销毁+workerGC回归2项1.77秒0，类型/Ruff/格式0。产品a72不变，不扩所有Web测试；总数735。当前待提交绑定独审/最后外置备份/push，再看最终HEAD735全检；925/ab的734运行若被新push取消须如实记录非通过。不要反复文档提交重启成功CI；最终实际状态记录issue6和.local/t044/github-delivery.json。
