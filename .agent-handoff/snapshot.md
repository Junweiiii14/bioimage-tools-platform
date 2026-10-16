# Handoff Snapshot

- 更新2026-10-16；当前T-035比例自动裁图，唯一状态work/tasks/T-035-ratio-crop.md。总体WB T003继续，非整套产品完成。
- 活动树C:/Users/70236/.codex/worktrees/t021-coordination/bioimage-tools-platform；codex/t035-ratio-crop；产品25ac71d。旧主目录dirty与.impeccable/questions保留。
- 新网页导入lane_ratio@1，宽/高=1.25*n，原像素裁图不重采样；旧项目/原生默认legacy不静默重裁。n控宽保高，undo/redo冲突metadata在恢复前验证。
- 自动完成直接拼图，无逐图确认；manifest命中区点回对应原图；改n/拖框后重算。pending/failed不冒充就绪，定量质量独立。
- 指定G4与M2叠加源图均1344×1100 RGB8，3/5泳道，236×63与394×63裁图。输入hash不变、导出原值裁图逐像素等于原图切片，完整UI闭环通过。历史混合文件5/10不作当前准确率结论。
- .local/t035含真实输出、验证JSON、截图、启动新版桌面.cmd。网页预览http://127.0.0.1:50617只展示记录和草稿，科学计算在同源桌面宿主。
- 25ac71d独立代码复审通过，18专项退出0；视觉ship，独立documenter已同步设计。最终全量582项及隔离wheel门禁退出0；首次581 passed但退出1异常仍保留，见任务/验证。
- 下一步高级曲线/OCR/模板/归一化网页化（目前仍原生窗口）、更多真实标注。干净Windows/远程CI/PR/main集成未做，禁止扩展其他工具。
