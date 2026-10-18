# Handoff Snapshot

- 更新2026-10-18。唯一任务work/tasks/T-044-wb-workflow-and-integrals.md，review；产品本地验证/独审/真实8图完成且PR15已草稿同步，当前仅CI012测试管理收尾和最终736远端门禁，再给用户简单专业维护汇报。不要扩展产品路线图。
- 活动检出C:/Users/70236/.codex/worktrees/t021-coordination/bioimage-tools-platform，codex/t044-wb-workflow-and-integrals，base d11552c；核对实际HEAD/dirty。正常入口Start-BioImage.ps1/桌面当前开发，-I验证实际模块与绿色Web界面目录。旧ResearchVault检出保持，不切旧树；用户PID33256不动，停止的CUA不恢复。
- 21工作树59分支、6历史干净树原位锁定。原19树备份与34原未提交SHA反复核验保持；当前4个.impeccable/questions仍未提交且另存外置逐文件SHA，.local/t044/untracked-backup.json。原图/旧结果/诊断输出全部保留，Git不含忽略原资料，不强推/不合main。

## 产品已验证，之后仅测试/文档

- 产品a72e710：目录首页/已有项目folder_sources@1与报告/明确补入、字面Fig/β字体；目标锚定5–25%背景；独立灰度ROI/N/极性/多泳道曲线/人工边界；当前行审核回存PNG+原值TIFF+最后JSON；质量原因集中；123产品Python调用链审查及最小去重；schema1–8/兼容接口保持。
- 本机完整733passed525.53秒、pytest child0/全部独立wheel/dev0，.local/t044/check-final-core-boundary.*。核心wheel缺PIL失败已修延迟显示依赖，安装检查加严，独审11项3.31秒0。各阶段绑定独审见任务/证据。
- 最终真实Web8源/8worker/4Fig/8回存/保存重开关闭实际0，.local/t044/final-workbench-20261018T062442Z/validation.json；独审输出像素/位深/来源/SHA和已评分成图逐源几何一致，未读参考像素/未注入结果。裁图历史1/8→8/8仅开发回归，N8,8,4,4,8,8,4,4。48槽13有效35复核、背景不足21→2、零值风险33保持；无积分真值，不叫积分准确率。
- 31旧结果作者RAM前后SHA一致，前态不持久化，独审不能复算历史；current-ledger只作后续基线。detector恰好一次/初6确认8实际Qt截图完成，不再生成。部分离屏视口陈旧/DOM空不作全DPI证明，设计sidecar/PRODUCT待后续刷新。

## CI012关键实际证据

- 3e5cee3/run39104680503：Linux约29% OCR中SIGSEGV/debugger255、wheel未跑，非GUI线程587 QWidget析构同时主线程事件；Windows完整733passed575.75秒/child+所有wheel/dev0。不是全部通过后的退出。
- 925/run39105503647：Linux28%再次SIGSEGV/线程574 QWidget析构，主线程selection reset；Windows因新提交取消。不可将Linux失败当仅取消。
- 受控真实窗口+holder引用环，后台GC旧未dispose进程Aborted3，先GUI销毁0；人为环不是精确原fixture，不能认定崩溃对象或全部历史因果。Qt/CPython来源及日志见ci012-fixture-lifetime.md。
- WB fixture补close/wait后deleteLater/waitinvalid；5c独审11项24.94秒0发现测试finally提前删P2，ab6a68e安全helper复用独审1项1.96秒0关闭。三项目共享fixture同类补正c5b5566独审5项9.96秒0；作者28项85.63秒0/两类销毁线程2项1.77秒0。
- c5/run39105787605 Linux完整735passed133.44秒/debugger0/所有wheel/dev0；Windows本记录时仍执行。后继一次清点的Web/平台/共享fixture统一到tooling/qt_test_lifecycle.py，只处理显式自有owner，保持原资源退休判据/等待阈值/关闭后业务断言，不禁GC/不全局删除/不改产品。
- 本批作者12模块67项157.28秒实际0，含真实等待失败不调deleteLater、新WB/Figure两类GUI析构；全项目Pyright/Ruff/格式525文件0。总数736；当前需绑定提交独审和最终远端验证，不用旧成功替代。

## 收尾顺序

1. 本批提交绑定只读独审（用户已授权/root/readonly_review），通过后运行.local/t043/backup_final_refs.py做unique allrefs/verify/SHA并核原34文件，safe push PR15。不要再无新原因改产品/生成真实结果/截图/完整本地复跑。
2. PR15 https://github.com/Junweiiii14/bioimage-tools-platform/pull/15，base stage-08=d11552c，原9草稿链保留，main最近221a2df。最终HEAD/run/备份摘要看.local/t044/github-delivery.json和issue6开发日志评论6246640297。只检查最终HEAD的rules、Windows/Linux736、desktop实际结果；失败按新证据继续，不能改成功/弱门禁。
3. 最终实际CI和独审、备份摘要写GitHub日志/PR及ignored receipt，不为只补CI成功文字再次提交触发12分钟全检循环。任务review表示待依赖阶段集成main，用户没有要求一次合128提交。最终简洁专业维护汇报链接docs/maintenance-plan.md/PR/日志。
4. 保留历史native UNKNOWN、独立科学真值/留出、恢复演练、干净Windows/DPI/最终包待后续；本轮功能与维护流程交付不等于正式发布。无需再次索要已授权审查/同步许可。
