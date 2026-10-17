# 测试子进程退出诊断

bbf3cc5远端Windows job117368899146完整pytest668passed/508.43秒，随后外层exit1，未运行wheel。原20循环与web drain均通过，没有60秒超时/native输出；仍为失败，不能说完整check通过或由此断言Qt崩溃。日志.local/t043/ci006-windows-failed.log。Linux同时在诊断模块平台类型失败，CI007最小guard已另行独审。

观察器在child.wait后打印原始十进制及32位hex退出码，再原样返回；无payload，不增加超时或改为成功。现有真实子进程17非零/诊断自身失败两条回归新增精确文本断言，原返回码断言保留；其余进程归属、进度及开关不继承测试均保留。定向8项和类型实际exit0，时间见本地ci008-targeted.log；产品仍a811ccfd，完整本地668/508.54秒及全部隔离wheel exit0的绑定不变，未冒充此增量已跑新全量。

新远端候选用于区分pytest正常非零退出与native异常终止；得到真实返回码前根因UNKNOWN。不跳过Windows或修改门禁状态，不直接合main。

f5b1fe4绑定独审无阻断，审查者独立8项/6.30秒/实际exit0。另核对固定pytest插件unconfigure会禁用faulthandler，只有启动已启用才恢复；CI补PYTHONFAULTHANDLER=1，并在原环境隔离测试断言传递，未改变取消、退出码或时限。真实子进程启动前/pytest结束后is_enabled均True且8项exit0，ci008-retention.log保留；这提供退出期栈机会，不保证所有native快退出均可捕获。来源[Python3.12 faulthandler](https://docs.python.org/3.12/library/faulthandler.html)及固定环境_pytest/faulthandler.py，2026-10-17核验。

f2a61b3追加独审无阻断，保持15分钟/退出/产品。启动故障处理环境的桌面诊断+观察器+dev环境11passed/4.14秒/实际exit0；首个误写tests/test_diagnostics.py无测试exit4保留，改正确test_desktop_diagnostics.py后完成。当前清单来源f2a61b3保留CI008回执。
