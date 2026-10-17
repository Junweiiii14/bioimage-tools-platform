# 后台QObject退出修复

Windows AMD64/Python3.12.14/PySide6 6.12.0，依赖锁未改。79f9070正式check --all在原20次重复关闭用例挂起；Python栈和自动native采集保存后，补采核对自有pytest PID10408←20632←8264的3条明确TID。自动32线程预算被OpenBLAS占满，补采仅本地临时采集器过滤3条线程，不改正式门禁。两次采集实际exit0；保存证据后只停止专属pytest树，完整check实际exit1，后续wheel未运行。用户工作台未触碰。

main19188等待QBasicMutex→QObject::connectImpl→PySide连接登记；23732在QObject析构+0x4d5→Sbk_GetPyOverride→PyGILState_Ensure；20144在storage.py:122 replied.emit的queued PyObjectWrapper复制等待GIL。与有界人工正负对照/固定6.12源码一起支持对象锁与GIL反转；不是存储磁盘慢，也不能笼统称GC或tracker.senderDestroyed阻塞。其他历史超时是否同因仍UNKNOWN。原始日志.local/t043/check-ci005-final.log及ci005-real-hang-selected-native.log保留本地。

修复AsyncStorage/WBBackground：排空已接工作、最后回执送达后，排队执行worker退休槽；在自身线程将无parent worker移回owner线程，再退出原QThread。GUI保留wait(0)非阻塞确认，deleteLater后由queued destroyed→@Slot确认实际析构，再发布closed。ProcessRunner解码器和ArchiveRestoreJob也有同样finished→worker.deleteLater模式，同步按排空→退休→退出→owner销毁→终态修复，防止相同风险。没有新公共接口、公式/schema/依赖/时限或跳过。

确定性回归用QObject @Slot直接观察实际析构线程，验证closed/finished时C++ worker已失效、QThread停止、最后回执先送达；覆盖失败回复、重复shutdown、进程启动失败及恢复失败不发布目录。首次新测试误import不存在background_models，收集exit2，未作红例；改为公开WBJob后旧实现2项真实失败/3.03秒，均因实际析构在worker线程。初次修复组合1失败/17通过，新测试误漏计storage原有close回执，按既有契约修正为2条（失败请求+close），未变原测试或产品回复。类型首轮8条private访问错误，改为明确测试内省与公开findChild，无ignore；Ruff提示常量getattr后抽为测试内省helper，无全局豁免。

最终组合36passed/42.12秒/exit0：新4项+全部存储、进程、恢复UI、WB桌面（原20循环完整保留）。helper整理后新4项再次exit0，Ruff通过；类型最终、完整门禁和绑定独审结果另记，不能沿用旧659通过。

依据：[Qt QObject moveToThread](https://doc.qt.io/qt-6/qobject.html#moveToThread)，须从对象所属线程push；[Qt6.12 QObject源码](https://raw.githubusercontent.com/qt/qtbase/v6.12.0/src/corelib/kernel/qobject.cpp)，析构持锁调用disconnectNotify；[PySide6.12连接登记](https://raw.githubusercontent.com/pyside/pyside-setup/v6.12.0/sources/pyside6/libpyside/dynamicslot.cpp)。2026-10-17核验。
