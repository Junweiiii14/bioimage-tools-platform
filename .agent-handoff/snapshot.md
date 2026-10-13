# Handoff Snapshot

- 更新：2026-10-13；Codex；bioimage-tools-platform。
- 当前任务唯一状态源：`work/tasks/T-002-p0-validation.md`。
- 用户授权：P0 本机打包、真实窗口、性能；干净 Windows 无 Python 验收留待后续。未授权扩大 WB 或恢复归档项目。
- 分支 `feat/T-002-p0-validation`，基线 main `221a2df`（PR #2 已合并）。
- 当前：独立 P0 探针完成源码自验，35 个测试通过；正在编译与实际窗口验证。未宣称完整 P0 退出或技术栈冻结。
- 下一步：干净提交构建 standalone，包态真实进程/窗口/性能，记录限制，按 PR 提交。独立审查未进行，不自动把作者自验算作独审。
- 活动入口：`tooling/p0/README.md`、`p0_probe.py`、`tooling/p0/`、`work/evidence/T-002/`。
- 已知问题：源码 pythonw 窗口被 Computer Use 误归入已安装 IDLE，刷新仍报 window owner mismatch；需尝试独立 EXE。Windows os.read 与 NumPy DLL 加载锁冲突已用 ReadFile 修复；uv 启动器子进程已绕过。
- 构建/样本/大日志只在 `.local/p0/`，禁止提交原图或二进制安装包。四项 GitHub 必需检查与回执机制保持。
