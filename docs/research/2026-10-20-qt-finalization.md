# E2全量测试退出异常调查

问题：b4b519f全部822断言通过后，pytest在解释器终结时0xc0000409。
验收必须包括真实进程退出，不能以断言汇总代替完整门禁。

## 证据与来源

- 本机Win11/Python3.12.14/PySide6.12.0；原始日志.local/t055-fullcheck.txt。
  主线程abort/purecall/QObject析构/QtWidgets.pyd/PySide destroyQCoreApplication/
  visitAllPyObjects/Py_FinalizeEx。具体对象类型与根因UNKNOWN。
- [固定PySide6.12.0源码pyside.cpp](https://raw.githubusercontent.com/pyside/pyside-setup/v6.12.0/sources/pyside6/libpyside/pyside.cpp)
  的destructionVisitor/destroyQCoreApplication：先遍历有效且Python拥有的QObject包装器，
  调用C++析构，再删除app。与当前栈位置相容，但不证明哪个对象导致异常。
- [QWebEnginePage官方生命周期契约](https://doc.qt.io/qtforpython-6/PySide6/QtWebEngineCore/QWebEnginePage.html)
  要求调用者保证非默认profile在page存活期间有效。不能为清理方便提前删除profile。
- 来源访问2026-10-20；动态网页不是固定6.12源码替代物。

## 最小实验与候选

定向desktop/frontend17项加现有只读inventory退出0，18.74s，root_count0。
这只说明该次顶层QWidget清单为空，不覆盖parentless QObject或全量时序。

非作者指出helper只等window失效，page销毁后才安排app所属profile.deleteLater，
以及reopen前后两代host需分别观察。以上是待测假设，不是已确认因果。
下一步先完成带已有inventory的全量诊断，再串行观察明确所属window/host/view/page/
profile的原生有效性和真实退出码。只记录类型、指针和有效性，不读取科研内容。

不采用全局delete、gc清扫、改成功状态或依赖升级；没有对象来源证据不猜测性修复。
若相同失败复现，必须用新增观测缩小来源后再决定修复，不无限重复全量检查。

## 本轮实验结果

同一产品诊断全量822/566.49s、真实child0及全部wheel/check0。退出前清单root_count344，
存在来源可追的旧无父view/OCR面板；清单截断，有父popup也计入roots，不能把总数当泄漏。
后续E6按明确所属测试完善销毁等待并复验，当前不推断其为原生异常根因。

E2 prepare/save/reopen/close所属对象探针1/9.68s退出0；helper返回时window、两代host/view、
page/profile均原生失效，fixture settings仍有效。此轮profile残留假设未复现。
观察保留包装器会影响引用时序，不能外推完整稳定性；详细真实失败和复验见T055 validation。
