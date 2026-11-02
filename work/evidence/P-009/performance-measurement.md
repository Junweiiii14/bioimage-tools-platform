# P009 原生交互测量口径

2026-11-03。测量工具为tooling/benchmark_workflow_authoring.py，复用P006的原生目标命中检查、JavaScript读回、nearest-rank分布和Windows进程内存读取。不改变产品、既有预算或旧P006结果。正式数据必须绑定冻结提交，使用全新输出目录；诊断数据与正式数据分开。

## 场景与样本

| 场景 | 实际负载 | 动作 |
|---|---|---|
| standard | 同一真实WB三节点图；12个明确的合成ROI注释，实际worker先提交表图 | 四主题节点选择、已提交报告预览；neutral暂停/继续/取消 |
| upper | 同源草稿保存为64个真实受信目录节点，其中61个新增原图预检节点；预检通过 | 四主题节点选择；不宣称执行64个worker |

12条注释沿同一合成原图复制ROI、使用不同明确标识，是参数表单负载，不是独立生物样本。上界节点切换在64张常驻DOM卡片中切换verify/analyze；定位/滚动至可命中目标是计时前准备，不代表全画布平移性能。场景规模不偷换成P006旧32行/8Fig工作台表格负载。

默认每组5次预热+30次正式，原始样本完整保留。四主题通过实际外观控件原生点击并确认保存，不通过样式属性伪装偏好持久化。新窗口使用独立QSettings；目标必须完整可见、命中正确元素、原生窗口活跃且页面visible。时间起点紧邻QTest派发；浏览器同时核实event.isTrusted，主动拒绝一次程序化click后才开始采样。

## 终点与解释

- feedback_ms：可信浏览器click时间戳至真实DOM回执后两次RAF；settled_ms另等实际动画完成及两次RAF。没有截图专用的关闭动画或500ms等待，不证明物理屏幕扫描延迟。
- 节点以选中节点和对应实际参数区为回执；预览须成果页可见、实际结果读取完成及已提交报告图加载完成。观察器只读取短DOM身份，避免反复复制整张64节点图污染成绩。
- 暂停/取消只在真实运行状态带PID/Run ID时请求；暂停等待pausing/paused后台确认，另记安全节点边界paused；继续后等待不同实际run_id，才请求取消。
- pause_ack_ms/cancel_ack_ms使用QTest派发前Python单调时钟至真实批次状态回调；pause_boundary_ms另记到已暂停，cancel_to_batch_closed_ms记到真实cancelled/closed。取消后编辑器存储所有者按产品设计继续打开，不能将batch closed冒充整个editor service closed，不能拼接各段p95。
- 结果记录真实请求/终态、RunRecord/PID和存储保留事实；收尾等待编辑器与原宿主资源全部关闭，之后重新打开Workspace核对runs。该最终关闭是资源核验，不伪装成35个完整服务关闭延迟样本。
- 内存仅为host/renderer两个进程PSAPI快照及各自高水位；同进程后续场景的高水位可包含前一场景，不是完整worker树峰值。CPU/OS/Qt/视口/DPR/GPU flags与每次可信/前台事实记录，不宣称目标设备或科学验收。

普通点击100ms初始参考预算按feedback分布对照；超线保留，不删样本、改容差、扩大超时或自动重试来凑通过。工具正常退出仅表示观测完成，不代表预算全部满足。正式采样期间不并行运行本地测试/打包；外部负载若未量化明确保留限制。

## 诊断历史

- r1/r2初始化及后续关闭等待超时，没有正式成绩；GLES/shared-context日志保留。最小实验`.local/p009-storage-pump-probe.log`明确观察到旧QTest.qWait等待期间存储Python槽未执行，进入QEventLoop后立即执行/投递。新工具AsyncEventPump使用真实短Qt事件循环，让Python存储线程获得执行机会；未修改P006工具或产品，也不由此统一解释旧原生故障。
- 新等待方式的实际存储创建/回复/关闭定向用例1passed1.80秒。观察器错误不被吞掉。
- r3已走通四主题节点/预览后，取消确认在自动读取成果的短暂中间状态被误判失效；保留错误。取消回执增加真实终态下取消按钮隐藏这一持续可见结果，仍要求最终真实cancelled/closed、真实run_id及身份不变，未放宽终态/可信事件/时钟守卫。
- r4及加入原生偏好保存/前台核验的r5小样本两场景均退出0，验证测量流程，不称正式p95。诊断时测量工具尚未提交，不能当作冻结基线。各次均新目录，不覆盖原错误。最小等待实验可用storage_event_loop_probe.py及全新workspace路径复现，输出随环境如实记录，不断言所有平台必然相同。

正式命令：`uv run --locked --no-sync python -m tooling.benchmark_workflow_authoring --run --output <全新目录>`。进程环境QT_QPA_PLATFORM=windows，GPU flags如实记录；--samples/--warmup仅供明确诊断，非默认数量不冒充完整分布。26f4470完整正式采样已退出0，原始.local/p009-perf-frozen-26f4470；部分普通节点及全部预览超100ms参考，不能称预算全部满足。

成果清单P1修复后，`--case standard --action results`只复测四主题预览及neutral真实暂停/继续/取消，仍默认5+30，原native/终态/样本断言不变。取消closed事件会触发自动results，也纳入受影响范围。默认action=all保留原完整协议。未改的同步节点选择/64节点数据保留26f原提交，不冒充修复提交实测；新报告显式记录action。内存仍记录实际进程快照，不以限定动作规避旧全协议高值或推断根因。
