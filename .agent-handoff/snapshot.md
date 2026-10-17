# Handoff Snapshot

- 更新2026-10-17；唯一任务状态 work/tasks/T-042-source-only-repair.md；总体T-003科学验收仍未完成。
- 活动树 C:/Users/70236/.codex/worktrees/t021-coordination/bioimage-tools-platform，codex/t042-source-only-repair，产品HEAD9eb5a1b；旧主目录dirty和.impeccable/questions不动。
- 已实现source_geometry@2（短膜/倾角/多证据Marker/N/独立原ROI），background_support@1（背景不足/内部双峰复核）；网页工作台启用新策略，web_ui HTML/CSS无改动。误开旧Qt测试窗口已关闭，验证入口改WebWorkbenchWindow。
- 8原图源输入识别、冻结后参考评分：旧1/8→新8/8，独审一致；回归集非留出。原图/12参考/旧成果SHA保持。frozen-final与独审frozen-v4 detection对象全等。部分裁图有残余曲率。
- 正常网页workbench-web-v3：8成功run、正常导出、保存重开相等、原图不变exit0；另重开DOM结果页48cells/48按钮/busyfalse通过。见.local/t042/workbench-results.png/json。
- 产品独审9eb5a1b增量完成，无未关闭确定缺陷；真实积分48槽7valid/41quality_review，其中21背景支持不足、33位深极值（交集），没有独立积分真值。
- 最终完整check --all：628项在tests/test_wb_desktop.py:480反复关闭窗测试挂起，faulthandler主线程停QTimer.timeout.connect，专属pytest33896已停止，check实际exit1。根因UNKNOWN，生命周期代码本任务未改；只读诊断不能证明GC死锁。隔离该模块10passed/29.39s/exit0；其余618测试分进程343.79s/exit0，合计628在两个进程通过，不等于完整check门禁。
- 独立wheel和smoke/policy exit0，类型0错误；58相关测试及114角度×N探针通过。626项前轮622passed/4failed已经9eb修复Schema漂移和N8/7°反例。
- 下一步调查原生挂起可复现顺序或原生线程栈，再完成全门禁；不得靠skip/改阈值或只看passed数量判成功。
- 未发布/PR/main/干净Windows。原生CUA不重启。源路径仅.local/t042/sources-only.json；参考仅scoring。所有失败轮次与私有成果保持。
