# P016 候选审查与验证

## c08979d 候选

- 本地 `uv run --locked --no-sync python dev.py check --all` exit 0；1735 passed / 10 既有弃用警告 / 1306.93 秒；隔离 wheel 验证全部执行完成。环境 Windows、本仓库锁定环境，QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu。日志 .local/p016-check-all.log，原进程 73881 已终止成功。
- PR67，quality run 42097306782：Linux通过，Windows 1734 passed / 1 failed。规则 run 42097306512 通过。Windows失败为既有 WB discovery 重开测试在异步 continuation 启动前看到临时空白 WBFigureProject；日志明确 open/documents/load 出现在 teardown 后。web_window._backend_closed 先发布新 epoch + idle，再 singleShot continuation，旧等待条件未区分这个临时空窗。修复测试等待条件，额外要求 host.workspace_path == 原工作区，保留原 epoch/idle 条件、20秒超时及全部结果断言，不放宽答案。不是改产品算法或掩盖错误结果。
- 只读独审 /root/p011_independent_review 对 c08979d 实证 P2：损坏 SQLite 异常未在 _ImageIO 线程边界捕获，完成槽断言 None，前端未发布失败。独审核对真实46核导出字节/身份和项目内导出拒绝通过，显示适配2项通过；随后因代理用量限制退出，不能视为整体验收通过。

## 审查修复（待新提交绑定）

- _ImageIO 明确捕获 sqlite3.Error，沿原失败路径发布错误、释放忙状态，不吞异常为零，不改存储或历史。
- 新增真实 QThread / 临时 Workspace 两例：数据库损坏、缺失，检查 idle、busy=false、failed、count=None、保留前一图和SHA，随后可重新选图。test_nuclei_ui.py 共6 passed /31.45秒；定向 Ruff 与 pyright 0错误。没有模型/网络依赖，也没有更改任何数值容差或skip。
- 后续需：新提交独审、更新PR必需CI、最终截图与逐项验收。尚未集成或完成。

## 16d32b12f3980cf2dcaeb3ec9d145488378c6dcd 独审通过

只读代理 /root/p011_independent_review 已完成，base a7612843e5216f0471b51be93bd3687f0b8dbc82。结论：已发现P2关闭，无其他可复现阻断问题。核查提交身份、原图/标签摘要、原坐标显示、唯一目录导出、取消与关闭等待接线、轻量默认依赖及隔离wheel调整，P015数值流程未变。

独立 `pytest tests/test_nuclei_ui.py tests/test_nuclei_web.py tests/test_instrument_intake_desktop.py::test_export_discovery_real_worker_save_and_reopen -q` 为8 passed /6.98s/exit0；显示适配2 passed/0.84s/exit0，Windows offscreen、--disable-gpu。实际保存样例独立核对46个非零实例ID、运行身份、标签摘要、显示尺寸、导出字节及项目内导出拒绝。

审查限制：未独立重跑真实模型、全仓或完整应用运行中关闭；四主题、高DPI、Linux实际模型、学生首次配置和科学验收未覆盖。首次配置指南仍需读源码README，没有界内直接打开指南，为非阻断可用性改进项。

作者增量验证：6控制器通过，Ruff/pyright通过；WB正确目标测试等待条件修改后1 passed/3.45s。规则回执检查16d32b1相对main通过。产品/测试已push，PR67新quality run 42157212799运行中，规则run42157213226及desktop-environment已通过；尚未合入。

## 最终截图

16d32b1当前Qt工作台，经真实WebChannel打开已提交公开46核项目（此次原生目录选择器替换，仅用于可重复截图，不冒充实际点击走查）。`.local/p016-final-1440.png` 和 `.local/p016-final-960.png` 分别1440×940、960×640；已由view_image人工检查，当前“已保存核数46”、原坐标轮廓、切换/缩放、设置及固定导出按钮可见。小窗口正文可滚动；截图不代表四主题/高DPI验收。临时harness `.local/p016_capture_test.py` exit0，1 passed/3.72s；首次harness错误等待裸字符串46（实际为已保存核数46）超时，改为实际可见文案后通过，未为截图更改产品。

## 最终CI与集成

最终验收：PR67已合入main 6bd4680530dc4697f8d394a96fd288723222ddb8，与候选16d32b12f3980cf2dcaeb3ec9d145488378c6dcd文件树diff退出0。quality42157212799成功：Windows1737 passed/10 warnings/1410.11s；Linux1733 passed/4既有Windows专用skip/10 warnings/951.94s；两平台随后wheel/check --all完整通过。rules42157213226、desktop-environment通过。只读独审绑定候选通过。2026-11-06已成功向上游01a19bfd-f3ab-7502-86da-9f61953d1c8a(local)发送正式入口/截图/证据/CI/独审/PRmain/边界和下一建议，要求自动接续。观察进程87597已exit0。
