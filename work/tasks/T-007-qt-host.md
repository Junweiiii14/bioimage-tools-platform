# T-007：Qt 宿主的异步存储与进程生命周期

- 状态：review（宿主自验完成，独立审查待办）
- base commit：731cd70
- 上位目标：T-003 持续开发 WB 软件；上轮 T-006 文件/SQLite/恢复自验通过。

## 范围与必读
允许 packages/desktop_sdk、packages/platform_runtime、apps/desktop、tools/wb、tests、tooling、docs、work、.agent-handoff、pyproject.toml、uv.lock、.importlinter、README.md。
根规则、架构/代码规范/模块地图，各已存储模块 README 和 WB worker 契约必读。
真实消费者是 WB worker 解码适配与 Qt 宿主；SDK 只承载窄类型/端口，app 显式装配，不把 WB 数值放入宿主。

## 行为与验收
SQLite/资产 I/O 在专用存储线程，GUI 不同步等待。QProcess 管真实子进程，分帧/解码异步，stdout/stderr 有界。
确认 PID 登记后才提交请求；取消保存状态、合作取消/超时强停与进程树管理；退出与解码结束都确认后才产出宿主候选，旧/重复/取消后结果不成功。
存储回调按请求 ID 路由，失败不暴露 DB 连接或伪造成功；关闭清理不留线程/进程。
用真实 Qt 事件循环验证 worker、取消/崩溃/强停与存储线程；补边界和独立 wheel。

## 未完成范围
WB ROI/曲线/复核产品界面随后接入此宿主，不用虚假按钮宣称已完成。自动候选/归一化/批次与产品安装仍在总目标中。

## 验证与审查
存储子阶段实现：bioimage_app 0.1.0 明确不可变命令/ID、FIFO 预算、后台 Workspace 所有权、异步关闭。
自验已运行：完整门禁 167 测试、9 导入合约、4 wheel；随后增加真实退出→异步提交/重开和两条门禁负例，最终结果见 evidence。
进程子阶段已实现：Qt 后台解码、4MiB帧/8MiB总流/64KiB stderr、真实PID存储门禁、Job Object/进程组强停与退出确认；RunSession 连接取消/提交终态。
实际WB原图快照→进程→存储→重开，旧运行不覆盖新草稿；异常/残帧/超限/强停孙进程/取消发布反例通过。
最终完整门禁185测试、9导入合约、4独立wheel通过。GUI界面进入下一任务；独审未执行，尚未集成main。
