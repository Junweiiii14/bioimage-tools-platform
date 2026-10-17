# Handoff Snapshot

- 更新2026-10-17；任务唯一来源work/tasks/T-043-gate-repair-and-staged-sync.md，总体in_progress。最新CI009任务work/tasks/CI-009-atomic-workspace-initialization.md；科学/交互/发布验收未完。
- 活动树C:/Users/70236/.codex/worktrees/t021-coordination/bioimage-tools-platform，codex/t043-gate-and-staged-sync；每次核对HEAD/dirty。当前产品57fd7ea，正式669 check/497.77秒+全部隔离wheel实际exit0，日志.local/t043/check-ci009-final.log。原ResearchVault根dirty保持，不能作为当前产品。
- 日常入口为活动树Start-BioImage.ps1/桌面“BioImage WB 工作台（当前开发）”；默认和历史--figure-project/--platform统一绿色WebWorkbenchWindow，HTML/CSS未变。旧窗口显式legacy，测试强制离屏，关闭失败不回退旧host；父工作区旧WB路由已完整备份后仅改该段，独审核验。用户工作台46512保留，不强杀/重启，不恢复停止的CUA。
- CI006a811ccfd修四处worker退休→owner线程析构→queued终态。79f9070真实三线程native及受控正负对照支持Qt对象锁/GIL反转；后续其他超时不一概归因。本机完整668/508.54秒+全部隔离wheel实际0，独审18项0。QtCore实际6.12.0；WebEngine独立6.140.0/Chromium140，不混用源码。WebEngine未完整析构边界仅假设，暂无确定缺陷。
- 远端当前1bb1d9d：Linux668/183.03秒+全部wheel0，规则/桌面环境0；Windows1failed667passed/516.76秒、真实child exit1，metadata close测试setup等待5秒，create执行区间6.125秒后正常emit/deliver。CI007平台guard和CI008退出诊断已完成；bbf3cc5此前668passed后exit1仍UNKNOWN，无wheel，不追溯当同因。
- CI00957fd7ea新库初始化BEGIN在executescript脚本内部，版本/5表/身份一次提交；同步/格式v1/旧库读/fsync/测试时限不变，失败目录保留。旧红1项真实半初始化，新45项0，独审45项8.31秒0；20本机创建旧median56.76ms→27.38ms，非托管CI保证。完整669/497.77秒+全部隔离wheel实际exit0，真实child0；远端新候选待复验。
- 最新8原图工作台功能链.local/t043/workbench-ci009实际exit0：8run、保存重开/关闭成功、N8/8/4/4/8/8/4/4、8原像素ROI与48值/状态与CI006相同，原SHA保持、参考未读，仍7valid41review。离屏截图不作视觉验收。T042 source_geometry@2/background_support@1已正常UI接入，旧1/8→新8/8仅开发回归集，无独立积分/留出真值。
- 治理#7→产品阶段#3→#8/9/10/11/12/13/14全草稿；开发与stage8远端精确1bb1d9d，main221a2df未变，无一次合累计历史。当前SYNC008清单来源57fd7ea，前置4582976e，含CI002–009历史回执；最终整理提交后须精确规则/独审，再正常FF/备份/atomic推两个分支，更新.local/t043/stages-published-final.json与Issue6。
- 原19树外置refs/patch/untracked备份，34原有文件SHA保持；6干净无.local旧树仅锁定，未删/移。私有原图/旧结果原位，Git bundle不替代它们。最新.local/t043/backup-final.json只到1bb，57新成果结束后必须新unique bundle并再验34文件；原.impeccable/questions4文件不提交。
- 用户要求完成后通俗简洁维护汇报；docs/maintenance-plan.md已更新机制/现状/小测试→完整检查→独审→阶段PR，不能宣称历史独审/科学/包态验收全完。GitHub开发日志Issue6/comment6231511951保持真实失败与当前状态，最终回读核对正文。
