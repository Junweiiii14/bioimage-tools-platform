# 工作区 v1 与宿主状态

工具文档是经过有限、无重复字段 UTF-8 JSON 检查的 opaque blob，平台不解释 WB/IF/IHC 字段。
AssetRef / DocumentRevision / DraftSnapshot / RunRecord / ProcessExitReceipt / RecoveryReport
由 tool_contracts.api 的严格冻结模型定义，机器 schema 在 storage-v1.schema.json。

目录：workspace.json、metadata.sqlite、assets、drafts、runs、results、.staging、recovery。
格式/数据库版本均为 1；打开先检查标识与版本并取得 OS 独占锁，未知版本拒绝，不隐式迁移。
SQLite 连接及 Workspace 实例只由一个宿主存储线程拥有，GUI 必须异步调度，worker 不写 SQLite。

输入复制成独立资产，按预期 SHA256 校验，不修改原文件。草稿按 expected_previous_revision
进行 CAS；每次修订新建文件，旧草稿保持可读。运行从指定修订复制请求，之后的新草稿不改变它。
一次工作区最多一个活动计算进程；PID 来自宿主启动观察，不能从工作区加载 PID 后直接杀进程。

状态顺序：prepared→running→committing→succeeded；prepared/running/committing
可收到取消进入 cancelling，确认退出后 cancelled；明确失败为 failed，未知/崩溃为 interrupted。
成功提交只接受匹配 run_id/PID、exit_code=0 的回执；未启动回执 pid=0/code=None，不能用于成功提交。
回执类型不代替 OS 观察；Qt 宿主后续须负责实际退出/进程树管理。

结果写入 staging（xb，不覆盖）、关闭/fsync、校验清单/大小/摘要，再移动到唯一 results/run_id。
文件发布后以及 SQLite CAS 前重新校验；最后插入资产并提交 succeeded。取消在 CAS 前胜出时，
不能被旧 completed 覆盖。文件系统与数据库不是同一事务，已发布但未登记目录不算成功。
重启将所有非终态运行标 interrupted；.staging 移到 recovery；孤立发布目录保留并报告，不删除。
历史已完成结果读取时也校验清单/大小/SHA；损坏时拒绝报告为已验证结果。

backup 只能创建工作区外的新目录，复制不可变文件并调用 Connection.backup，支持重开验证；
不覆盖旧备份、不复制 .owner.lock、不把活动 DB 主文件的普通复制当一致性备份。
内部路径不用显示名，拒绝越界、重复分隔符、控制字符、Windows 设备名/末尾点、symlink/junction，
及工作区文件的硬链接；根目录与文档显示名仍可为中文。

当前验证包括真实文件/SQLite、同大小损坏、发布/数据库之间异常与真实 os._exit 崩溃、取消竞态、
原输入改动后快照仍可供真实 WB worker 分析、独立安装。不是 OS 断电/硬件损坏或恶意写入沙箱证明。
schema v1 当前历史样例仅来自本实现；不宣称已支持其他软件的数据迁移。
