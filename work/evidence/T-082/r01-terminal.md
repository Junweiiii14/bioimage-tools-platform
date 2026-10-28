# R01 后台任务终态

基线 8f40aef（产品同18b5cf6），Windows/CPython3.12.14/PySide6 6.12.0，离屏Qt。修改仅 WB 后台请求边界及新增行为测试；原分派操作、科学公式、导出、历史schema均保持。

## 复现与改动

真实QThread上在解码返回/OCR首块返回时用Event阻挡；主线程明确取消/关闭后释放。旧代码漏出 AnalysisCancelled、空MemoryError、RuntimeError，正常回复未到，pending不能清空。相同回归在基线产品代码上 **8 failed / 4 passed / 6 deselected，exit1，5.04s**；原代码只临时载入测试，finally恢复当前文件，证据 `r01-red.txt`。

任务入口现在检查预先取消，捕获AnalysisCancelled为非空取消错误；统一Exception终态保持失败值None。空异常也有类型和错误提示，BaseException退出信号继续传播。通过已有WBReply和正常 `_reply` 排空，没有清空pending、强杀QThread或在工作未结束时宣布关闭。已发布副作用不被入口统一追加的“结束后取消”逆转。

错误用Qt现有会话诊断记录request/operation/revision、类型和最多8层文件名/行号/函数；不写异常正文、私有源路径/局部变量/图像。诊断分配或I/O失败也不能阻断终态。既有预期ValueError/OSError/TypeError提示保持。

原execute已接近Pyright复杂度上限；新增异常处理触发“Code is too complex”。将分派提取到 `_execute`，外围只收口终态。未新增分派模式或改53类操作，既有AST穷尽分派检查仍有效，不降低类型规则。

## 验证

- 最终受影响回归：`pytest tests/test_wb_background_terminal.py tests/test_wb_job_dispatch.py tests/test_worker_retirement.py tests/test_quant_session_identity.py tests/test_manual_lanes_workbench.py tools/wb/tests/test_fig_partition.py -q --tb=short`：**37 passed / 22.16s / exit0**。
- 新18项覆盖开始前/解码后/OCR分块间取消与关闭并发、空MemoryError/RuntimeError；每次一次终态、pending自然清空、同队列小任务可用、关闭一次且线程退出。旧代码失败时仅测试finally排队retire回收有限操作；验收断言之前绝不清理pending，不把teardown当排空成功。
- 真实FigureProjectWindow/存储验证取消、关闭、失败、新草稿拒收旧回复；项目保持、busy退出、后续保存可用、真实资源关闭。已有真实网页手动泳道/历史组回归通过。
- 退出信号不被吞；一次可定位诊断且无私有载荷；故障诊断器仍能回复。Ruff检查/格式与定向严格Pyright exit0。
- 初次测试编辑误用Windows默认文本编码，中文期望损坏，产生额外2失败；已修复测试UTF-8，保留 `r01-initial-encoding-failure.txt`，产品文本未受影响。新草稿测试首次构造非法Fig顺序导致夹具失败及关闭超时，改为合法protein编辑后通过，未改产品保护或测试时限。
- 完整已有门禁、准确提交独审尚待执行，不以定向计数宣布本轮目标完成。存储worker仍使用显式异常列表；本次未把其未复现故障扩大为既定修复。

## 独立复核与错误正文补丁

非作者对462aa4e独审：18测试独立通过、分派AST不变，但发现P2：ValueError子类的`__str__`再抛异常时未发终态，故未接受。新增真实队列“正文格式化失败”正常/并发关闭两例，在462aa4e上**2 failed / 18 deselected / 4.52s / exit1**；见r01-bad-message-red.txt。先准备非空失败回复，再在受保护区域尝试提取既有提示，格式化失败保留原回复。

补丁后新20项及分派/退休/身份回归**36 passed / 6.51s / exit0**。新增参数首轮漏改原RuntimeError类型断言，2失败34通过；现明确断言BrokenMessage，未放松一次回复、pending、草稿、恢复、退出要求。严格Pyright/Ruff通过。

462aa4e发起的全门禁在pytest阶段已出现2失败及GPU消息，等待最终详情。10:28前后继续本补丁后该运行视为被后续改动取代的诊断运行，不作最终提交完整通过证据；最终集成须重新完整门禁。静态阶段此前已通过，失败原因暂不推定。

下一步：绑定补丁提交独立复核；R02核验统一TIFF准入。全门禁失败待最终详情定位。
