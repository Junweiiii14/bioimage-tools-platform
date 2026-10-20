# PR24 CI分段选择修复

Windows/Python3.12.14，锁定依赖；原head5019b928bcadfa6dfe4ed4bb1d297e32504ff90f。

GitHub Actions quality39416542187：Linux job118606842117，938通过/1失败388.39s、调试器实际1；Windows job118606842442，938通过/1失败574.55s、child实际1/u32=1。两者均在原test_compact_layout_edits_and_advanced_table_share_geometry，r1预期[(1,1),(2,3)]、实际[(1,3)]，均未到隔离wheel。desktop/rules成功不代替foundation。原始日志保留于忽略的.local/t066-pr24-{linux,windows}-failure.log。

作者以新增9项快捷键→原compact单项顺序复现9通过/1失败8.14s、实际1；独审冻结同顺序9通过/1失败8.01s、实际1。独审进一步收窄单个test_real_key_saves_group_draft_once_through_the_button_action前驱→原compact：1通过/1失败2.93s、实际1。观察到Qt全局Ctrl+Shift修饰状态，setCurrentCell后selectedRows=[1]、随后的selectRow后为空，current仍[1,0]；split_selected明确提示未选行。远端无modifier快照，不能把本地确证触发链当远端内部状态的直接观测。

独审只在诊断进程临时替换为setCurrentCell(index,0,ClearAndSelect|Rows)，相同前驱、修饰状态和原几何预期2通过/2.57s、实际0；selectionChanged另一次观察1通过/1失败3.31s、实际1，证明依次选中/取消。诊断脚本和日志在.local/t066-pr24-selection-review，未修改冻结产品或测试。

作者采用这一窄产品修复：紧凑单项选择明确ClearAndSelect|Rows，取消第二次selectRow。高级表格ExtendedSelection、分段几何、原数据、测试预期/容差/超时、依赖及门禁均无改动。原快捷键与compact/laboratory_layout整文件顺序回归28通过/7.91s、进程实际0。Qt shared-image诊断仍保留，不将本次成功外推其他native UNKNOWN。定向Ruff/格式通过；静态与冻结独审另记。

官方Qt选择API参考：https://doc.qt.io/qt-6/qitemselectionmodel.html ，固定Qt6.12.0的QTableView源码：https://raw.githubusercontent.com/qt/qtbase/v6.12.0/src/widgets/itemviews/qtableview.cpp 。来源用于解释选择API，本地对照实验承担修复证据。
