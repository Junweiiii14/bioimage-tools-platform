# T-006：工作区输入快照、修订与结果事务

- 状态：review（实现与自验完成；独立审查尚未执行）
- base commit：74e6561
- 上位目标：T-003 持续开发 WB 软件；上轮 T-005 已有真实 worker 自验。

## 范围与必读
允许 packages/tool_contracts、packages/platform_runtime、tools/wb/tests、tests、tooling、docs、work、.agent-handoff、pyproject.toml、uv.lock、.importlinter、README.md。
必读根规则、架构/代码规范、模块地图、WB worker 契约。新公共包由真实输入快照/运行结果保存需求驱动，只提供窄文件资产/修订/运行契约，平台不含 WB 公式或字段。

## 行为与不变量
创建/打开有明确格式版本的本地工作区，单宿主独占锁。输入复制为校验摘要的不可变资产；草稿每次修订单独保存，CAS 防旧草稿覆盖；运行冻结请求副本。
结果 staging→文件关闭/摘要验证→唯一目录发布→SQLite 终态；过程故障不能伪装成功。原始输入/历史结果不可覆盖。
只由宿主写 SQLite；进程退出确认后才提交成功/失败/取消。取消竞态不能被结果覆盖。
重启将未完成运行标 interrupted，保留/quarantine 未提交资产，不删除用户数据。拒绝路径越界/重解析点、未知格式/数据库版本、历史文件损坏。

## 验收
真实文件/SQLite 往返、输入摘要与原图不变、修订历史/CAS、结果唯一与状态机、取消/退出确认、重启恢复、发布与 DB 间故障注入、路径及篡改负例。
新包加入 workspace、公开 api、import-linter、隔离 wheel 测试与现有 CI 命令。

## 验证与审查
2026-10-14：完整 dev.py check --all 退出 0，164 测试、Ruff/Pyright strict、7 导入合约与三个独立 wheel。
38 工作区测试涵盖文件/SQLite、源快照、CAS/历史、真实 WB 子进程、取消/损坏、3 异常点和3真实宿主 os._exit 崩溃、重开与备份。
Windows junction 与硬链接实际负例通过，无 skip；所有测试数据/移动均在自身临时目录内。
平台/契约独立环境不安装 WB/NumPy/Qt；WB 独立环境不依赖存储。现有 Windows/Linux CI 运行完整 dev.py，远程本轮 CI 未运行。
新包 tool-contracts/platform-runtime 0.1.0，已有锁 Pydantic 2.14.1；无第三方版本升级。
存储格式/schema 1，未知版本拒绝，不自动迁移；原算法/输入语义未改变。
新增 gates 与负例，不放宽原预期/容差/skip。已知声明路径先前具备预登记，边界脚本说明及模块地图同步更新。
独审未执行。Qt 宿主、GUI、强停和最终产品验收后续继续，不宣称完成全部软件。
