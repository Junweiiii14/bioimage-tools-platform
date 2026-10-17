# CI-005：Windows Qt挂起的原生栈证据

- 状态：complete（诊断证据阶段）；沿T043明确授权，真实失败已捕获并转CI006修复，不以诊断本身代替修复。
- ea6178e远端Windows15分钟取消；60秒栈停于test_web_bridge.py:128关闭等待中QTimer.timeout.connect，2线程无Python帧；Linux659/184.75s及wheels0，本机659/509.86s及wheels0。
- 本机精确关闭50次/26.81s/exit0，未复现；停止同样压力重复。只读源码提出Qt共享对象锁与PySide连接GIL顺序假设，需要实际native栈验证，不能归因GC。
- 仅Windows显式诊断开关对pytest子进程失去输出60秒时采一次原生栈；父进程只监控自己启动的Python子进程树，包含Windows虚拟环境启动器后的实际解释器。只输出模块basename/函数/偏移，不生成内存dump、不传环境或payload。Suspend只用于复制context，立即Resume后才解析栈，不单独超时杀死采集器或测试子进程；查符号阶段已恢复目标线程。
- 保留全部用例、退出码、环境隔离、15分钟CI和原断言；诊断失败不改成功状态，不杀用户进程。新增单元/真实子进程/native探针，绑定提交独审后完整门禁与精确阶段清单。
