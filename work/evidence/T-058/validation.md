# E5/T058 验证（实施中）

base9d747ef，Win11/Python3.12.14/Qt6.12.0，锁/门禁未改；规则输出已读取，回执随任务保存。

- 新核心3 passed/2.58s：1–96槽数性质、重复蛋白独立身份/空值、裁剪失败显式状态、schema13旧表结构不变/schema14旧读拒绝、部分索引/恢复资产重映射摘要稳定。
- 新导出/旧归档/E4核心联合37 passed/8.34s（.local/t058-core-adapter.txt）；新增最后CSV解析预期后7 passed/5.09s（.local/t058-core-final-substep.txt）。两Fig全部原图/固定槽位、原始三角积分400×来源倍数×槽位、无信号空值、输出索引实际成员SHA/长度、完整导出/重复导出旧ZIP不变/归档重新检查、缺run降为部分、变源、取消和ENOSPC注入均覆盖。
- 纯适配测试的RunRecord PID123明确为应用边界夹具，不是实际worker或本机成功收据；真实宿主/worker到导出/CAS未验收。
- 开发失败保留：初次裸test模块导入不适用当前pytest importlib模式，改为现有命名空间测试助手路径；StagedProjectArchive误用位置参数导致摘要拒绝，改明确关键字而不改预期。首版冻结复制无扩展被既有TIFF入口正确拒绝，现仅按已验证容器头保留读取器扩展，不绕过TIFF/原值检查。新增测试块一度置于取消测试中间产生NameError，已修回所属测试；没有弱化断言/容差/预算/时限。
- 核心/适配定向Pyright0，第一次全仓Pyright仅测试decoded列表缺注释3项，补明确LoadedProjectResult类型；最终全仓待重跑。Ruff格式/导入机械修正。新进程API不加载任何PIL模块探针0。
- 未完成：宿主/界面/恢复故障集成、隔离wheel14、最终完整check、绑定最终提交非作者独审。E5仍implementing。
