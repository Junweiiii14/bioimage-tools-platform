# PR23 Windows失败与完成条件修正

原head6bba535，quality39410431350，Windows job118586677989：[实际失败日志](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/39410431350/job/118586677989)。Windows930项中1 failed、929 passed/589.26s，原pytest退出1/u32=1，隔离wheel未执行；Linux、桌面环境、规则检查SUCCESS。不是native退出，不以局部通过抹去失败。

失败在tests/test_instrument_intake_desktop.py重开同名导入根测试：等待 `session_epoch==1 && shutdown_stage==idle` 后立即调用current，看到新host的空schema1文档。来源池在此前导入/去重/双组断言均通过；此错误不证明原图丢失。

源码对应web_window.py._backend_closed先替换host、设置idle/发home状态，再以QTimer.singleShot(0, continuation)继续open_project；后者才转opening并异步open/load真实文档。旧等待条件可能在continuation启动前成立。日志显示失败点后，teardown期间open/documents/load正常入队完成，符合这个时序。

修正测试等待条件：同时要求精确原project_id已装入新host且非忙态，再执行未改变的完整来源集合相等断言；20秒时限不变，不删除断言、增加容差、skip或改变门禁。产品代码不改。本次只修正成功条件，不宣称修复其他原生UNKNOWN。

局部验证与提交绑定非作者复核见后续条目；不得直接重跑服务器掩盖本次原始失败。完整最终候选本地门禁仍留待P7。

a263fee等待条件修正作者单项3.10s实际0，非作者冻结单项4.46s实际0、无行动项；产品无diff、成功条件严格增强，原时限/来源断言不变。后继CI39412508698该重开用例通过，但Windows仍1failed/929passed/572.08s、实际pytest1/u32=1，wheel未运行。失败为原手动泳道真实指针坐标预期35/40/20/40，实际39/42/16/38，原abs1未通过。

非作者冻结a263诊断：自然轨迹证实测试设zoom1.4后，首次sessionStateChanged路由晚到，switchMode将zoom重置1；原测试有一次仍通过，说明其声明的缩放前提并未成立。可控Qt重排旧取点路径1fail，新等待两帧后取点1pass（原abs1），合计1fail1pass/5.33s实际1；自然轨迹分别1/5.95s与1/4.21s实际0。此人工对照证明取点竞态，不认定CI具体偏移的唯一触发者；远端没有矩形/事件坐标，原日志保留。

窄测试修正：导入前只读监听既有sessionStateChanged，等待目标项目quant路由到达、当前quant行同步且非忙；调用现有route消费已收到token后才设置缩放。details原生键操作之后等待两帧完成布局/fitImage，并明确断言zoom仍1.4，再执行原Qt指针事件和坐标abs1断言。原动作时限、数值预期不变，增加的是有界初始化前提同步；不增加容差或减少事件。作者单项11.11s实际0，Ruff/diff0；产品代码/依赖/工作流未变，待新提交独审。

同轮Linux job118593472193在15m17s超时取消，没有pytest终态/进程成功/wheel证据。Python60s栈为intake_page fixture清理等待、StorageWorker.retire的moveToThread；没有实际故障native栈，不把它归因本次坐标或先前锁/GIL机制，不修改门禁掩盖。原长日志在忽略目录.local，后继检查仍须完整完成；历史UNKNOWN保留。

最终7f46334da85e890feecf0caa4ac3f81e6c0bd093原非作者单项13.86s实际0、无行动项。CI39414898283四项SUCCESS：Windows10m57s、930pytest/563.63s且原child0/u32=0；Linux6m56s、930pytest/352.88s且原debugger0；两者全部隔离wheel、真实PP-OCRv6/worker/PNG OCR完成，最终check成功；桌面31s、规则6s。原失败及UNKNOWN保留，不因此认定间歇根因已定位。2026-10-20T11:38:13Z正常精确merge PR23，main e842c6c040cf42a8268ac4af0bb6457c878970e0；未绕过服务器规则。
