# T-007 异步存储子阶段自验

2026-10-14，本机 Windows/Python 3.12.14/uv 0.13.0，分支 feat/T-007-qt-host，base 731cd70。

- `uv lock` / `uv sync --locked --all-groups`：0。仅新增本地 bioimage-app 与现有锁定依赖引用。
- `uv run --locked --no-sync python dev.py check --all`：0；167 tests、Ruff/Pyright strict、9传递合约、4独立wheel。
- 随后补真实退出→异步提交/重开和两条新增合约的负例；最终 `pytest -q`：0，170 passed。
- 最终 `ruff check .`、`ruff format --check .`、`pyright`、`dev.py policy`：均0。
- 隔离 desktop wheel 真实 QCoreApplication 保存/加载/关闭/重开；不导入WB/NumPy。
- Qt 存储屏障期间 GUI QTimer 继续；SQLite 生命周期由专用线程完成；CAS错误保留ID且后续请求成功。

未实现/未测：QProcess宿主、取消/强停/终态仲裁、WB产品窗口、打包/干净机。独立审查与远程CI未运行。
门禁变更扩大 apps/src 扫描和两条传递约束；负例分别注入宿主存储→WB与runtime→desktop，未削弱原有预期。

## 后续进程阶段

- 最终 `uv run --locked --no-sync python dev.py check --all`：0；185 passed，Ruff/format/Pyright strict，9合约，4wheel。
- 15个新案例：真实WB延迟PID许可/真实WB宿主持久化、分片/CRLF/有界stderr、畸形/残帧/超限/无终态、FailedToStart零PID、原生Windows强停孙进程、RunSession成功/取消/启动前取消/异常/启动失败、发布期间取消。
- 独立desktop wheel真实QCoreApplication→QProcess→退出→RunSession提交→关闭重开；无WB/NumPy导入。
- 实际WB源被测试外部修改后仍读工作区快照，解析信号10；运行revision0与新草稿revision1同时保留。
- 新的commit_result可选取消检查只改变宿主取消/终态仲裁；无公式/算法/schema变化，工作区格式v1保持兼容。
- 锁文件只新增app的可选WB成员依赖，无第三方版本升级；未新增/削弱门禁、skip、数值容差或忽略。
- 当前缺项：产品GUI、包态验收/干净机、独立审查及远程CI。T-007宿主自验完成，不代表整个WB软件完成。
