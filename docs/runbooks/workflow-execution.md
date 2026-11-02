# 原图工作流执行

桌面入口：`uv run --locked --no-sync python -m bioimage_app --workflow-ui`。

选择真实TIFF及已有AnalysisRequest JSON，填写一个不存在的新工作区路径，然后开始；也可显式选择合成验证输入。原图快照、请求、真实运行记录和已提交成果保存在该工作区。

界面列出步骤及真实运行编号；只有宿主确认进程退出、成果校验、正式提交及账本落盘后才显示已提交。暂停等待当前步骤完成，继续沿冻结计划运行；取消等待实际进程退出。关闭暂停执行会保留它；关闭活动执行会取消并等待存储和进程退出。填写原工作区路径及执行编号，可重开并继续或重试中断节点。

暂停或完成后，可更换参数JSON或报告排版，然后选择“应用调整并运行”。它在同一工作区创建新执行和新图修订，按实际依赖复用已提交成果，不覆盖原执行。仅报告排版变化不重做定量。损坏的输入或成果明确报错，不作为零值或缓存成功。

命令行使用相同执行器：

```powershell
uv run --locked --no-sync python -m bioimage_app --workflow --workspace <新目录> --validation triangle_u16
uv run --locked --no-sync python -m bioimage_app --workflow --workspace <新目录> --source <原图.tif> --parameters <参数.json>
uv run --locked --no-sync python -m bioimage_app --workflow --workspace <已有目录> --resume <执行编号>
uv run --locked --no-sync python -m bioimage_app --workflow --workspace <已有目录> --rerun <执行编号> --layout compact
```

这是固定原图三节点的执行入口；完整模块画布编辑属于P009。合成数值和本机工程运行不代表独立科学留出、干净Windows或物理DPI验收。
