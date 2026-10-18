# Handoff Snapshot

- 更新2026-10-18；当前任务唯一来源work/tasks/T-044-wb-workflow-and-integrals.md，in_progress。用户新增积分/目录识别/同Fig/审核后回存/独立灰度与峰交互/界面精简/全库冗余审查，完整范围见任务。T043历史间歇退出仍UNKNOWN；不宣告整项目完成。
- 活动树C:/Users/70236/.codex/worktrees/t021-coordination/bioimage-tools-platform，codex/t044-wb-workflow-and-integrals，基线d11552c（其远端run39030621380两平台670及全部wheel/最终check、规则、桌面成功，独审已核验）。产品57fd7ea，本机669/497.77秒+全部wheel/最终check0；becb389远端run39025981922已全部成功：Windows669/407.87秒child0、Linux669/178.49秒，两平台全部wheel/最终check成功，规则/桌面环境成功。0d269db纯文档后继Linux669/146.29秒后SIGSEGV、exit245/wheel未跑，Windows669/346.68秒/child0及全部wheel0；前次成功不覆盖新失败。使用前核对实际HEAD/dirty。
- 日常从活动树Start-BioImage.ps1或桌面“BioImage WB 工作台（当前开发）”启动；默认/历史常用参数统一现有绿色工作台，HTML/CSS未变，旧原生工具仅显式legacy。父工作区WB路由已备份后修正，快捷方式/实际文件由独审复核；测试强制离屏，关闭失败不回退旧host。用户工作台46512未强制关闭，不恢复停止的CUA。
- CI006修四worker退休→owner线程实际析构→queued终态；79f9070真实native/Python栈及受控正负对照支持Qt对象锁/GIL反转。CI009新DB版本/5表/身份单事务，真实故障回滚旧红新绿/45独审0，不改schema/v1/同步/fsync/测试时限。源码QtCore6.12.0与WebEngine6.140.0不可混用。
- 历史bbf668passed后外层exit1仍UNKNOWN；1bb的create执行6.125秒后正常回执是另一实际失败。当前通过不能将所有旧失败一概归因；WebEngine资源析构边界仅假设，未据此乱改。详情见risks及CI005–009证据。
- 最新8图正常工作台功能链.local/t043/workbench-ci009实际0：8run/保存重开/关闭，原图SHA保持、参考未读，8原像素ROI/N和48值/状态与CI006保持，N8/8/4/4/8/8/4/4、7valid41review。T042旧1/8→新8/8是开发回归集，无独立积分真值/留出验收；离屏截图不当作视觉通过。
- 治理#7→产品#3→#8/9/10/11/12/13/14均草稿，main221a2df未变，不一次集成累计128历史。SYNC008精确base4582976e，清单来源aabd39e，保留CI002–011祖先回执。后续集成先按真实base重载规则/清单再跑检查。
- 原ResearchVault根及各历史dirty树保留；34原未提交文件SHA反复核验，原.impeccable/questions4文件不提交。19树外置patch/untracked/refs备份；6干净无.local旧树仅原位锁定，未删/移。最新bundle位置/SHA在.local/t043/backup-final.json，原图/旧结果原位保留，Git不能代替原资料备份。
- 已授权只读独审复核becb远端两HEAD/PR/main、入口/父路由、备份/34SHA及发布日志正文，无阻断；收尾文档仍须独审/精确规则后正常FF、unique备份、atomic推开发及stage8并回读Issue6/PR14。不强推/不合main。
- 用户最终要求简单专业维护汇报。docs/maintenance-plan.md已说明固定入口、模块/API边界、依赖锁、小回归→完整检查→独审→小PR、备份/任务/交接及4项报bug材料；每周检查是人工建议，没有后台定时任务。发布/科学/恢复演练/历史独审缺口继续真实保留。

- CI010现行40f Linux云端GDB15.1真实控制成功、669/158.32秒及全wheel/dev0；WSL同锁定环境669/398.40秒pytest0（非full dev check）。同HEAD Windows669/433.12秒后Aborted/AV，原child3221225477/c0000005、wheel未跑。不能凭一次Linux成功关闭间歇故障。
- CI011诊断提交aabd39e：标准Windows API仅观察自有单个解释器，保留原退出码；五真实控制作者/独审均0，相关9项作者2.64秒/独审2.56秒0，修改模块双平台类型0。绑定独审无阻断；PC0故障线程无帧，其他线程有栈，罕见OS API组合仅静审。正式670/517.68秒及全wheel/dev本机实际0，云端后继待验证，产品仍57fd7ea；不是产品崩溃修复，不混淆故意控制fault与产品fault。

- T044首阶段已实施目录头信息筛选、明确Fig/采集前缀标签、Unicode字体后台导入。真实目录选8/排除24，4 Fig，正常WebWorkbenchWindow/8真实worker/保存重开/关闭0，原SHA与48积分值状态原因全保持。20定向8.82秒0/相关类型0；完整门禁与提交绑定独审待执行。积分诊断20零值/8背景不足/13重叠，盲扩25%/50%不可靠，独审反例证明全区argmax可抢走目标。下一步先提交独审现阶段、定义显式目标锚定上下文策略与回归，再实现回存/独立灰度/精简UI/全库审查。不得将41项直接判有效，参考像素不参与识别。

- 5b9b752阶段独审P2（编号变体被静默排除）已补可见清单/改选和落盘，待后继绑定复核。5b9b752首轮完整check实际1，3项新增测试list类型错误，pytest/wheel未跑；已修，后继全项目Pyright0、18相关19.97秒0，完整门禁待后继执行。不要当作全量通过。

- 当前20586fe已完整678/489.79秒、child0、全部wheel/check0。随后独审项目归属P2已补workspace+project_id绑定，A→B/跨workspace与当前SHA负例19项27.95秒0/全项目类型0，后继提交独审/最终全检待做。父AGENTS仅WB行硬编码分支已备份去除，回执.local/t044/parent-route-receipt.json。数值原型.local/t044/probe_anchored_context.py与anchored_analytic.py：19/21支持、4解析对照0，尚未接产品；下一步定义target_roi/上下文版本及原坐标/手动编辑全链，不把未完成的回存/独立灰度/UI精简/全库审查遗忘。

- T044锚定上下文已实现并设为当前Web默认（待绑定独审/最终全检）；新target/context原坐标与比例、旧wire字节/历史兼容、手改失效重算已测。112相关20.79秒0、旧网页9项27.89秒0、新快照1项1.98秒0、入口12项4.17秒0、全项目类型/Ruff/格式/Node0；初轮3失败及schema扩展说明在T044验证。8真实目录/正常Web/8worker/新导出/重开/关闭实际0，CSV48槽13valid35review，背景不足21→2，33零值风险保持；不是积分准确率。e6d1abd独审2项2.33秒0关闭归属P2并核父路由。下一步绑定审查本阶段、审核后回存/独立灰度全泳道交互/UI精简/全库审查/最终视觉全检与安全同步，完整目标仍进行中；原生间歇退出UNKNOWN。用户最终报告需简单专业讲维护机制/快速修bug，非提前结项。

- 最新3a830fb完整check失败：696passed/488.23秒后原生AV，原child3221225477/c0000005，dev/外层-1，wheel未跑；.local/t044/check-anchored.{log,json}。实际native栈1线程，Qt/包装器/父子析构路径，最近符号不当精确源码根因，见T044/native-exit.md。独审18项11.36秒0发现P2目标不变清人工参数，后继已修target比较及桥接no-op，38相关29.70秒0+新API/公开桥接2项2.00秒0/相关类型0，待提交绑定复核。下步先最小四组Qt退出控制定位，勿重复盲跑/猜清理/抹失败；再继续回存/独立灰度/峰交互/UI精简/全库审查/最终门禁安全同步和简单维护报告。
