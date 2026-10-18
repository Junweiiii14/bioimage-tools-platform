# T044：退出阶段原生异常证据

2026-10-18，Windows活动树，提交3a830fbcc08f9448cc619c1d4e4283d65e60a981。
正式命令`uv run --locked --no-sync python dev.py check --all`，启用现有自有进程
原生观察器、faulthandler与原子退出码记录，未改测试/时限/依赖。

- Ruff、格式、全项目类型、9条导入契约通过。
- pytest汇总696passed/488.23秒，随后进程真实AV，原child
  `3221225477 / 0xc0000005`；dev/外层实际-1，整轮失败，隔离wheel没有运行。
- 日志`.local/t044/check-anchored.log`，回执`check-anchored.json`绑定上述提交。
- 自有pytest PID21348，故障TID8732，first/second-chance同地址；采集时只剩1线程，
  无Python帧。不能把汇总passed解释为完整检查成功。

主要模块/偏移路径：`pyside6.abi3.dll+0x1c91e`，最近符号
`PySide::SignalManager::retrieveMetaObject+0xaa`；继而Qt元调用、
`QObject::destroyed`、`QWidget::~QWidget`、Shiboken包装器销毁、
`QFormLayout`析构及父对象`deleteChildren`。
这些是DbgHelp最近符号，不是已匹配PDB的精确源码位置；不能凭大偏移的
`PySidePropertyPrivate::getValue`/`qt_static_metacall`等名字断言实际发生某属性读取。

与先前跨线程锁/GIL挂起不同，本轮支持“退出阶段Qt父子/包装器析构路径异常”这一范围。
具体控件、所有权/连接与析构次序尚UNKNOWN；未证明WebEngine profile残留或全部历史
故障同因，不据此盲目改清理、升级依赖、提前os._exit或放宽检查。

授权只读审查者独立核对原码/日志与退出码，建议先做四个独立小型对照：
普通Qt控件/纯Python子类，分别自然退出/显式先销毁父对象。均只含QApplication、
QWidget、QFormLayout和少量输入控件，不引入WebEngine、worker或产品，保留真实退出。
若均未复现，下次必要的完整检查可只记录退出前存活顶层对象类型与父子关系；不新增
destroyed Python回调，不额外清理来掩盖异常。该组实验尚未运行。

同版本主要源码（2026-10-18访问，仅机制线索）：
[SignalManager](https://raw.githubusercontent.com/pyside/pyside-setup/v6.12.0/sources/pyside6/libpyside/signalmanager.cpp)、
[PySide退出清理](https://raw.githubusercontent.com/pyside/pyside-setup/v6.12.0/sources/pyside6/libpyside/pyside.cpp)。
动态元对象读取会涉及包装器/类型数据，退出清理涉及Python拥有的QObject与QApplication；
这些源码描述不足以证明本机故障位置或所有权错误，仍需最小复现和匹配二进制证据。
