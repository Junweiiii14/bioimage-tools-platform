# Handoff Snapshot

- 更新：2026-10-14；Codex；bioimage-tools-platform。
- 当前任务唯一状态源：`work/tasks/T-002-p0-validation.md`。
- 授权：P0 本机验证与便携包；干净 Windows 无 Python 验收后续。不扩展 T-001/WB 或归档项目。
- 分支 `feat/T-002-p0-validation`；PR #3 草稿，未合并。基线 main `221a2df`。
- 已完成：35 测试、Ruff、Pyright strict；源码原生窗口实操；standalone 构建；ZIP 330 文件解压哈希；包态固定样本、取消/强停/崩溃恢复基准。构建源提交 `293c6c0632e2`，应用 183.5MiB；完整 ZIP（含固定大图集）794MiB。
- 未完成：用户物理 Esc 停止 Computer Use。本轮没有继续桌面工具；包态原生加载/ROI/按钮、GUI 大图峰值与交互 p95、125/200% 进程缩放未测。干净机和跨显示器亦待后续，独立审查未进行。不能宣称完整本机 P0 通过或栈冻结。
- 下一步：用户继续时恢复 T-002，仅补上述未完成验收。重新读取 Computer Use 文档，重新选择窗口，不复用 handle；不要重做已通过的源码或完整编译，除非相关代码变化。
- 包：`../deliverables/BioimageP0-Windows-x64-293c6c0.zip`；已解压到 `../deliverables/P0独立验收/BioimageP0-293c6c0`。GUI PID 40464 启动后留给用户控制，后续须核对进程现状。
- 证据：`work/evidence/T-002/validation.md`（含 ZIP SHA、包态基准、限制）；脚本：`tooling/p0/README.md`。最小环境启动已完成、实际 DLL 来源已记录，但不等于干净机。
- 构建日志/XML 在 `.local/p0/build-293c6c0632e2`。首轮宽泛构建主动中止在 `.local/p0/build-d81350859588`；缓存未删除。二进制与原图不进 Git。
