# CI-009：新工作区数据库原子初始化

- 状态：in_progress；T043性能/全门禁修复授权。
- 1bb1d9d Linux668/183.03秒+全部wheel成功；Windows1failed667passed/516.76秒，真实child exit1。metadata close测试setup等待创建5秒，阶段日志显示Workspace.create执行6.125秒，随后正常emit/deliver。不是本轮原生异常或永久挂起；bbf先前668passed后exit1仍UNKNOWN。
- 代码新建库executescript无显式事务，PRAGMAuser_version/5表分别autocommit，再另一次元数据INSERT提交。改为单一显式事务，保留SQLite同步/格式v1/原有库读取、不降低fsync或测试时限。
- 先以真实SQLite在metadata INSERT失败注入，独立查询初始化应原子rollback无表/版本0；旧红新绿。记录本机新目录创建前后耗时分布和事务边界，不外推托管runner必然低于5秒。
- 相关真实存储/异步/故障恢复、类型与独审后正式全量check和原图功能链；阶段清单刷新，安全备份/普通推送，main不变。所有失败/原图/旧结果/原未提交改动保持。
