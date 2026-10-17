# 隐藏宿主生命周期验证

离屏最小实验在关闭后台后销毁工作台：修复前`host.parent() is None`，owner的C++对象失效但host仍有效；修复后宿主Qt父对象为工作台，两者C++对象均失效。日志在`.local/t043/web-host-ownership-{before,after}.log`，均退出0。

新增回归先在旧实现稳定失败：`test_destroyed_workbench_releases_its_hidden_native_host`明确断言宿主仍有效，1failed/2.90s/exit1。首版测试重复交给qtbot清理已显式销毁的窗口造成额外teardown错误，已改为测试自己负责显式销毁；最终红例没有此错误，未更改产品断言。首次组合命令误写不存在的测试文件，exit4且0测试，不作验证通过。

修复仅给隐藏宿主设置Qt父对象并保留Window标志；现有关闭失败不切旧宿主、后台关闭完成后才接受关闭的逻辑保持。入口/网页桥接/平台组合23passed/17.15s/exit0，包含同步/异步拒绝关闭、真实C++销毁及高级窗口属性。Ruff/format退出0，Pyright 0errors/exit0。未更改任何超时、skip、容差或科学预期。

另一个手动close/显式delete的GC探针均退出0，没有复现挂起。不能由对象残留推断出特定GC死锁；本项修复确定的宿主所有权缺陷，远端15分钟挂起根因仍需诊断栈。

来源：[Qt QWidget关闭语义](https://doc.qt.io/qt-6/qwidget.html#close)、[pytest-qt清理接口](https://pytest-qt.readthedocs.io/en/latest/reference.html#pytestqt.qtbot.QtBot.addWidget)。使用本机pytest-qt实际源码核对其会对注册窗口close并deleteLater，因此显式销毁生命周期用例自行清理，不重复注册已销毁对象。未修改第三方依赖。


绑定提交5decc73..b4bc8ba只读独审无阻断；审查者独立执行实际销毁及同步/异步拒绝关闭3项，退出0。作者随后用8原图经正常工作台宿主导入、自动处理、保存和重开验证，8个run成功、原图SHA不变、参考未读取、重开内容相等，退出0；输出.local/t043/workbench-ci003/validation.json。此次离屏WebEngine截图为空白，伴随GPU context lost信息，不能作视觉验收；只记录功能链验证，不以截图宣告UI已验收。旧输出保持原位。
`n完整产品b4bc8ba随后正式check --all实际退出0：658passed/497.50秒，静态、边界及全部隔离wheel/真实OCR均完成，日志.local/t043/check-ci003-final.log。之后CI004新增诊断另跑最终门禁，不把本轮旧结果充作其验证。
