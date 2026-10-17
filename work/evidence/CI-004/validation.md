# CI-004 回执超时诊断

远端5decc73的Windows检查实际1failed/656passed、426.36秒：`test_actual_wb_host_commit_reopen`首个create在10秒内未收到回复，finally shutdown没有再超时。日志.local/t043/pr14-windows-diagnostic-failed.log；原15分钟无节点取消日志也保留。这次没有60秒线程栈，不能据此定位永久锁死或认定磁盘慢。只读独审同样UNKNOWN。

补充标准库DEBUG日志：每个请求的enqueue、execute-start、execute-end（固定ok/error结果）、reply-emit和GUI deliver，包含单调纳秒和native线程ID；发射前先记录，故同一请求可追踪。默认DEBUG关闭，不建立文件handler/长期缓存，不记录路径、document_id、输入/结果字节或异常正文。Pytest仅捕获该logger，失败自动附录，teardown恢复等级；成功不额外打印。不改线程、队列、取消、持久化或10秒断言。

新增真实存储用例验证失败创建、重试创建、FIFO保存和关闭；各request分别检查阶段顺序，并放入路径、文档、输入JSON及异常正文隐私哨兵，确认日志均不含。定向7passed/9.96秒，首轮工具包装只显示output未保留退出码，不把它作为完整门禁exit0；最终完整check另记。Ruff/format通过，Pyright实际exit0。

诊断本身有日志锁和开销，可能改变竞态概率；启用后通过不表示根因修复。所有旧失败保留。此次顺便纠正活动树AGENT_HANDOFF索引的旧目录指针，与现有snapshot/workspace一致；不修改原dirty历史树。

绑定b4bc8ba..68c32654d8858331429f5f2a081dfe816ab155bd只读独审无阻断；审查者独立执行新增诊断与既有FIFO/错误/关闭2项，实际exit0。最终659项完整check结果见末尾真实退出记录。


CI004产品68c3265正式完整check --all实际exit0：659passed/509.86秒，静态/架构/政策检查和全部隔离wheel、真实OCR/worker均通过；日志.local/t043/check-ci004-final.log，退出码记录.local/t043/ci004-final-gate.json。没有修改时限、预期、skip或依赖；通过不证明偶发超时根因。
