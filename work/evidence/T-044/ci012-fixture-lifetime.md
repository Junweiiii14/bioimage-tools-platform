# CI012：旧WB测试fixture的GUI对象销毁

## 真实失败和证据

PR15最终文档HEAD3e5cee3，Actions run39104680503，Linux job117607923410在约29%的test_ocr_before_roi_cross_source_and_explicit_binding[png]过程中SIGSEGV，debugger实际255，后续wheel未跑。日志.local/t044/github-linux-39104680503.log。不是733通过后的退出，也不是可选依赖失败；本机a72e710完整成功仍仅本机证据。

GDB线程587在Shiboken::Object::destroy→QObjectPrivate::deleteChildren→QWidget::~QWidget；同时主线程处理posted event。说明确有非GUI线程QWidget析构，不据最近metaType符号猜具体对象。CPython Garbage-collecting标记来自解释器全局gc.collecting，不能因其列在主线程下就认定由主线程发起GC。参考[Qt线程规则](https://doc.qt.io/qt-6/threads-qobject.html)、[CPython3.12.14 traceback实现](https://github.com/python/cpython/blob/v3.12.14/Python/traceback.c)。

## 最小实验和范围

旧test_wb_desktop.make_window仅保存Python列表、close和等resources_closed，没有明确销毁原生窗口；关闭默认只隐藏。自有隔离进程真实create_wb_window，关闭并等后台终止后，构造明确的holder引用环，再后台gc.collect：未dispose组Fatal Aborted实际3；先GUI deleteLater并等isValid false组实际0，destroyed线程ID等于主线程。脚本.local/t044/window_gc_probe.py、window-gc-red/green.log；人为引用环仅为实验条件，不冒充原fixture精确引用环，也不能证明崩溃对象身份。

修正只在该fixture已拥有的每个窗口完成原异步关闭等待后deleteLater，再等待其原生对象实际销毁。没有全局Qt对象删除、全局GC切换、强退出、跳过/放宽测试、改变产品运行或锁文件。也不只加qtbot.addWidget：锁定pytest-qt在用户fixture清理前发close/deleteLater，会早于原异步后台结束。

新增回归要求fixture清理后原生窗口无效、destroyed只能发生主线程，随后后台GC不能再次析构窗口。提取原close/wait为helper、尚未dispose时新断言真实红1failed/2.87秒；增加精确销毁后原11用例绿25.58秒实际0。初次无参destroyed监听lambda产生类型Unknown，改显式object可变参数命名回调；最终相关Pyright/Ruff/格式0，没有ignore。

本修复是测试生命周期的明确缺口修正，产品代码未变；生产旧入口多窗口移除持有路径仍有审计价值，未据此改动或宣称全部历史native根因解决。提交绑定独审、最终远端734用例全检待验证；不得将当前PR标记完整通过。

## 绑定独审与错误清理补正

5c932b8独审整份11项24.94秒实际0，发现新回归finally仅isValid就deleteLater：若helper等待后台超时，会提前销毁仍有线程的窗口（P2）。正式fixture helper本身顺序正确。后继finally改复用同一个close/wait/dispose helper，不以包装器有效代替资源退休；新回归1项2.01秒0、相关Pyright/Ruff/格式0。后继绑定复核与远端734全检待做，不把初审写作无阻断。

后继ab6a68e绑定独审1项1.96秒实际0，P2已关闭，无新增阻断。原3e5cee3 Windows实际733passed575.75秒、child0、全部wheel/dev成功；同run Linux失败保持。审查后ab6a68e已备份核34原未提交并安全push；最终文档后继的远端734全检结论见PR15/issue6，不以本地/旧HEAD通过替代。

## 同类项目fixture补齐

等待734远端期间只读检查发现另外三处同类共享fixture：test_figure_desktop.project_window、test_project_measurements.windows、test_automatic_workflow.automatic_window。独审只读确认均在close/wait后未销毁，限定各自拥有的对象补deleteLater/waitinvalid；保留所有关闭后业务断言、原等待阈值和失败不强删原则，不批量改Web测试、不改产品。

作者三模块28项85.63秒实际0、相关类型/Ruff/格式0；WB/真实Figure两类窗口共同运行主线程销毁/后台GC回归2项1.77秒实际0，因此全套增加为735项。automatic_window初始化yield之前失败的清理没有扩展处理。与旧fixture同类缺口修正仍不能证明远端具体崩溃对象；提交绑定独审及最终735远端检查待完成。旧734运行会因这次精确同类补正推送被正常取消，不当失败或通过。

## 有范围的窗口测试生命周期管理

进一步一次只读清点确认bridge/prepared共享fixture、四个Web桥接窗口、独立灰度保存前旧Web重绑定、首页目录Web、独立定量host和两个Platform共享fixture也只close/wait未销毁。保留已有正确qtbot注册/等待路径，不改刻意检验主线程GC的重复关闭用例，不删除全局Qt对象或追随任意根对象。

增加仅用于测试的tooling/qt_test_lifecycle.py：只接收测试明确拥有的窗口和原资源退休判据；确认调用线程、正常close、等待原判据成功，再deleteLater并等原生对象无效。已失效owner直接返回；资源等待错误原样抛出，不强删。Web只销毁owner，不再单独删除其已有父对象的host；Platform保持原active_tool为空判据，产品已安排工具自身deleteLater。原等待时限、关闭后业务断言和初始失败范围保持；此前三共享fixture也共用该路径，避免重复遗漏。

新增真实Qt资源等待失败回归：故意保持未退休，实际等待超时后不允许安排deleteLater；finally仅对没有异步资源的技术QWidget进行正常清理。WB/Figure两类原生析构线程回归继续保留，总数736。作者12模块67项157.28秒实际0，全项目Pyright0/Ruff0/格式525文件0。初次批量替换误触两处测试体close/wait（含跨分支缩进），在执行批次前已据diff还原，两处原业务步骤完全保留；初轮导入排序12项修正后静态通过，没有ignore或放宽测试。

精确补充运行历史：925的734运行中Linux在28%再次SIGSEGV，非主线程574 QWidget析构/主线程QItemSelectionModel::reset，日志github-linux-39105503647.log；其Windows因新提交取消。不能将该Linux失败写成仅取消。c5b5566后继Linux完整735passed133.44秒、debugger0、全部wheel/dev成功；Windows在本批次记录时仍运行。单次通过不证明所有旧故障因果；最终736实际状态以后继PR为准。本批只有测试/工具与文档，无产品代码变化，未再生成原图结果或截图。
