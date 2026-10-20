# E2/T055 验证

开始2026-10-19，持续至2026-10-20；base19a11fb，Win11/Python3.12.14/Qt6.12.0，锁不变。

- 新schema11保存确认清单与版本化阶段账本；旧1–10读取和schema10无处理结果语义保留。账本不是定量成功收据；阶段状态不生成ROI/run/数值。
- 首轮核心/既有清单/派生计划/真实桌面组合36项10.94s退出0；新增取消、编辑、保存失败后桌面10项14.86s退出0；纯阶段6项2.25s退出0；前端6项10.64s退出0。最终提交完整门禁/wheel及非作者独审待执行。
- 阶段测试覆盖两个独立Fig、局部失败、完整Fig才可量化、旧票据/重复完成拒绝、取消确认、中断恢复、重试、归档来源重映射；桌面后台准备/CAS保存重开、返回编辑与失败不安装。
- Ruff/format、定向及模块Pyright、Node语法已检查；初轮新增样式/类型问题按工具修正，没有忽略或放宽原断言。无依赖升级/科学默认值/平台格式/门禁规则修改。
- 截图首次用离屏QWebEngineView.grab为空白，已判无效，不作为视觉通过；移除只验证能写出空白PNG的机械测试。语义/交互断言保留。
- 改用同源实际web_ui文件副本的本地浏览器合成预览：127.0.0.1:63894；只检查视觉，不执行科学计算。有效1280×720顶部及滚动后阶段截图见.impeccable/review/t055-browser-top.png和t055-browser-stages.png。没有960/mobile视觉通过结论。真实Qt保存/重开由独立相关测试证明，不用浏览器替代。
- Impeccable context已读；surface-brief read路径选择返回候选/退出1，随后直接读明确web-workbench surface。保留既有视觉系统，不修复预存PRODUCT默认入口描述漂移。detector一次退出0：12项均advisory（9字号、1圆角、2颜色），旧T051样式及新增沿用12/16字号；未改DESIGN tokens。独立视觉审查待执行。

## 独审修复 b4b519f

3项代码P2及1项界面P2已修复并非作者复审关闭，见independent-review.md。
作者最终定向：核心8 passed/2.13s；真实desktop+frontend 17 passed/15.42s；
Pyright0错误、Ruff/Node语法0。包含真实CAS在途取消与后续保存新修订、
busy/失败焦点恢复、保存后摘要/返回编辑聚焦与live文本断言。
没有新增类型忽略/skip/xfail/容差或放宽门禁；首次测试误导入未公开DraftSnapshot
导致收集失败，改为测试端口object返回注解，未扩展平台API。
原输入反例首次reviewed=True但未设ROI被既有行验证先拒绝；补有效ROI后验证输入摘要拒绝。
最终完整check --all正在执行，原始日志.local/t055-fullcheck.txt，未结束不计通过。

首次完整门禁失败：822 passed/543.27s后pytest退出阶段原生0xc0000409，
observed child3221226505/u32=0xc0000409，外层-1；wheel未执行。
故障栈主线程abort→purecall→QObject析构→PySide::destroyQCoreApplication→Py_FinalizeEx。
不能由822断言通过宣布完整门禁成功。下一诊断使用仓库已有只读qt_exit_inventory
记录残存Qt对象的首次测试来源，不添加全局删除/GC补丁，不修改退出状态。

诊断复验同一产品b4b519f，未改产品/测试/门禁，新增`-p tooling.qt_exit_inventory`
只读观测：完整check --all最终退出0；822 passed/566.49s，Observed child0/u32=0；
9导入契约和全部隔离wheel（真实离线OCR/worker/PNG、桌面异步关闭）通过。
日志.local/t055-fullcheck-inventory.txt。保留GPU context/font警告及首次原生失败；
不以该次正常退出宣布purecall根因已修复。

全量清单root_count344、truncated=true；可见无父FigureProjectView/OCR面板分别首次
观察于既有ratio_crop_view、crop_return_selection、contextual_panels_ui、standard_display_ui
等测试。大量QFrame为有父popup，不把总数等同泄漏数。来源线索转E6生命周期优化，
不能对所有Qt对象全局删除，也不能据清单直接归因purecall。

串行临时只读所属对象探针，原E2 prepare/save/reopen/close真实测试1 passed/9.68s退出0；
helper返回时initial host/view、reopen前host/view、current window/host/view、page/profile
均原生失效，fixture QSettings仍有效。未复现profile延迟残留；不据候选假设改关闭逻辑。
日志.local/t055-owned-lifetime.txt。临时观察器不处理事件、不执行删除/GC，保留对象包装器
只为观察isValid；这会影响引用时序，非无扰动证明。后续发布仍需复验原生稳定性。
