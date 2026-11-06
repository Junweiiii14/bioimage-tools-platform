# P016 候选审查与验证

## c08979d 候选

- 本地 `uv run --locked --no-sync python dev.py check --all` exit 0；1735 passed / 10 既有弃用警告 / 1306.93 秒；隔离 wheel 验证全部执行完成。环境 Windows、本仓库锁定环境，QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu。日志 .local/p016-check-all.log，原进程 73881 已终止成功。
- PR67，quality run 42097306782：Linux通过，Windows 1734 passed / 1 failed。规则 run 42097306512 通过。Windows失败为既有 WB discovery 重开测试在异步 continuation 启动前看到临时空白 WBFigureProject；日志明确 open/documents/load 出现在 teardown 后。web_window._backend_closed 先发布新 epoch + idle，再 singleShot continuation，旧等待条件未区分这个临时空窗。修复测试等待条件，额外要求 host.workspace_path == 原工作区，保留原 epoch/idle 条件、20秒超时及全部结果断言，不放宽答案。不是改产品算法或掩盖错误结果。
- 只读独审 /root/p011_independent_review 对 c08979d 实证 P2：损坏 SQLite 异常未在 _ImageIO 线程边界捕获，完成槽断言 None，前端未发布失败。独审核对真实46核导出字节/身份和项目内导出拒绝通过，显示适配2项通过；随后因代理用量限制退出，不能视为整体验收通过。

## 审查修复（待新提交绑定）

- _ImageIO 明确捕获 sqlite3.Error，沿原失败路径发布错误、释放忙状态，不吞异常为零，不改存储或历史。
- 新增真实 QThread / 临时 Workspace 两例：数据库损坏、缺失，检查 idle、busy=false、failed、count=None、保留前一图和SHA，随后可重新选图。test_nuclei_ui.py 共6 passed /31.45秒；定向 Ruff 与 pyright 0错误。没有模型/网络依赖，也没有更改任何数值容差或skip。
- 后续需：新提交独审、更新PR必需CI、最终截图与逐项验收。尚未集成或完成。
