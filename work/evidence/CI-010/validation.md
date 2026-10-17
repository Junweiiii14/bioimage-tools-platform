# Linux 测试结束后崩溃的原生观察

0d269db仅11个文档后继，Linux job117379036624真实669passed/146.29秒后0.58秒主线程SIGSEGV、无Python帧，完整check exit245，wheel未执行；Windows job117379036794真实669passed/346.68秒、child0及全部wheel/dev成功。两者保留在.local/t043/closeout-{linux-failed,windows-success}.log。前一becb双平台成功不能覆盖新失败。

pytestqt4.5的qapp为session强引用，根conftest无session销毁；PySide6.12最终清理和QtWebEngine6.140退出都涉及QObject/Chromium收尾，但当前栈不能定位具体扩展。page/profile延迟销毁尚未独立确认不等于已证明UAF，QPointer反证仍成立；不先加猜测性清理。

CI010只增加显式Linux诊断：dev仅对pytest子进程在BIOIMAGE_LINUX_NATIVE_STACKS=1时使用GDB；子环境移除开关避免递归。禁用初始化/自动加载/调试符号联网，限制64线程×24帧且优先故障线程；不打印参数值/locals/内存，不生成core。记录后继续原信号；--return-child-result保留正常退出码，信号终止仍失败，GDB信号退出表示与原subprocess负数不要求整数相等。原15分钟/所有测试不变，产品不变。

Linux CI先以真实0、17和SIGSEGV子程序校验观察器：退出码对应、故障标记和最终Program terminated with signal均须存在，失败则不进入正式全检。此控制尚未在Linux执行，不能以Windows静态/模拟替代。工作流只额外安装诊断gdb并记录版本；原依赖锁不变。

作者Windows相关8passed/2.49秒实际0，Ruff/format0、模块Windows及Linux目标Pyright0。首命令误填不存在tests/test_dev.py导致无测试exit1，另格式首检1处失败已修，均保留日志。Linux原生复验/独审另记，不提前宣称修复。

2026-10-17核验官方：[GDB模式及return-child-result](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Mode-Options.html)、[信号pass/stop](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Signals.html)、[自动加载](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Auto_002dloading.html)。

绑定0d269db..6bef18a只读静态独审无阻断，明确Linux真实控制尚待执行；建议保留系统ASLR，单行后继b7e1caa增加disable-randomization off，追加独审确认无阻断。首次fault后继续传信号，若程序自行恢复，后续fault可能没有第二份栈；仍按真实子结果失败/成功，不吞异常。新阶段清单来源b7e1caa，保留CI010及全部旧历史回执；下一步备份/普通同步后受控原生完整观察，不提前宣称产品修复。
