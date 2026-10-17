# CI-004：异步存储回执超时的阶段诊断

- 状态：in_progress。
- 远端5decc73 Windows完整检查1failed/656passed，tests/test_wb_host.py首个create等待10秒超时，finally shutdown完成；不能断言永久死锁。此前阶段7同类等待5秒失败，原SHA重跑通过，失败记录保留。
- 只读独审未定位确定丢回复缺陷，60秒栈捕获不覆盖10秒失败。增加enqueue→execute→Workspace完成→reply emit→GUI deliver的单调时间、请求ID及线程ID日志，测试失败保留capture；不记录路径、输入字节、结果或图像。
- 不改时限、预期、skip或依赖；默认DEBUG关闭，不改FIFO、线程归属和关闭协议。完整门禁及绑定提交独审后同步阶段8。
