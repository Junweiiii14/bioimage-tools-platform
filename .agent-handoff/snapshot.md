# Handoff Snapshot

- 更新2026-10-17；状态唯一来源work/tasks/T-043-gate-repair-and-staged-sync.md，本轮in_progress，CI010定位Linux测试后SIGSEGV。CI009原子初始化complete；T003整体产品/科学/交互/发布验收仍待办，不自动扩展路线图。
- 活动树C:/Users/70236/.codex/worktrees/t021-coordination/bioimage-tools-platform，codex/t043-gate-and-staged-sync。产品57fd7ea，本机669/497.77秒+全部wheel/最终check0；becb389远端run39025981922已全部成功：Windows669/407.87秒child0、Linux669/178.49秒，两平台全部wheel/最终check成功，规则/桌面环境成功。0d269db纯文档后继Linux669/146.29秒后SIGSEGV、exit245/wheel未跑，Windows669/346.68秒/child0及全部wheel0；前次成功不覆盖新失败。使用前核对实际HEAD/dirty。
- 日常从活动树Start-BioImage.ps1或桌面“BioImage WB 工作台（当前开发）”启动；默认/历史常用参数统一现有绿色工作台，HTML/CSS未变，旧原生工具仅显式legacy。父工作区WB路由已备份后修正，快捷方式/实际文件由独审复核；测试强制离屏，关闭失败不回退旧host。用户工作台46512未强制关闭，不恢复停止的CUA。
- CI006修四worker退休→owner线程实际析构→queued终态；79f9070真实native/Python栈及受控正负对照支持Qt对象锁/GIL反转。CI009新DB版本/5表/身份单事务，真实故障回滚旧红新绿/45独审0，不改schema/v1/同步/fsync/测试时限。源码QtCore6.12.0与WebEngine6.140.0不可混用。
- 历史bbf668passed后外层exit1仍UNKNOWN；1bb的create执行6.125秒后正常回执是另一实际失败。当前通过不能将所有旧失败一概归因；WebEngine资源析构边界仅假设，未据此乱改。详情见risks及CI005–009证据。
- 最新8图正常工作台功能链.local/t043/workbench-ci009实际0：8run/保存重开/关闭，原图SHA保持、参考未读，8原像素ROI/N和48值/状态与CI006保持，N8/8/4/4/8/8/4/4、7valid41review。T042旧1/8→新8/8是开发回归集，无独立积分真值/留出验收；离屏截图不当作视觉通过。
- 治理#7→产品#3→#8/9/10/11/12/13/14均草稿，main221a2df未变，不一次集成累计128历史。SYNC008精确base4582976e，清单来源57fd7ea，保留CI002–009祖先回执。后续集成先按真实base重载规则/清单再跑检查。
- 原ResearchVault根及各历史dirty树保留；34原未提交文件SHA反复核验，原.impeccable/questions4文件不提交。19树外置patch/untracked/refs备份；6干净无.local旧树仅原位锁定，未删/移。最新bundle位置/SHA在.local/t043/backup-final.json，原图/旧结果原位保留，Git不能代替原资料备份。
- 已授权只读独审复核becb远端两HEAD/PR/main、入口/父路由、备份/34SHA及发布日志正文，无阻断；收尾文档仍须独审/精确规则后正常FF、unique备份、atomic推开发及stage8并回读Issue6/PR14。不强推/不合main。
- 用户最终要求简单专业维护汇报。docs/maintenance-plan.md已说明固定入口、模块/API边界、依赖锁、小回归→完整检查→独审→小PR、备份/任务/交接及4项报bug材料；每周检查是人工建议，没有后台定时任务。发布/科学/恢复演练/历史独审缺口继续真实保留。

- 最新任务work/tasks/CI-010-linux-post-test-crash.md；只增加Linux GDB观察与真实0/17/SIGSEGV预检，不改产品/断言/15分钟；本机8相关2.49秒0/双平台模块类型0，Linux控制尚未实际执行。先绑定独审、刷新精确阶段清单、备份普通推送；不得只为绿灯盲重跑或先改Qt清理。
