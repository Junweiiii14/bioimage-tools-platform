# T-006 工作区事务与恢复

2026-10-14；Windows；Python 3.12.14；uv 0.13.0；base 74e6561。
新包 tool-contracts/platform-runtime 0.1.0；storage schema/format 1；WB 0.4.0 未改变。

| 验证 | 退出码 | 范围 |
|---|---:|---|
| 最终 dev.py check --all | 0 | 164 测试，Ruff、Pyright strict、7 import-linter 合约，三 wheel |
| 工作区专项 | 0 | 38 例真实文件/SQLite/CAS/状态/失败/恢复/备份 |
| 独立图正/负例 | 0 / 预期 1 | 8 图含新增 runtime→WB、contracts→SQLite/runtime 传递依赖拒绝 |
| 真实宿主硬退出 | 预期 77 | before_publish / after_publish / before_database_commit 三点；OS 锁释放、旧成功不变，新运行 interrupted |
| 三阶段同大小损坏 | 预期 IntegrityError | 不被大小检查掩盖，不能提交 succeeded；文件保留用于恢复报告 |
| 发布时取消 | 预期 StateConflict | cancelling 不被成功 CAS 覆盖，退出确认后 cancelled |
| 真实 WB→存储 | 0 | 原图导入后被测试修改，worker 仍用独立快照得到 signal 10；新草稿 rev1 不被旧运行 rev0 覆盖 |
| Windows junction / 硬链接 | 预期 IntegrityError | 实际创建临时别名，检测通过；不触碰用户源图 |
| 一致性备份/恢复 | 0 | Connection.backup，旧草稿/结果验证，拒绝重用目标和内部递归备份 |
| 独立 runtime/contracts wheels | 0 | 新 venv、-I、无源码 cwd，无 WB/NumPy/Qt 包；真实子进程退出后提交并重开 |
| 独立 WB wheel | 0 | 保持原 TIFF/分析/真实 worker 证明，不加载 GUI/存储 |

无旧预期/容差削弱，无新 skip。新 JSON schema 从契约模型生成，漂移测试通过。
新的目录规则只使用现有根规则与各包 README；回执更新到实际规则/范围。
目录发布后与 DB CAS 前再次校验；API 不覆盖输入/草稿历史/结果；外部恶意写入不是沙箱承诺。
未知版本不迁移，OS 断电/设备损坏未测试。Qt 存储线程/实际 UI、进程树强停、产品安装包、真实标注和独审未完成。
