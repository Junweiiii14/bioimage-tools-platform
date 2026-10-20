# Windows关闭阶段的定向修正

绑定现场：PR30/cb2c26a，quality39463236311，Windows job118767900369。本机20c完整977/845.63s、原child0与全部wheel/check0，Linuxcb2完整977/395.52s/debugger0/wheel/check0均已通过。Windows只完成前四测试，停在 test_archive_restore_ui.py::test_cancel_or_close_waits_for_restore_thread_and_publishes_nothing[close]，不是运行到新增序列诊断。15分钟限时及随后取消收尾后job20分钟=CANCELLED；没有可确认的pytest成功退出，不以另两平台替代。

job日志API及gh run view均404/not found，实际非0，未篡改状态。GitHub登录浏览器的原有live页面可展开247行原始日志；已保存本地渲染片段与截图（.local/t071-windows-live-fragments.txt、t071-windows-hang-browser.png），片段含重复/非完整下载，不能冒称完整job日志。

Python栈：WB后台background.py:60 retire/moveToThread；存储storage.py:129 replied.emit；GUI test_archive_restore_ui.py:176 waitUntil。native帧分别为GUI QObject析构→Shiboken/GIL等待，存储copyArgValues/PyObjectWrapper→GIL等待，WB moveToThread→QBasicMutex等待。它支持交叉锁等待假设，但没有完整锁地址/持有者证明，不宣称全部native UNKNOWN根因已解决。

最窄修正仅FigureProjectWindow所属端口关闭次序：最终保存完成后先关闭WB；其closed已晚于线程wait(0)成功、GUI deleteLater与worker destroyed，然后才启动storage.shutdown，原双端口closed判定不变。背景提前closed只记状态，不在宿主运行时关闭存储；宿主关闭时直接承接已closed端口，重复close仍用既有幂等机制。无阻塞join、任意全局清扫、数据/算法/依赖/门禁/CI限时改变。

主来源：[Qt QObject](https://doc.qt.io/qt-6/qobject.html#moveToThread)、[Qt Threads and QObjects](https://doc.qt.io/qt-6/threads-qobject.html)说明对象线程归属、所属线程操作与延迟删除约束；原有低层归属/删除策略保持。具体GIL锁交叉是现场推断，而不是文档已经证明本案。

定向控制：新增延迟后台shutdown控制在旧cb2源上实际1（Storage is closing），证明存储先于后台退休；没有伪称确定复现了原生锁死。首次测试误直接导入仅TYPE_CHECKING导出的类型导致收集2，改用既有公开factory后得到上述真实反例。最小顺序版17项/35.40s实际0；补提前closed/正常close边界后四文件23项/66.80s实际0，含三个真实-I诊断。Ruff/格式/Pyright0；B009初次指出测试常量getattr，使用既有私有worker观察helper后0，无忽略/测试门槛削弱。最终需要绑定增量独审、新候选完整门禁与四必需CI。
