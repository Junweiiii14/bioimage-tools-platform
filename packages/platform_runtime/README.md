# 工作区存储

公开入口 platform_runtime.api.Workspace；线程归属明确，一个实例由一个宿主存储线程拥有。
实例独占 OS 文件锁并持有 SQLite；GUI 必须通过后台存储线程调用，worker 不写数据库。
create 只接受新/空目录；open 校验格式版本和工作区 ID，不自动迁移未知格式。

import_asset 复制输入并校验声明摘要；save_draft 使用 CAS 修订并保留旧文档；
prepare_run 冻结指定草稿副本。start_run 只允许一个活动进程；结果提交需要匹配的成功退出回执。
request_cancel 先保存 cancelling；finish_cancelled 在宿主确认退出后调用。
commit_result 的阶段是 staging、文件 fsync/摘要、唯一目录发布、SQLite CAS 成功终态。
宿主可传入 cancelled 检查回调；提交开始/最终校验之后检测到取消会保存 cancelling，
拒绝 succeeded，并保留未登记的发布目录供恢复报告。最终提交检查决定先后；之后的取消不改写历史终态。
文件发布与数据库不是同一事务；失败时不冒充 succeeded，重启将未完成运行标 interrupted。
未发布 staging 移到 recovery；未登记的发布目录作为 orphan 报告，保留而不删除。
backup 使用 SQLite 一致性备份 API 和不可变文件副本，拒绝现存目标与工作区内部目标；
不是简单复制活动数据库主文件。未知格式或数据库版本不自动迁移。

输入、请求、草稿修订与结果经 API 不覆盖；读取检查记录、清单、大小与 SHA256。
拒绝目录穿越、符号链接/junction 和工作区文件硬链接。不是防恶意操作系统写入的沙箱。
操作系统崩溃/断电持久性还依赖目标文件系统；本轮以真实文件/SQLite 与阶段故障测试验证。

测试见仓库根 tests/test_workspace.py；完整门禁还构建并隔离安装独立 wheel。
