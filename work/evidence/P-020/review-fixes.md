# P020 首轮独审修复

上游于2026-11-06回传指定独审对 `3056334e15dca4ea70fc9929b65761e214692136` 的真实复现，要求集中最小修复。正式报告由独审/上游保管，作者不代写通过结论。以下是同一PR72增量，准确新HEAD见上游复审请求。

- **R01/P2**：原表格把所有非数值字段交给状态词典，样本 `blank` 被显示成 `空白`。现在只有 role/status/reason 翻译，样本/板/技术重复等身份原文显示。扩展原真实worker→提交→导出→新进程→损坏拒绝测试，同时保留原S1/LOW场景，并加入blank/空白及板ID sample，页面身份逐一等于正式结果。未改CSV数据模型、算法或正式结果。
- **R02/P2**：QTextBrowser 原先内部处理HTTPS和失效相对链接。现在禁用内部导航，固定文档HTTPS通过既有QDesktopServices进入默认浏览器；P014来源改为基线提交中确实存在的固定HTTPS文件地址。实际鼠标点击两链接的测试捕获桌面浏览器API调用，并确认1000余字符说明保持；file URL不会由此入口打开。未自动下载模型，未增加任意文件加载框架。
- **P3建议**：其他工具占用时BCA run返回明确“等待当前任务完成或先取消”信息，沿用choose既有提示。测试真实选择CSV后切换占用状态，确认提示且不启动任务。
- **全量检查发现的旧预期**：`test_platform_and_tool_home_preserve_draft_and_ignore_background_navigation` 仍断言 installed-tool 数量1；独立复现为1 failed/2.64s。改为当前授权的3工具，所有草稿/导航断言保留。不是削弱门禁，也未修改数值容差、skip/xfail或类型忽略。

## 验证

Windows锁定环境，`QT_QPA_PLATFORM=offscreen` / `QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu`：

- `uv run --locked --no-sync python -m pytest -q tests/test_bca_web.py tests/test_bca_ui.py tests/test_nuclei_ui.py tests/test_platform_home_scroll.py`：exit0，**17 passed / 15.36s**，`.local/p020-review-fixes-final.log`。
- 本轮六个Python文件Pyright：exit0，0 errors/warnings；Ruff check及format：exit0。`python -m tooling.web_quality`：exit0，四门禁自测通过。
- 初轮新测试因Qt JS数组返回转换得到空字符串而2失败/15通过；改为显式JSON字符串传输验证，未改期望身份。初轮类型检查的未类型化Qt回调/测试私有字段访问已用有类型回调和公开选择流程解决，无ignore。
- 旧候选本机第三轮全量检查在36%收到实质修复要求后中止，exit1；曾出现的一项F已按旧单卡断言独立复现并修复。`.local/p020-check-ci-env.log`保留，**没有完整全量成功结论**。初轮格式/第二轮GPU中断也保留。新候选由必需双平台CI执行完整门禁，不再重复本机大矩阵。

原16张截图对应3056334，当前仅身份翻译/帮助外链/占用提示改变，未进行新的布局或主题调整，原截图不冒充新增行为证据。科学、真人、设备DPI、安装与用户安装更新未验边界不变。待指定增量复审和准确HEAD必需CI，上游安排集成。
