# Handoff Snapshot

- 更新2026-10-17；唯一任务状态 work/tasks/T-042-source-only-repair.md；总体T-003科学验收仍未完成。
- 活动树 C:/Users/70236/.codex/worktrees/t021-coordination/bioimage-tools-platform，codex/t042-source-only-repair，HEAD2980a0a；旧主目录dirty和.impeccable/questions不动。
- 已实现source_geometry@2（短膜/倾角/多证据Marker/N/独立原ROI），background_support@1（背景不足/内部双峰复核）；网页工作台启用新策略，web_ui HTML/CSS无改动。误开旧Qt测试窗口已关闭，验证入口改WebWorkbenchWindow。
- 8原图源输入识别、冻结后参考评分：旧1/8→新8/8，独审一致；回归集非留出。原图/12参考/旧成果SHA保持。新裁图有残余曲率，不宣称像素匹配。
- 正常网页workbench-web-v3：8成功run、正常导出、保存重开相等、原图不变exit0；另重开DOM结果页48cells/48按钮/busyfalse通过。见.local/t042/workbench-results.png/json。
- 独审df375c4前5缺陷已关闭、12项独立测试exit0；2980a0a均匀背景已裁场兼容增量正在复核。真实积分不能报准确率；支持不足21/48，原始值与有效信号分离，位深极值仍复核。
- 下一步读work/evidence/T-042/validation.md，收集完整check --all session51449/.local/t042/check-all-final.log（626测试，带faulthandler），types-final-head已0错误，收集全门禁，再更新证据。旧600passed/exit1与此次约72项停滞未判根因。
- 完整旧数据不覆盖；未发布/PR/main/干净Windows。原生CUA不重启。源路径仅.local/t042/sources-only.json；参考仅scoring。
