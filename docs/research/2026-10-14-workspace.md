# 文件资产与 SQLite 的提交边界

问题：怎样在不可覆盖原图/结果的前提下保存草稿、运行与结果，并让进程中断后的状态真实？
决定：平台只保存不透明工具文档与通用资产/修订/进程状态，不把 WB 数值或字段放进 runtime。
AssetRef 的实际复用是输入、草稿、运行请求和结果四种文件提交；没有宣称两个实验工具已验证复用。

SQLite 事务并不把外部文件目录包含在同一事务中。本实现先 staging/校验/唯一目录发布，再
SQLite CAS 终态；取消和提交间按保存状态仲裁。重启未知运行 interrupted，不从目录存在推断成功。
来源：[SQLite 原子提交](https://www.sqlite.org/atomiccommit.html)，访问 2026-10-14；
硬件刷新假设仍存在，本机进程崩溃实验不是断电持久性证明。

备份采用 [Python 3.12 sqlite3 Connection.backup](https://docs.python.org/3.12/library/sqlite3.html#sqlite3.Connection.backup)，
文档当前展示 3.12.15，本机仍固定 3.12.14，实际往返已测，不升级锁环境。
文件路径按 [Windows 命名规则](https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file)
排除设备名/末尾点/控制符等别名，并检查真实 symlink/junction/硬链接。本机实际 junction 与
硬链接负例通过，测试移动的两端先确认位于自己的临时目录中。

新增两个真实 workspace 成员，版本 0.1.0；contracts 只依赖已有 Pydantic 2.14.1，
runtime 只依赖 tool_contracts.api。Import Linter 多根设置由安装的 2.15 源码确认，
7 个合约及独立传递负例覆盖 runtime→工具、contracts→数据库/运行层。
独立 runtime 环境没有安装 WB/NumPy/Qt，安装 wheel 的快照、真实退出回执、提交/重开通过；
WB 另有独立环境，两个环境不共享源码路径。

限制：仍需 Qt 存储队列与进程管理/UI；迁移未实现，未知版本明确拒绝；独立审查未执行。
