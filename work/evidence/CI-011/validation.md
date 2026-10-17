# Windows 测试后异常的受控观察

40f Windows job117383522334真实669passed/433.12秒后Aborted→access violation，child3221225477/u32c0000005，完整check失败且wheel未跑。Linux117383522520真实GDB15.1四控制成功、669/158.32秒、全部wheel/dev成功。WSL同锁定Python3.12/Qt6.12/WebEngine6.140/GDB12.1另做669/398.40秒完整pytest观察0（非full dev check）；正常关闭最小实验app.exec返回时page/profile均invalid，退出0，不能凭推测认定必然残留profile。

本机无CDB。仅下载/枚举官方Microsoft.Debugging.Platform.DbgEng 20260319.1511.0包，22MB/SHA875678516f9ceed4a1c8b9b106d165106fcaa38723ad7c584c47b95b231600de，无CDB，未执行/装入任何DLL，不引入产品依赖。转用系统Windows调试API与现有采栈器。

新增显式BIOIMAGE_WINDOWS_FAULTS模式：拥有者Popen仍直接启动/等待pytest，单独观察线程验证直接子启动器、唯一直接解释器、创建时刻与存活句柄（保持句柄防PID重用），仅附加这一个含python312.dll的解释器。DebugActiveProcess只调试当前进程、不跟随其workers；先禁调试器退出杀目标，失败分离不成功则保留事件泵直到自有目标自然退出。不能声称任何OS/API失败都保证分离成功。

附加/等待/继续均在同一观察线程；只消费附加的预期初始breakpoint，其余异常以NOT_HANDLED原样分发。first/second chance分别记录，first chance不等于进程崩溃；有界8个异常键、故障tid优先32线程×24帧，DbgHelp与空闲观察串行，无参数值/locals/内存转储/联网符号。每个事件在finally继续，文件句柄关闭，系统管理的事件进程/线程句柄不混同关闭。退出依据仍是原Popen.wait，实际故障码不得被观察器成功覆盖。没有设置全局调试器/权限/安全策略，也不附加用户当前工作台。

真实控制已在Windows执行成功：0→0、17→17；新建自有小进程的native空入口线程触发AV，原始3221225477保留且first/second chance均有栈；采栈器注入ValueError仍继续事件、原AV不变且不泄漏异常文本；错误owner拒绝附加但子17保留。控制先握手附加完成才触发，日志.local/t043/ci011-real-controls-final.log，完整控制命令exit0。新增真实集成测试确认run_with_native_watch返回c0000005并记录原退出。

作者相关9passed/2.64秒实际0；Ruff/format0、修改模块Windows/Linux目标Pyright0。最初Linux目标15项错误为三个辅助函数缺平台guard，已补真实非Windows拒绝，无ignore；首轮字符串长行/回调loop binding等格式失败保留并修正。新增一项跨平台分支测试：Windows验证真实fault原码，Linux验证明确平台拒绝，不新增skip/xfail或放宽旧断言。产品/公式/schema/依赖锁/原15分钟和旧测试时限不变。正式670完整check、绑定独审与远端另记，当前只是观察能力，不宣称原崩溃修复。

2026-10-17主来源：[DebugActiveProcess（ONLY_THIS_PROCESS）](https://learn.microsoft.com/en-us/windows/win32/api/debugapi/nf-debugapi-debugactiveprocess)、[WaitForDebugEvent及句柄](https://learn.microsoft.com/en-us/windows/win32/api/debugapi/nf-debugapi-waitfordebugevent)、[DEBUG_EVENT结构](https://learn.microsoft.com/en-us/windows/win32/api/minwinbase/ns-minwinbase-debug_event)、[ContinueDebugEvent](https://learn.microsoft.com/en-us/windows/win32/api/debugapi/nf-debugapi-continuedebugevent)。
