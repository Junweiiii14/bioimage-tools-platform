# Handoff Snapshot

- 更新2026-10-17；任务唯一来源work/tasks/T-043-gate-repair-and-staged-sync.md，总体in_progress；科学/交互/发布验收未完。
- 当前活动树C:/Users/70236/.codex/worktrees/t021-coordination/bioimage-tools-platform，codex/t043-gate-and-staged-sync；每次核对HEAD，不使用历史快照SHA启动。原ResearchVault主目录dirty，原有内容不变，不能用作当前产品。
- 桌面“BioImage WB 工作台（当前开发）”固定活动树Start-BioImage.ps1；无参及历史--figure-project/--platform统一绿色WebWorkbenchWindow。旧窗口仅显式legacy，兼容测试离屏；高级编辑器仅显式工具动作打开。HTML/CSS未变；不重启用户现有工作台，不恢复用户停止的CUA。
- 已确认旧界面三路径：真实默认/历史CLI旧窗口、失败关闭host.show、可见兼容测试；2e5021d修复并独审。CI003b4bc8ba又修确定隐藏宿主Qt所有权，审查者3项exit0；不是原挂起根因证明。
- 最近完整产品b4bc8ba：check --all实际exit0，658passed/497.50s及全部隔离wheel/真实OCR。此前642/657两轮完整成功与失败记录均保留，见T043验证。
- CI00468c3265补存储enqueue/execute/end/reply/deliver的DEBUG单调时间/请求/线程日志，不含载荷；独审2项实际exit0。最终659完整check实际exit0、509.86秒及全部隔离wheel/真实OCR通过，日志.local/t043/check-ci004-final.log；无时限/skip/锁/公式变更。
- 远端阶段7 Windows首次初始化5秒超时，原SHA重跑成功；阶段8bcf Windows15分钟无节点取消，5de诊断后Windows首个create10秒超时，1failed/656passed；finally shutdown完成。根因UNKNOWN，无永久死锁证明；日志.local/t043/pr14-windows-diagnostic-failed.log。诊断通过也不能声称根因修复。
- 同步分支为codex/t043-gate-and-staged-sync与codex/stage-08-source-repair，精确HEAD现场核对；CI003/004已完成本地完整门禁与绑定独审，SYNC008清单以68c3265为来源快照。治理PR7及产品阶段1–7当前CI成功，阶段8实时CI以PR14/Issue6为准；全草稿、main221a2df不变。
- 阶段链PR7→3→8/9/10/11/12/13/14；.local/t043/stages-published-final.json结束时更新。前置合main后需真实重载base及CI，禁止一次合累计历史。旧T007/T026回执Git版本保留。
- T042 source_geometry@2/background_support@1已接现有工作台；8原图独立推理，参考仅评分，旧1/8→新8/8（开发回归集）。48槽7有效/41复核，没有独立积分真值。8原图/12参考/旧预测保持；最新8图功能链.local/t043/workbench-ci003退出0，离屏截图空白不作视觉验收。
- 原19树外置allrefs/二进制patch/未跟踪tar保留；34原有未提交文件SHA保持；6干净无.local树原位锁定，未删/移目录。私有原图/旧结果仍原路径，不能以Git bundle替代而删除。最新备份指针.local/t043/backup-final.json需在最终refs后更新。
- GitHub开发日志Issue6/comment6231511951持续记录实际检查/阶段HEAD，保留全部失败与UNKNOWN。后续继续原生稳定性证据、阶段审查/实际base刷新及独立科学验收，不能扩展新工具。
