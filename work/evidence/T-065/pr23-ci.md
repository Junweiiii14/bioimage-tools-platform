# PR23 Windows失败与完成条件修正

原head6bba535，quality39410431350，Windows job118586677989：[实际失败日志](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/39410431350/job/118586677989)。Windows930项中1 failed、929 passed/589.26s，原pytest退出1/u32=1，隔离wheel未执行；Linux、桌面环境、规则检查SUCCESS。不是native退出，不以局部通过抹去失败。

失败在tests/test_instrument_intake_desktop.py重开同名导入根测试：等待 `session_epoch==1 && shutdown_stage==idle` 后立即调用current，看到新host的空schema1文档。来源池在此前导入/去重/双组断言均通过；此错误不证明原图丢失。

源码对应web_window.py._backend_closed先替换host、设置idle/发home状态，再以QTimer.singleShot(0, continuation)继续open_project；后者才转opening并异步open/load真实文档。旧等待条件可能在continuation启动前成立。日志显示失败点后，teardown期间open/documents/load正常入队完成，符合这个时序。

修正测试等待条件：同时要求精确原project_id已装入新host且非忙态，再执行未改变的完整来源集合相等断言；20秒时限不变，不删除断言、增加容差、skip或改变门禁。产品代码不改。本次只修正成功条件，不宣称修复其他原生UNKNOWN。

局部验证与提交绑定非作者复核见后续条目；不得直接重跑服务器掩盖本次原始失败。完整最终候选本地门禁仍留待P7。
