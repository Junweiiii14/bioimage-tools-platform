# Qt 中止专项证据

问题：T-008/T-010均有一次Windows pytest原生Aborted；仅有Python栈，不能确定是QThread提前释放、对象跨线程销毁还是其他Qt断言。T-010栈顶WBBackground._reply的信号发送不是根因证明。

2026-10-14核验官方说明：
- [Qt QThread](https://doc.qt.io/qt-6/qthread.html)：运行中的线程对象不能销毁；finished/deleteLater和wait分别有对象/线程退出语义。现有三个异步端口使用非阻塞wait(0)确认退出，未因猜测改动。
- [Qt消息处理器](https://doc.qt.io/qt-6/qtlogging.html#qInstallMessageHandler)：处理器可能并发调用，应可重入并保留前一处理器；fatal消息返回后程序终止。
- [Python 3.12 faulthandler](https://docs.python.org/3.12/library/faulthandler.html)：保留文件描述符到禁用时，支持显式输出所有线程栈。资料页面当前patch版本3.12.15，本地仍固定3.12.14，不升级依赖。

本地最小探针在独立进程给QThread命名并记录create/start/finish/destroy及pytest阶段；默认与GC阈值80/5分别运行9桌面用例，另一次-s运行9例，共36例通过，无原生复现。探针会改变分配/时序，结果不足以关闭风险；私人过程日志在.local/requirements-review。

决定：增加桌面入口本地诊断，线程安全地记录Qt消息/Python异常，在Qt fatal时主动dump_traceback。实测Python调用qFatal并不必然经过faulthandler的SIGABRT入口，因此必须显式dump，不能只检查普通Python fatal信号。三个独立子进程验证正常恢复处理器、Python异常与实际非零退出前的Qt fatal消息/栈。

限制：没有获得原事故的Qt原因，未改线程/Qt版本，不能宣称已修复。诊断只自动启用于正式桌面入口，worker stdout协议不受影响；pytest本身的Qt捕获可能替换处理器，专项复现应使用-s并保留原始stderr或探针的handler转存。后续真实中止按日志核对原因，再定向修复。跨会话日志总容量回收留待发布整理。
