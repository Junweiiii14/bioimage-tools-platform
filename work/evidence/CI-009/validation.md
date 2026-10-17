# 新工作区初始化事务

1bb1d9d真实Linux668/183.03秒及全部隔离wheel成功；Windows1failed667passed/516.76秒、child exit1，metadata close测试setup等待create超过5秒。DEBUG阶段执行区间6.125秒，结束/emit/deliver同刻；包含文件写入、fsync、目录和SQLite，不能将全部延迟归因某个调用。旧bbf3cc5的668passed后exit1仍UNKNOWN。

Python3.12.14/Windows、原SQLite设置；executescript本身不启事务，旧user_version与五条DDL逐条autocommit，再metadata INSERT提交。仅在脚本开头BEGIN IMMEDIATE，保留最后INSERT后commit；版本、表及身份一次提交，异常close回滚。必须放在脚本内，避免executescript预先commit。格式v1/schema/旧库读取/同步/fsync均不变；只减少冗余提交并增强数据库初始化一致性，目录和header失败残留继续保留。

真实SQLite authorizer在metadata INSERT返回SQLITE_DENY，旧代码红例1failed/1.00秒：独立连接看到user_version1/半初始化表。修复后同测试及全部Workspace/AsyncStorage45passed/11.05秒/实际exit0，独立查询版本0/无表，随后Workspace.open到版本验证证明owner锁释放；非mock SQLite或改预期。类型实际0错误。原5秒等待与全部旧断言保持。

本机新目录每组20次create+close顺序描述性计时：旧median56.76ms/max68.08ms；新median27.38ms/max35.93ms；分别保留ci009-bench-before/after timing.json与全部新目录。不是托管runner基准或所有创建必小于5秒的保证；缓存/调度并非完全受控。

依据：[Python3.12 executescript/transaction](https://docs.python.org/3.12/library/sqlite3.html#sqlite3.Cursor.executescript)、[SQLite事务](https://www.sqlite.org/lang_transaction.html)、[user_version](https://www.sqlite.org/pragma.html#pragma_user_version)。2026-10-17核验。绑定独审、完整门禁和8原图正常工作台复验另记，不沿用旧668结论。
