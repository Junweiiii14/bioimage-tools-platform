# Windows原生挂起证据

环境：Windows AMD64，Python3.12.14，PySide6 6.12.0，固定锁依赖未改。当前ea6178e远端Windows作业39019269567/117357627590到15分钟取消；Linux完整659/184.75秒及隔离wheel实际exit0，本机659/509.86秒及wheel实际exit0。

60秒栈停于test_web_bridge.py:128的finally，关闭工作台后等待后台释放；pytest-qt wait_signal.py:37 QTimer.timeout.connect内，20秒等待尚未运行完成；之后gc.collect尚未执行。2条无Python帧线程不足以判GC。只读源码审查提出共享Qt对象锁与PySide普通Python方法跟踪连接的GIL顺序假设，仍需真实native栈，不能记根因已定位。

本机精确关闭路径参数化50次26.81秒/exit0，未复现，停止重复同类压力。独立2秒诊断探针确认pytest faulthandler栈进入日志，exit0。原始日志保存在.local/t043，不上传本地原图或日志路径明细。

## 原生采集实现与失败记录

Windows环境显式BIOIMAGE_NATIVE_STACKS=1仅为pytest启用父进程观察；控制开关从测试子环境移除，防止嵌套测试递归启用。逐行转发原输出，60秒无输出只观察一次，保持原退出码，不增测试时限、不终止测试。只采自己启动的Python树，限制4进程×32线程×24帧；拒绝无归属目标。DbgHelp用进程内锁串行，空搜索路径及忽略环境符号路径，不下载符号，不生成内存dump，只打印模块basename/函数/偏移。目标线程仅复制context期间暂停，finally立即恢复，之后才查符号和展开栈；运行线程的栈为尽力快照，不能假装是原子完整转储。

首轮定向1failed/7passed：虚拟环境python.exe是启动器，实际解释器为子进程，直接父关系校验不足，已改为已验证归属树并检查真实python312.dll帧。第二轮1failed/7passed：GetProcessIdOfThread缺THREAD_QUERY_INFORMATION，采不到THREAD；修正为最小0x4A权限（query/getcontext/suspend-resume，不设context），无帧会明确失败，不伪造成功。最终8passed/2.07秒/exit0，覆盖实际原生帧、错误目标拒绝、诊断失败仍保留子退出码17、正常进度及开关不继承。Ruff/format/Pyright实际exit0。

组合真实路径另验：观察新建Python子进程空闲，默认原生采集捕获启动器及真实解释器，子进程自然退出23，wrapper断言23后exit0；日志.local/t043/ci005-native-watch-integration.log。没有终止用户工作台或改原图。完整门禁和绑定独审另记，以上不等于根因修复。

来源：[Microsoft StackWalk64](https://learn.microsoft.com/en-us/windows/win32/api/dbghelp/nf-dbghelp-stackwalk64)、[GetThreadContext](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getthreadcontext)、[x64 CONTEXT](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-context)、[符号选项](https://learn.microsoft.com/en-us/windows/win32/api/dbghelp/nf-dbghelp-symsetoptions)。锁顺序仅假设：[PySide6.12源码](https://raw.githubusercontent.com/pyside/pyside-setup/v6.12.0/sources/pyside6/libpyside/dynamicslot.cpp)、[Qt6.12 QObject源码](https://raw.githubusercontent.com/qt/qtbase/v6.12.0/src/corelib/kernel/qobject.cpp)。
