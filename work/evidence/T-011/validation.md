# T-011 诊断子阶段验证

2026-10-14 Windows/Python3.12.14/Qt6.12.0，base12cac86，fix/T-011-qt-lifecycle。旧原生中止尚未复现或定位，本记录不是修复证明。

- 原代码桌面9例加QThread命名/create-start-finish-destroy、pytest阶段记录，GC阈值80且-s一次通过（11.65秒）；启用原pytest捕获+Qt消息转存，阈值700/80/5各9通过（11.10/相应过程日志/11.43秒）。共36例、每个独立进程退出0。仪器/私人图片未参与。探针与日志.local/requirements-review/qt_diagnostic.py及qt-lifecycle-trace*.log。
- 新DesktopDiagnostics：三个独立子进程正常/未捕获Python异常回调/实际Qt qFatal通过。初版假定qFatal一定触发Python fatal handler，测试反证未出现信号栈；补QtFatalMsg内显式dump_traceback后验证退出前消息/当前线程栈。没有削弱非零退出或堆栈预期，改为实际Qt错误路径的栈断言。
- 完整`uv run --locked --no-sync python dev.py check --all`退出0：218测试（62.88秒）、161文件Ruff格式、Pyright strict零错、9导入合约、4wheel/5隔离安装场景。安装GUI场景验证诊断文件正常结束，原wb/wb_ocr worker仍实际通过。
- uv.lock只更新本地bioimage-app0.3.0→0.3.1；第三方库不变。文档v1/v2、积分及OCR算法不变；未加skip/xfail/类型忽略。初次完整检查在Ruff SIM105风格处停止，改contextlib.suppress等价写法后运行上述完整检查。
- 根因UNKNOWN；没有独立审查/远程CI/最终包态与用户验收。跨会话日志保留策略后续整理，不删除历史用户数据。worker入口在诊断初始化前分派，stdout协议不混入日志。
