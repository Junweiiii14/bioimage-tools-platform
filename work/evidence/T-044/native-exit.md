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
destroyed Python回调，不额外清理来掩盖异常。后继实际控制结果见下节。

同版本主要源码（2026-10-18访问，仅机制线索）：
[SignalManager](https://raw.githubusercontent.com/pyside/pyside-setup/v6.12.0/sources/pyside6/libpyside/signalmanager.cpp)、
[PySide退出清理](https://raw.githubusercontent.com/pyside/pyside-setup/v6.12.0/sources/pyside6/libpyside/pyside.cpp)。
动态元对象读取会涉及包装器/类型数据，退出清理涉及Python拥有的QObject与QApplication；
这些源码描述不足以证明本机故障位置或所有权错误，仍需最小复现和匹配二进制证据。

## 四组基础控制与后继观察

9f96f5c下四个独立自有进程，PySide/Qt均6.12.0，原生观察器均确认附着：

| 对照 | 原退出码 | 原生异常 |
|---|---|---|
| 普通Qt控件、自然退出 | 0 | 未观察到 |
| 普通Qt控件、先销毁父对象 | 0 | 未观察到 |
| Python控件子类、自然退出 | 0 | 未观察到 |
| Python控件子类、先销毁父对象 | 0 | 未观察到 |

仅包含QApplication/QWidget/QFormLayout/少量输入框，不导入产品、WebEngine或worker。
自然退出组将包装器与类型保留至解释器清理；显式组使用DeferredDelete事件核实父对象
确已销毁。不是产品清理变更。四例未复现不能宣称根因修复。
本机receipt `.local/t044/qt-exit-controls/receipt.json`，原型脚本SHA256
`4a43f7a683bb73599edf5046a711e6e1bc980131c7c7f0540770cdaa71c3af0a`。

新增显式启用的pytest观察插件`tooling.qt_exit_inventory`，只在Qt测试之后用弱引用
记下顶层对象首次观察所在测试（去掉参数值），最终记录有界类型/对象标识/父子关系。
不读取窗口标题、控件文本、objectName或图像；不新增destroyed回调，不发送事件、
gc、删除或关闭对象，不修改测试退出状态。默认不启用，不改CI/依赖/原测试/时限。
最多128顶层/256对象（可校验预算至512）、1024弱引用来源，截断/无法读取明确记录。
这是输出/遍历预算；Qt的topLevelWidgets/children先取得完整列表，不是严格的瞬时内存上限。
读取API会临时建立包装器引用，不能声称完全不影响最终析构时序。

作者两项实际0：验证对象层级、隐私字段不输出、对象仍存活和预算截断，相关类型/
Ruff/格式0。下次有必要的最终完整检查显式加`-p tooling.qt_exit_inventory`并保留
已有原生观察器和原始子退出码；该观察插件不是崩溃修复，最终完整检查仍待执行。

694279f绑定独审2项0.38秒实际0，无隐藏产品失败/主动清理问题；建议补teardown观察
异常容错。后继增加仅记录异常类型的防护，不把诊断读取错误转成原测试teardown失败，
也不读取异常文本。故障注入旧实现1failed/0.58秒实际1，新实现3passed/0.45秒实际0；
相关类型/Ruff/格式0，未放宽断言/门禁。当前仍未修复退出根因。

## efec471 完整观察及测试隔离修正

显式启用清单和原生观察器的完整检查实际结束：700 passed、1 failed，488.11秒；
原child与外层均1，隔离wheel未运行。本轮未观察到原生异常，不能关闭间歇退出风险。
日志与绑定回执为本机`.local/t044/check-exit-inventory.{log,json}`。

失败位于诊断单元测试的root/child身份断言：测试时Qt全局根计数4208，清单明确截断，
新测试对象未必进入前128根/256节点。最终全局计数5448、输出截断；其中包含有父对象
的Qt弹出部件，不能把数字直接解释为5448个产品窗口或已证实泄漏。
first_observed_after仅首次观察来源，也不是对象创建位置。

修正仅隔离诊断单元测试的根集合与来源表，使用本用例真实Qt对象；没有删除前序产品
对象、提高预算或放宽原身份/内容隐私断言。新增多根节点预算、129根截断、来源容量
及unattributed对照。作者5项0.46秒实际0、相关Pyright/Ruff/格式0；初轮格式/私有字段
类型错误已修，未加忽略。插件运行行为未改，完整全局清单仍由最终钩子记录。
后继提交绑定独审与完整检查待执行；下一原生定位应对照实际产品View生命周期，
不通过测试清理全部对象来假装修复产品退出。

## 实际View的所有权缺口与修正

662d767绑定独审5项0.37秒实际0，确认诊断单测patch在全局观察钩子前恢复，未隐藏
全局清单。该审查还指出隐藏控件缺少parent/布局归属；保留对象兼容比贸然删除稳妥。

两个自有实际View进程使用公开`create_figure_project_view(parent)`，不创建后台或
WebEngine，均附着原生观察器，natural/显式parent销毁实际0、无AV。显式组确认
parent和view已无效，但Qt根数41→11；单独空View诊断逐个确认残留均无parent，包含
历史提示、隐藏导入/导出/导航控件以及定量面板的隐藏提示/原图画布。
本机receipt `.local/t044/figure-view-exit-controls/receipt.json`，脚本SHA256
`255001f1afbbafd30efe97a2f841158ca6d9519d2ae5dd84d60e5f41e9706af6`；逐项记录
`figure-view-residual-roots.json`只含静态属性名/类型/parent状态，不含用户文本。

修正将这些保留控件和隐藏预览说明明确归属View/预览页；未入布局的source_heading
明确hide，保持原来不展示的行为。数值/数据格式/原图/窗口关闭协议不变，没有全局
delete/GC、强制退出或修改测试清理来掩盖问题。未用静态未引用作为删除兼容接口理由。

新增独立进程回归先确认parent/view真实销毁，再要求本次全部Qt根包装器失效，并
检查原进程退出码；旧实现1failed/2.27秒，残留11；新实现与诊断5项合计6passed/
2.21秒、实际0。最初在pytest共享Qt会话直接flush DeferredDelete的试验出现失败及
caplog stash teardown KeyError，日志view-ownership-red.log保留；因此改用隔离进程
观察，未忽略异常或减弱预期。相关工作流/保存重开/定量重算12项18.09秒实际0，
相关Pyright/Ruff/格式0。后继绑定独审/完整检查待执行。

这是可复现的对象归属缺口修复，尚不能证明历史retrieveMetaObject AV根因已解决。
