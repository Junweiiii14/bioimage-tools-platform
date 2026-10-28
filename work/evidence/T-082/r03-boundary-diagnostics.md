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

## 独审反例与修补

05c1a16非作者审查 **Request changes**，不是Accepted：真实click/open入口仍挡住损坏回执后的只读重试；acceptState先提交epoch、sync先清草稿，跨身份渲染失败可丢草稿且拒绝后来的旧合法状态；recovered诊断传输抛错会反向打断有效恢复。独立原16测试虽通过，但不能覆盖这些反例。

- 在未修入口的05c1a16上新增实际UI点击open/write/public_open三例，**3 failed / 6.99s / exit1**，均没有发出第二次只读请求；修补只放行receiptFailed时reload/同工具open，不放行重复保存。旧回执不能覆盖新读请求。
- 状态/会话接收边界新增短生命周期编辑检查点；失败回滚state/epoch/路由及既有各工具编辑数据，并失效显示缓存。只克隆本地表单/几何/身份，不克隆原图和大状态；未完成指针手势取消，已编辑草稿保持。成功即释放备份，不建立第二套持久状态。高级、导入分组/计划/裁剪/积分/拼图网格与手动编辑都沿各自原有权威数据恢复。
- diagnostic recovered使用与report同样的传输异常隔离，不影响正常业务恢复。

新增同/跨epoch实际渲染异常、会话home渲染异常、诊断恢复传输异常、仪器导入草稿恢复；同时覆盖已有高级、导入、生命周期、手动泳道、项目导航六文件回归。第一次完成检查点77通过后，为缓存失效/会话home增加验证，最终 **78 passed / 67.46s / exit0**。命令文件集为 `test_web_boundary_diagnostics.py test_workbench_advanced.py test_intake_web_ui.py test_workbench_lifecycle.py test_manual_lanes_workbench.py test_project_navigation_session.py`，仍锁环境及CI软件渲染。Ruff/严格Pyright与JS门禁通过。补丁准确提交复审与最终冻结全门禁待办。

## 第二轮独审反例与修补

ad12225 非作者复审仍为 **Request changes**：非home会话路由原地修改state.selectedId，检查点只保存state引用；全组草稿恢复后清空contentKey，下一条同身份合法状态重绘又清空草稿。独立23项通过并不能排除这两个缺口。

新增真实页面操作，第一项在原ad12225上 **1 failed / 2.81s / exit1**（`.local/T082/r03-route-red.txt`）；第二项在原group_review上 **1 failed / 3.21s / exit1**（`.local/T082/r03-group-red-final.txt`），失败位于后续合法重绘后的hasDraft断言。建立第二项夹具期间曾误设项目行数为2而实际为3、误用input而真实处理为change；这些夹具失败不算产品反例，修正后才计入上述有效红例。

检查点现在浅拷贝state顶层投影，保持嵌套科学载荷引用；groupReview保存语义contentKey，并用独立repaint标记失效DOM。只有真正身份/修订等键变化才清空草稿，同身份恢复重绘继续显示编辑后的数值，不将旧草稿迁入新项目。

`pytest tests/test_web_boundary_diagnostics.py tests/test_group_review_workbench.py tests/test_project_navigation_session.py -q --tb=short`：**41 passed / 22.95s / exit0**（`.local/T082/r03-second-followup.txt`）。两个新增测试分别验证非home路由失败后恢复原行和手工草稿、恢复后的下一条合法状态仍保留真实基线端点数值。仍使用锁环境和进程局部软件渲染；已有mailbox诊断保留。JS完整门禁及4负例通过；Ruff/定向严格Pyright通过。第二轮准确提交复审待办。
