# CI012：旧WB测试fixture的GUI对象销毁

## 真实失败和证据

PR15最终文档HEAD3e5cee3，Actions run39104680503，Linux job117607923410在约29%的test_ocr_before_roi_cross_source_and_explicit_binding[png]过程中SIGSEGV，debugger实际255，后续wheel未跑。日志.local/t044/github-linux-39104680503.log。不是733通过后的退出，也不是可选依赖失败；本机a72e710完整成功仍仅本机证据。

GDB线程587在Shiboken::Object::destroy→QObjectPrivate::deleteChildren→QWidget::~QWidget；同时主线程处理posted event。说明确有非GUI线程QWidget析构，不据最近metaType符号猜具体对象。CPython Garbage-collecting标记来自解释器全局gc.collecting，不能因其列在主线程下就认定由主线程发起GC。参考[Qt线程规则](https://doc.qt.io/qt-6/threads-qobject.html)、[CPython3.12.14 traceback实现](https://github.com/python/cpython/blob/v3.12.14/Python/traceback.c)。

## 最小实验和范围

旧test_wb_desktop.make_window仅保存Python列表、close和等resources_closed，没有明确销毁原生窗口；关闭默认只隐藏。自有隔离进程真实create_wb_window，关闭并等后台终止后，构造明确的holder引用环，再后台gc.collect：未dispose组Fatal Aborted实际3；先GUI deleteLater并等isValid false组实际0，destroyed线程ID等于主线程。脚本.local/t044/window_gc_probe.py、window-gc-red/green.log；人为引用环仅为实验条件，不冒充原fixture精确引用环，也不能证明崩溃对象身份。

修正只在该fixture已拥有的每个窗口完成原异步关闭等待后deleteLater，再等待其原生对象实际销毁。没有全局Qt对象删除、全局GC切换、强退出、跳过/放宽测试、改变产品运行或锁文件。也不只加qtbot.addWidget：锁定pytest-qt在用户fixture清理前发close/deleteLater，会早于原异步后台结束。

新增回归要求fixture清理后原生窗口无效、destroyed只能发生主线程，随后后台GC不能再次析构窗口。提取原close/wait为helper、尚未dispose时新断言真实红1failed/2.87秒；增加精确销毁后原11用例绿25.58秒实际0。初次无参destroyed监听lambda产生类型Unknown，改显式object可变参数命名回调；最终相关Pyright/Ruff/格式0，没有ignore。

本修复是测试生命周期的明确缺口修正，产品代码未变；生产旧入口多窗口移除持有路径仍有审计价值，未据此改动或宣称全部历史native根因解决。提交绑定独审、最终远端734用例全检待验证；不得将当前PR标记完整通过。
