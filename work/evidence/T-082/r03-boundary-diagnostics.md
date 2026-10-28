# R03 状态边界诊断

基线 `918598c0385f91a7669290f07d3ee658100915a5`。原宿主 publish 对所有 ValueError 静默返回，普通异常漏出；网页坏JSON仅toast或直接返回，无可定位事件。先在未改产品的基线上运行新增8项行为检查：**7 failed, 1 passed / 30.22s / exit1**。失败为3种快照异常（ValueError、RuntimeError、受控MemoryError）、3条实际WebChannel坏JSON及实际渲染TypeError；原生未完成编辑原本就保持。原日志 `.local/T082/r03-red.txt`。

## 改动与边界

- 沿用DesktopDiagnostics的Qt消息入口，新增有界 `web-boundary@1` 事件：包版本、动作/阶段、会话/修订、请求及项目的SHA关联令牌、异常类型和最多8条无目录栈位置。没有异常正文、完整URL、JSON载荷、原图或私有路径；WebChannel诊断输入再做长度/字段校验。
- 相同边界在一个失败期间只报一次，成功恢复后允许报告新事件。损坏状态不作为替换项目，错误提示建议重试当前操作/提供本机会话日志。日志写失败不妨碍提示与恢复。没有吞BaseException或自动重复写操作。
- state/progress/session/advanced入口区分解析、最小协议验证和渲染。高级回执在处理前保留草稿/基线/冲突/待处理身份，渲染失败恢复本地编辑状态；同一合法回执可继续。若用户重新读取，只允许新的只读open替换损坏回执的客户端pending，不自动重做保存。
- `IncompleteProjectEdit` 是保持ValueError兼容的明确控件校验类型。WB原生视图仅在读取可编辑控件时使用；历史证据重建及快照序列化的ValueError仍是故障。原始项目组装/公式/历史schema不改。

## 验证

Windows / Python3.12.14 / PySide6 6.12.0，所有Python命令通过 `uv run --locked --no-sync`。Qt使用与现有CI一致的进程局部 `QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu`；仍出现已有mailbox诊断，不宣称GPU根因修复。

1. 首轮同8项：**8 passed / 24.22s / exit0**。
2. 增加高级回执坏JSON/坏结构/渲染失败、日志写失败、诊断传输恶意结构后，运行 `pytest tests/test_web_boundary_diagnostics.py tests/test_workbench_advanced.py tests/test_web_bridge.py tests/test_project_navigation_session.py tests/test_workbench_lifecycle.py -q --tb=short`：**45 passed / 45.15s / exit0**。覆盖真实WebChannel、重复消息、下一条合法状态、未保存29像素行间距草稿保持、宿主原值未改，已有保存/关闭/重开/旧身份回归。
3. `npm run check:web` 格式/lint/checkJs及4门禁自验证exit0；改动Python Ruff、严格定向Pyright均0；`python -m tooling.import_contracts` **9 kept / 0 broken**；`git diff --check`通过。

准确提交独立复核及最终冻结树全门禁仍待办。类型门禁仍仅覆盖R04请求生成器，诊断处最小验证不声称完整UI schema覆盖。
