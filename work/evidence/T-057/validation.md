# E4/T057 验证（已完成）

base1719a2d，Win11/Python3.12.14/Qt6.12.0，锁未改。
核心首批3 passed/2.42s，定向Pyright与Ruff0；旧E2/E3核心14 passed/4.44s。
覆盖两Fig一缺一完整、同名蛋白不串、schema13/旧读拒绝、实际资产恢复路径重映射、
未claim/取消/变源不发布、完整成图后才可measure、空回复不作done、实际原数组三角
解析积分400/800按源倍数、无信号not_detected、显示lane_unit120→60请求逐字相同。
运行引用在纯应用测试中是显式合成RunRecord/已验证结果，不冒充真实worker或收据。

首轮测试误用measurement.area而现有公开字段是signal，改用真实字段保持解析预期；
旧修订伪造先被ProjectRowAnalysis拒绝，后将伪造改为合法修订但错误极性，以确实
检验冻结请求不一致拒绝。没有放宽答案/容差/skip/门禁。动态列表补显式类型，
未添加类型忽略。宿主/真实worker/界面/完整门禁与最终独审未完成。

## 宿主与界面候选（待最终提交）

- 真实桌面闭环1 passed/8.42s：成图与请求先实际保存，prepare_run读取的冻结JSON中compose done、measure running，两个真实pid worker成功、平坦原图未检测不作零，schema13重开核验同RunRecords与缓存。
- 三种失败/取消与真闭环合计4 passed/12.63s：compose终态CAS失败、measure claim CAS失败、晚到成图取消均不启动测量、不装假产物；单测量取消1 passed/4.78s，首行真实准备后取消并恢复launch，下一来源未启动。
- 核心/桌面/前端联合31 passed/33.68s；最后桌面/前端27 passed/32.89s，真实WebChannel保持layout/results、图块回正确原行、同名蛋白标行序、有效/待复核原始积分分列、固定N与本Fig重试。
- 大图预览2048边限制，原PNG字节不变，保留原source ROI/output_box，单独preview_output_box/preview_source_to_output缩放；四核心3.44s。单独preview_binding绑定当前项目修订/成图资产摘要/输入，不把旧PNG修订改成新原始证据。
- 旧E3重开期望12随显式新schema13升级改为13；旧不支持legacy命令错误文案“尚未接通”改为真实的阶段执行入口，拒绝与无处理断言保留。新大图测试起初误将row_id已单列的manifest ROI预期为也含lane_id；改为显式原坐标四边+独立row_id集合与变换不变量，无放宽几何预期。
- 最后Pyright0、Ruff0；纯核心增量e8e2f96非作者17 passed/3.12s及独立错行顺序/取消/恢复摘要探针0，无P0–P2，不代表宿主已独审。
- 同源浏览器合成预览1280×720，.impeccable/review/t057-browser-{intake,stages,figure,results}.png已逐张打开核验；本地fixture的CPU数值/合成RunRecord仅作视觉，不冒充真实进程/科学真值。真实worker另由上列桌面测试证明。首轮fixture误用reviewed而非ready裁图enum已修正，并按真实ledger使未处理行pending；二轮同视口复验完成。Tab实测从Fig标题到手形平移；切results焦点为结果标题。
- E4 detector仅一次，.local/t057-design-detector.json为[]、0 findings；未重扫。完整门禁及宿主/界面最终独审未完成，E4仍implementing。

## 最终候选 d2cf9b8

- 核心最终5 passed/3.21s（.local/t057-core-final.txt），新增明确横向手动分段保留与未分段逐字相同的原像素请求。不同显示段不改变数值输入。
- 全仓Pyright 0 errors/0 warnings（.local/t057-type-final.txt），Ruff/pre-commit退出0；测试仅在故障注入中用类字典读取原launch，不增加类型忽略或更改门禁。
- 已启动带原生栈与只读Qt退出inventory的完整check --all，日志.local/t057-fullcheck.txt；运行中，尚不能计通过。最终非作者代码审查与限定Windows桌面device class的UI finish审查并行，只读且不并发Qt测试。

## 独审修正 df98166（完整门禁运行中）

- d2cf9b8首轮check因独审发现UI两P2主动Ctrl+C，外层退出1，日志.local/t057-fullcheck.txt；不能计通过，也没有据此认定新原生故障。
- 200项上限改为分页，页码随快照保持、新会话重置、长度减少夹紧；每项仍保留原rowId/槽位状态和值。新增201末槽失败/空值/回源/刷新保页/上一页真实WebChannel断言，8 passed/8.26s，日志.local/t057-review-ui.txt。无预期放宽/时限/skip/类型忽略。
- 回源按钮纵向排列并支持长名换行。浏览器CSS缓存最初保留旧样式，fixture加入当前资源版本后computed style实测flex/column，Fig截图重新保存并打开；没有把缓存旧图当修正通过。
- 新增t057-browser-results-page2.png：201项独立界面容量fixture，无真实运行；第201–201项/第2页/失败原值均空/真实rowId入口可见。明确合成标识，不混作原15槽技术样例或科学证据。
- df98166全量check日志.local/t057-fullcheck-final.txt，仍运行中。绑定代码增量与UI两项复审已关闭，见independent-review.md。detector仍仅一次。

- df98166最终pytest：843 passed/570.37s，原始child exit=0/u32=0x00000000；只读退出inventory仍344/truncated，不等于344泄漏，也不抹去旧purecall UNKNOWN。已进入隔离wheel验证，外层结果尚待。

- 该轮隔离核心wheel失败：新intake_figure适配器顶层导入PIL，未安装figures extra时import wb_tool.api抛ModuleNotFoundError；完整check真实退出1（.local/t057-fullcheck-final.txt），不能记为通过。
- ff89867仅把PIL及渲染/发布适配器导入移至实际调用函数，不新增依赖/extra/改锁或放宽既有无PIL断言。核心5 passed/2.72s（.local/t057-lazy-core.txt）、全Pyright0、Ruff/precommit0。全隔离wheel复验及新提交完整check待完成；独审增量待结论。此前UI结论仅覆盖未改变的UI产物。
- ff89867整套隔离wheel真实退出0（.local/t057-wheels-lazy.txt）：核心无PIL/GUI导入、runtime/事务重开、显示像素/来源/DPI、schema7及模板、项目OCR与显式归一化、桌面widget/入口/异步关闭、真实PP-OCRv6 CPU/worker/PNG均通过。独审增量无阻断。最终完整check正在.local/t057-fullcheck-lazy-final.txt运行。

## 最终通过 ff89867

2026-10-20 Win11/Python3.12.14/Qt6.12.0，锁与门禁未改。
最终dev.py check --all实际退出0（.local/t057-fullcheck-lazy-final.txt）：843 passed/579.73s，原child exit=0/u32=0x00000000，9导入契约/全类型/静态/全部隔离wheel及真实PP-OCRv6 CPU、worker、PNG OCR、桌面异步关闭通过。退出inventory仍344/truncated，旧原生风险不销账。该结果及绑定ff的非作者独审满足E4工程阶段退出；科学留出、干净Win10/DPI和正式发布仍未验收。
