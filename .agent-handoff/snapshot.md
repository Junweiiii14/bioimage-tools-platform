# Handoff Snapshot

- 更新2026-10-18。唯一任务状态：work/tasks/T-044-wb-workflow-and-integrals.md，in_progress。用户完整目标尚未完成；结束后须给程序小白简洁专业的维护/快速修bug汇报，见docs/maintenance-plan.md。
- 活动检出：C:/Users/70236/.codex/worktrees/t021-coordination/bioimage-tools-platform，codex/t044-wb-workflow-and-integrals，基线d11552c。每次核对实际HEAD/dirty，不为旧分支指针切回历史代码。正常入口Start-BioImage.ps1/桌面“BioImage WB 工作台（当前开发）”，默认WebWorkbenchWindow；旧原生host只显式兼容。
- 原ResearchVault检出和历史dirty/旧结果保留，不启动作当前产品、不覆盖、不kill用户工作台；用户停止的CUA不恢复。.impeccable/questions四个原文件未提交。

## 当前成果与证据

- T044目录头信息筛选folder_sources@1、明确Fig/蛋白字面解析、Unicode系统字体后台入资产已接现工作台。实际目录选8/排除24，4 Fig；有可见筛选记录和明确补入，状态落盘。e6d1abd将报告绑定workspace+project，独审2项2.33秒0关闭跨项目P2；父AGENTS原字节备份/1行去掉t043硬编码分支独审通过，快捷方式路径不变。
- 锚定积分策略anchored_context@1/anchored_background@1/quality@1已实施并为Web默认。target_roi是目标，roi是采样区，逐步5–25%首个完整支持、无邻峰夺目标。原像素/公式/零值风险保持，三schema可选显式策略扩展；旧wire字节保持/旧请求不升级。手动几何清旧上下文/边界后从目标重算，基线修改保留锚点。
- 3a830fb产品阶段作者112相关20.79秒0；网页9项27.89秒0、新快照1项1.98秒0、入口12项4.17秒0，全项目类型/static0。8原图正常Web目录导入/8worker/新导出/保存重开/关闭0，.local/t044/workbench-anchored/validation.json。CSV48槽13valid35review，背景不足21→2，33零值风险保持；不是积分准确率，原SHA/N8,8,4,4,8,8,4,4和4Fig保持，参考像素未读。
- .local/t044/anchored-preservation.json：19槽扩展，29未扩展槽原面积/bounds/flags全保持；前后正常成图PNG像素完全相同。T042旧1/8→新8/8仅指定开发集裁图评分，没有独立积分真值/未知仪器留出验收。
- 3a独审18项11.36秒0发现不变目标误清人工参数P2，9f96f5c已修；作者38相关29.70秒0+最终API/公开桥接2项2.00秒0，独审2项1.64秒0关闭。无变动保留原项目/代际、不重算；同目标伴基线编辑也保留上下文。

## 最新完整门禁：诊断测试隔离失败；原生退出根因仍UNKNOWN

- 3a830fb正式check --all：696passed/488.23秒后原生AV，原child3221225477/c0000005，dev/外层-1，wheel未跑；.local/t044/check-anchored.{log,json}。不能拿passed汇总或20586fe完整678/489.79秒+wheels0替代新失败。
- 实际native栈仅1线程：Qt窗口/父子/QFormLayout/包装器退出析构，最近SignalManager.retrieveMetaObject符号不当精确源码定位；不是已证实旧跨线程GIL死锁或WebEngine profile问题。详细证据/主来源/计划：work/evidence/T-044/native-exit.md。
- 四个最小Qt-only自有进程（普通/子类×自然/先销毁父对象）observer均附着、实际0、未复现；无产品/WebEngine/worker。receipt .local/t044/qt-exit-controls/receipt.json；不是根因修复。
- 694279f新增显式-p tooling.qt_exit_inventory观察插件：弱引用首次来源，最终有界对象类型/父子ID；不读文本/标题/图像，不发事件/GC/删除/关闭，不改退出。独审2项0.38秒0。Qt先返回完整列表，所以仅输出/遍历预算，不是瞬时内存上限；临时包装器引用可能影响析构时序。
- efec471诊断容错绑定独审3项0.39秒0。该提交完整check带清单/native observer真实700passed/1failed、488.11秒，child/外层1，wheel未跑，没有复现AV。失败trace为测试在全局4208根的128根截断清单中要求新root/child必出现；不是已定位的产品崩溃。最终5448根包含Qt弹出部件，不等于5448个产品窗口或泄漏证明。
- 后继仅隔离诊断单测根/来源表，保持原断言，补多根节点/129根/来源容量unattributed对照；5项0.46秒实际0、相关类型/Ruff/格式0，待提交绑定复核和最终完整check。没有清理前序产品对象/提高预算/改插件运行或成功状态。日志/回执.local/t044/check-exit-inventory.{log,json}，session14805已结束，源码不再冻结。
- 只读生命周期审计：resources_closed只证worker排空、不代表QWidget已析构；现有控件lambda/字段字典可能保留包装器，QFormLayout父属本身正常，尚无因果。下一独立控制可构造实际FigureProjectView（无后端/WebEngine），对照自然退出和显式父析构；不能为掩盖产品问题改全套测试清理。
- 积分新线索：源5剩余lane2/4在30%首支持，lane2在35%又不足/40%峰在目标外。独立解析三角峰真值36750在35%首次valid且准确36750（.local/t044/analytic-context-oracle.json）；无参考像素/结果注入。候选@2试5..50须保留@1≤25重放；先冻结弱/强邻峰、肩峰、非线性背景、截断和非单调候选反例。只读审查提醒扩大上限不足以证明背景真值；v2尚未实施。

## 下一步完整范围

1. 提交绑定复核诊断单测隔离，按实际View最小控制继续退出定位；新积分线索先建立独立反例再实现版本化候选策略，不简单调参宣布最后两槽修复。最终提交完整检查保留真实原生退出，不能改成功状态绕过。
2. 审核后裁图回存原文件夹：可信本机来源登记/源SHA重核、后台无覆盖新文件、显示裁图与原值区分、写后核验/保存/代际取消保护。尚未实现。
3. 独立灰度入口/自由目标ROI+N，不需先裁图或拼图；复用原像素worker/持久化，旧WBQuant仅参考全部泳道纵向峰、单lane精调、封底/填充面积交互。尚未实现。
4. 去除重复“需要审查”视觉噪声但集中保留真实质量原因；仍有NSUN6源5泳道2/4背景不足，不强判35项有效。之后全库冗余审查，按真实调用链保留兼容API/旧格式，更新过时文档；尚未完成。
5. 最终真实8图/完整检查/绑定独审/有界视觉验收后，外置备份复核原34文件，再安全GitHub草稿PR/开发日志同步，main不合128提交；最终用简单语言报告维护机制与限制。

## GitHub与保留约束

- T044全部仍本地，未新建/推送T044 PR。此前9草稿PR #7/#3/#8–14，远端t043/stage8 d11552c；main最近核验221a2df，不强推/不合main。发布前重新读远端实际状态。
- 原19工作树patch/untracked/refs外置备份、6干净旧树原位锁定、34原未提交文件SHA历史核验保持，原路径/旧结果不移动删除。最新allrefs备份指针.local/t043/backup-final.json；T044最终同步前需再做unique bundle并重核34SHA。Git不包含私有原图或忽略旧结果，不能替代资料备份。
- Issue6现有开发日志评论6231511951最后是T043；T044尚未发布。后续更新真实已验证事实，不公开私有图/绝对路径。
- 历史CI006真实Qt锁/GIL反转已修、CI009新库事务已修；其他间歇退出/包态干净Windows/恢复演练/科学留出仍保留，详见T043任务/risks。
- Impeccable已读取/上下文执行一次；全部网页修改后再运行机械detector一次和有界视觉循环。PRODUCT/设计sidecar过时已发现，不自动扩展刷新；最终说明一次。当前离屏GPU告警截图不作视觉验收。Qt官方支持--disable-gpu用于诊断，可只在自有视觉试验验证，不改用户环境/依赖。
- 自有子进程已验证PYTHONPATH可抢同名包，-I定位活动安装检出；尚未改启动器，不认定用户此前旧版同因。可在后续入口加固中使用，勿为匹配历史路径切旧树。
