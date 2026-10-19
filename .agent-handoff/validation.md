# Validation History

- 2026-10-16 T033/a68000e：全门禁568 passed/224.97s退出0，最终9专项退出0，独审另5项退出0；wheel含web资源；真实10原图SHA不变。网页1440/390、角点/拖画/减少动效实际操作；详见任务与.local/t033。


## 2026-10-14 / T-009暂停前增量检查（未提交工作树）
- worker+桌面联合：38 passed/1 failed；旧测试用v1专用读取器读v2失败，已改公开read_wb_document。
- 修正后旧桌面6 passed；新增真实OCR桌面→自动写表→XLSX→保存重开→ROI失效单测1 passed。
- 新测试前Pyright零错误。新测试初版Optional/不存在属性9错已修正；最新代码未复跑类型/全量门禁。OCR协议schema/取消反例、隔离wheel及独审未执行。无skip/xfail/容差放宽。

2026-10-14 T-002：最终本地 35 passed（27.22s），Ruff/Pyright strict 通过；standalone 与 ZIP 哈希通过；包态基准 exit 0，20 图整批中位数 21.819s、worker RSS 峰值 257.855MiB。源码原生 UI 通过；包态 UI 因用户 Esc 停止而未验收，不能推断通过。完整证据在 work/evidence/T-002/validation.md。

T-002 进行中：本轮基线 `dev.py check --all` 29 passed；新增协议/原值/真实进程反例后 Ruff、Pyright strict、35 pytest 全部通过（23.74s）。源码基准已执行，standalone 与真实窗口尚未通过；最终结论以 T-002 证据为准。

| Date | Command/Check | Result | Notes |
| --- | --- | --- | --- |
| 2026-10-13 | Codex updater / login / CLI features | passed | 更新渠道 up_to_date，实际能力与未测能力见环境报告 |
| 2026-10-13 | uv lock / sync --locked --all-groups | passed | Python 3.12.14，67 个依赖安装 |
| 2026-10-13 | dev.py check --all | passed | Ruff、Pyright strict、14 pytest；无产品源码 |
| 2026-10-13 | dev.py smoke-env | passed | Qt offscreen、QProcess、中文 TIFF 原值往返 |
| 2026-10-13 | pip-audit --local | passed | 67 个包，未发现已知漏洞 |
| 2026-10-13 | Skills frontmatter / script AST / digest | passed | 5 技能，2 脚本语法，非业务端到端验证 |
| 2026-10-13 | GitHub rulesets | blocked | 私有仓库套餐限制 403 |
| 2026-10-13 | 产品/打包/科学样本/独立审查 | not run | 当前只治理与环境，产品任务未启动 |

| 2026-10-13 | Nuitka / GCC compiler probe | passed | 专用短缓存路径、生成启动器；不等于 Qt standalone |
| 2026-10-13 | GitHub CI at fdf9a61 | passed | Windows/Linux foundation 与 desktop-environment 三项 |
| 2026-10-13 | 官方 GitHub skills 只读脚本 | passed | PR #1 检查与审查线程读取成功 |
| 2026-10-13 | F-002 rule loader / Ruff / Pyright / pytest | passed | 29 个测试；包含遗漏、过期、范围扩大、路径与中文编码反例 |
| 2026-10-13 | Public visibility / ruleset 25008972 | passed | 用户授权公开；active，四项指定 Actions 检查，无 bypass；替代初次私有套餐阻碍 |
| 2026-10-13 | 规则回执独立负例与正例 | passed | 03afb43：其余检查成功，仅回执失败仍 BLOCKED；5eb1e8b：四项全部通过 |

| 2026-10-14 | T-003 dev.py check --all | passed | 61 测试，Ruff/Pyright strict、2 import-linter、隔离 wheel；GUI/检测未实现 |

| 2026-10-14 | T-003 输入阶段 dev.py check --all / 真实输入探针 | passed | 77 测试、3 合约、隔离 wheel；5 张 TIFF 只读加载，真实检测/GUI 未测 |

| 2026-10-14 | T-004 dev.py check --all | passed | 90 测试、4 import-linter、隔离 wheel TIFF→手工分析；不代表 worker/UI/存储完成 |

| 2026-10-14 | T-005 dev.py check --all | passed | 123 测试、4 合约、schema 漂移、隔离 wheel 真实 worker；GUI/强停/存储未测 |

| 2026-10-14 | T-006 dev.py check --all | passed | 164 测试、7 合约、3 wheel；38 工作区案例含真实硬退出/Windows别名/备份；UI未测 |

| 2026-10-14 | T-007 存储子阶段 check --all + 最终 pytest/Pyright/Ruff/policy | passed | 初次167，补用例后170测试；9合约/4wheel；实际Qt队列与退出提交；QProcess/UI未实现，独审未执行 |

| 2026-10-14 | T-007 进程阶段 dev.py check --all | passed | 185tests/9合约/4wheel；真实Qt进程、Windows孙进程强停、WB存储重开/旧revision、取消发布；GUI/独审/远程CI未完成 |

| 2026-10-14 | T-008 dev.py check --all / Qt交互追加验证 | passed | 190全量、9合约、4wheel5安装场景；真实手工GUI信号10保存重开/关闭保存/uint16/取消关闭；最终pytest见T008证据；OCR/独审/包态未完成 |

| 2026-10-14 | T-009后端 dev.py check --all / 独立XLSX reader | passed | 199tests/9合约/4wheel5场景；真实PP-OCRv6禁网6标签/空间关联/3045和1995写表/无覆盖，bundled openpyxl3.1.5读Unicode与值；GUI/worker仍待接入 |

## 2026-10-14 / T-009 完整桌面闭环
- Windows/Python3.12.14，wb-tool0.7.0/bioimage-app0.2.0；`dev.py check --all`退出0，205测试（59.00s）、9导入合约、4wheel/5安装场景，含安装产物真实OCR worker。
- 新增实际OCR先于ROI、独立拼图/原图、人工绑定、无效名称、实时写值、保存重开和过期清值；strict协议/取消/模型摘要/schema/旧v1兼容通过。积分数值预期、容差/skip/xfail未放宽。
- 新资料只读实测发现短编号和高置信误读；布局@2支持短编号及并排重复标签，私人数据留.local；不是准确率验收。
- 最后修正表格重绘选中位置被循环索引覆盖，并补桌面断言；随后定向桌面测试与静态检查通过（结果以最新命令记录为准）。
- 锁文件只更新两个本地包版本。独审/远程CI/最终包态未运行；物理FAT未测，Windows已使用无覆盖rename。

## 2026-10-14 / T-010
完整`dev.py check --all`退出0：215测试（60.92秒）、Ruff/Pyright、9导入合约、4wheel5场景。新网格/原像素裁剪9数值与格式用例，桌面9用例（含真实拖框/保存重开/异步导出），隔离wheel调用新API通过。初版测试漏load_document已修正；组合测试后一次Qt原生Aborted仍未确定根因，后续通过不代表修复。详细证据work/evidence/T-010/validation.md。独审/远程CI/完整产品打包未运行。

## 2026-10-14 / T-011诊断子阶段
`dev.py check --all`退出0：218测试（62.88秒）、Ruff/Pyright、9合约、4wheel5场景。原代码4轮36桌面压力未复现旧中止；新诊断3独立子进程正常/异常/qFatal落盘通过。首个qFatal用例证实不能只依赖Python信号handler，修正为QtFatalMsg主动dump后通过；未把日志功能记成根因修复。详见work/evidence/T-011/validation.md。

## 2026-10-14 / T-012
`dev.py check --all`退出0：230测试（63.06s）、Ruff170文件、Pyright0、9合约、4wheel5场景。12新用例验证多图Qt闭环/模板复用、原像素/来源/复核/取消。另真实用户10张TIFF批量导入/重开与外部源SHA保持通过。详情work/evidence/T-012/validation.md。旧Qt原生中止未复现且仍未定位；独审/远程CI/完整产品包未运行。

## 2026-10-14 / T-013
`dev.py check --all`最终退出0：244测试（65.02s）、Ruff182文件、Pyright0、9合约、4wheel5场景。新增14用例验证候选/固定空位/弱带/边缘/多膜、v1/v2快照/来源、真实Qt应用恢复/聚焦坐标/失败继续/取消关闭/过期拒绝。真实10图建议快照保存重开、外部SHA保持通过；真实行均未审核/应用。初次完整运行类型失败修正后通过，未减门禁；旧Qt中止未复现也未定位。详情work/evidence/T-013/validation.md；独审/CI/最终包态未运行。

## 2026-10-14 / T-014 多源定量第一阶段
产品提交79a675a，最终dev.py check --all退出0：262测试（72.36s）、Ruff191文件、Pyright0、9合约、4wheel/5隔离场景。新增13核心+5真实Qt用例；包括原图双源积分/基线、重开/自动表/XLSX、取消保留已完成行、坏结果/外来run隔离、旧修订拒绝与刷新保留编辑。此前严格模型重建失败与损坏结果整批阻断已修复，首轮全量后发现的刷新丢标注问题亦修复并重跑门禁。无容差/忽略/skip放宽；详情work/evidence/T-014/validation.md。Qt旧中止未复现也未定位；独审、远程CI、最终包态和用户验收未运行。

## 2026-10-14 / T-014 项目OCR关联
产品05e5d56，最终dev.py check --all退出0：268测试79.48秒、Ruff198文件、Pyright0、9合约、4wheel/5隔离场景。新增2核心+4桌面用例，验证实际OCR进程、重复标签显式绑定、自动值/字面XLSX、取消旧关联保留、重开损坏隔离、运行/导入期间编辑拒绝后到覆盖、审核候选同步。实际用户组合图只读流程15token/11未确认行，原SHA保持、保存重开一致；源码Qt截图已查看。锁文件仅本地版本变更，无门禁/容差弱化；独审、远程CI、最终包态和真实准确率未验收。证据work/evidence/T-014/ocr-validation.md。

## 2026-10-14 / T-015 项目归一化
产品0cd390b，dev.py check --all退出0：284测试85.27秒、Ruff207文件、Pyright0、9合约、4wheel/5隔离场景。新增11领域/4应用/1桌面用例并扩展OCR桌面流程；明确配对、手算q/m/f、异常/零/极端浮点、坏对照不丢、v5无OCR/保留OCR、真实进程/重开/过期/字面导出通过。Qt截图已查看。中间类型检查问题已修正，无容差/ignore/门禁削弱；锁文件仅本地包版本。独审/远程CI/最终包态/实际实验验收未运行，旧Qt中止根因仍UNKNOWN。详情work/evidence/T-015/validation.md。

## 2026-10-14 / T-016 PNG与完整成图识别
产品1d5ae2a，dev.py check --all退出0：304测试103.49秒、Ruff213文件、Pyright0、9合约、4wheel/5隔离场景。PNG已知像素/透明/16位灰度/CRC/动画/方向/预算、真实worker、完整大图Qt/配对归一化保持/重开/取消/关闭/晚到保存/错误保留及单图PNG通过。第一次大图测试版式非法未放宽模板校验，trace定位提示覆盖并修复；详见work/evidence/T-016/validation.md。真实组合PNG副本1347×902、15token/11未确认行，显示像素与TIFF路径相等、原SHA保持、重开一致；70.86秒是全流程而非OCR基准。源码Qt截图已看；独审/CI/最终包态与准确率未验收。

## 2026-10-14 / T-017 批量元信息
产品9ea4089，最终dev.py check --all退出0：335测试110.95秒、Ruff224文件、Pyright0、9合约、4wheel5场景；新增31测试，数值/旧预期无削弱。首次完整1失败332通过，关闭导入回退已按旧行为修复、13桌面组合通过；第二次完整约72项后停滞并停止，后续145诊断98.74秒通过且无栈，根因UNKNOWN。测试同步清理强化不代表根因已修。真实Excel50×49/190公式、47未绑定提议/0应用、2原图缩略图、源SHA/重开保持，Qt截图已看。详情work/evidence/T-017/validation.md；独审/真实映射/最终产品验收未完成。

## 2026-10-14 / T-018 结果CSV与统一归档
产品c5f5787，最终dev.py check --all退出0：364测试113.15秒、Ruff235文件、Pyright0、9合约、4wheel/5隔离场景；新增25核心/4Qt并扩展完整PNG OCR真实运行归档。35定向2.07秒、27桌面/项目41.93秒。首次全门禁363通过115.73秒，复查将索引计入成员/总字节预算并加反例后完整重验。原4000/真0/缺失、原像素/字节/SHA、损坏隔离、冻结修订、CSV/OOXML一致和取消/关闭/代际/无覆盖通过。新夹具8失败已修正API/字段用法，未放宽旧预期；锁文件只改本地版本。旧Qt/停滞根因仍UNKNOWN。详情work/evidence/T-018/validation.md；独审/外部表格兼容/真实科学与最终Windows验收未完成。

## 2026-10-14 / T-019 ZIP恢复（产品6a06369）
最终dev.py check --all退出0：398测试124.27秒、Ruff244文件、Pyright0、9合约、4wheel/5隔离场景，新增34项。先前396全量128.27秒通过，补成员标志反例后完整重验；70核心/Qt/存储17.92秒通过。4000/空/0/8000/16000/0、OCR绑定、归一化表、编辑失效/真实复算2500、0条外来本机run/复算仅1条真实本机run、二次2来源4历史通过。8/16位/RGB/MINISWHITE、旧格式/坏数据/预算/无覆盖/取消/关闭/发布失败和发布后关闭均有反例。源码Qt截图已看；未新增真实科学准确率、外部Excel/FAT/非Windows/断电/大项目性能，独审及最终产品验收待办。首轮门禁仅Ruff行长失败已修，原预期/容差/skip无削弱，锁仅3个本地包版本。详情work/evidence/T-019/validation.md。

## 2026-10-14 / T-020 TIFF/PNG直接成图
最终dev.py check --all退出0：425测试143.71秒、Ruff251文件、Pyright0、9合约、4wheel/4个隔离环境；新增27测试。专项28核心/原有1.21秒、9Qt17.48秒。完整像素/来源/DPI/自有暂存核验、取消/关闭/晚到保存/编辑/无覆盖/已发布保持、已知显示图量化拒绝/真实OCR显式回填4000与归一化0.5及重开通过。真实组合图全幅格式包装1577×988，原1347×902显示像素/原SHA保持；17token/0确认/0绑定，非科学验收。私有输出与Qt截图已看；旧Qt/停滞风险未宣称修复，独审与最终产品验收待办。详情work/evidence/T-020/validation.md。

## 2026-10-15 F-003

policy退出0（83文件），diff --check退出0。PR读取/日志成功后网络EOF/TLS。无产品修改，未全量测试、独审、REA实测或远程CI。

## 2026-10-15 F-003最终

policy退出0；技能文件/引用/脚本语法/方向列表与ImpeccableSHA/引擎/隔离context通过。REA合成分析/追踪退出0、篡改退出1符合预期；证据F-003/rea-probe-summary.json。PR #5最终ac75f6f四项SUCCESS；本地F-004为29测试22.30秒、环境烟测和规则回执通过。无产品代码修改，不重跑产品全量/独审。最终检查见F-003/validation.md。

## 2026-10-15 / T-021 worktree集成

产品1e6cd5ab02968dc7493b2cecc5b3625564f23b8d：dev.py check --all退出0，490测试174.80s、Ruff274文件、Pyright0、9合约、4wheel/4隔离环境通过；模板后端18+桌面8专项与Qt截图检查通过。新独立审查绑定bb5601a..1e6cd5a，55专项退出0，无可操作问题。旧schema1–6对照旧实际产物像素/完整manifest一致，schema7真实合成积分/OCR明确绑定/归一化/ZIP恢复保持。模板导入新空项目，字体在目的工作区保存；逐源一次解码按顺序释放。无测试容差/skip/类型忽略削弱；锁仅本地包版本。详细证据work/evidence/T-021/validation.md与independent-review.md。旧Qt中止/停滞仍UNKNOWN，真实准确率、大项目/DPI/最终Windows与远程CI未验收。

## 2026-10-15 / F-006 当前版本展示

产品1e6cd5a未改。独立合成演示已启动；实际两条后台run均succeeded，已生成PNG/模板。documents捆绑Python生成Word，默认LO渲染退出1后改Word原生导出PDF退出0，Poppler渲染7页全部已目视检查。使用报告/本机启动脚本在.local/deliveries/WB-preview-20261015-2，详细F-006任务/validation。未重跑产品全门禁，不扩张为真实科学或包态验收。

## 2026-10-15 / T-022

最终产品32a2d18：dev.py check --all退出0，500测试173.83s、Ruff289、Pyright0、9合约、4wheel隔离环境通过。独立代码审查17专项9.02s无发现；原生1280×900/1100×780变化图视觉ship。演示窗口已打开，真实PID41120/启动stderr空，合成数据。旧WBQuant只作外观参考，不继承旧操作；科学/DPI/最终安装包与远程CI未验收。证据work/evidence/T-022/validation.md。

## 2026-10-15 / T-023 静态设计候选

三张本地HTML浏览器实拍1440×900，A/B首轮、C标签对比度修复后检查；6份JPEG来源嵌入scan0missing。产品未改，不重跑T-022全门禁或声称功能验收。详情work/evidence/T-023/validation.md。

## 2026-10-15 / T-023 正式A

产品0d9aad94最终505/173.57s全门禁退出0，Ruff298/Pyright0/9合约/4wheel通过；独审15/8.13s；视觉两项修复resolved。一次完整测试约100项后停滞，专属pytest停止exit1；未改产品以faulthandler_timeout=30重跑通过，无超时栈，根因UNKNOWN保留。DESIGN/sidecar已更新，原生13截图元数据0missing；合成演示PID34964以进程为准。完整证据work/evidence/T-023/validation.md。

- 2026-10-15 T-024自动核心子树：40定向测试通过1.31s，Pyright WB源/新测试0，Ruff通过；10真实TIFF仅本机只读探针，详见work/evidence/T-027/automatic-core-validation.md；独审/全仓由集成继续。

- 2026-10-15 T-027后续：58定向2.34s通过（质量复核原始积分/Qt显示/CSV-XLSX/旧项目归档），Pyright0；不改变有效信号/归一化，schema1–7表布局不变。

## T-024 / 16f3877

`uv run --locked --no-sync python dev.py check --all` exit0；532/193.25s、Ruff/Pyright0/9合约/隔离安装通过。真实10图自动链与ZIP恢复通过；独立5复现exit0/5.24s，修复resolved。首次全量527/1旧schema8拒绝预期失败及显示格式预期更新均详记T-024 validation。

## T-028 / 审核提案（基线93792bc，产品16f3877）

context --task T-028 --scope work --scope .agent-handoff --scope .impeccable/critique --record exit0；Impeccable context/detect exit0，detect为[]且PythonQt不代表视觉通过。Taste draw exit0，seed216553621；独立A/B审查完成，真实ZIP恢复/8页Qt截图脚本exit0。初次复制活动工作区遇到锁失败，改为不可变ZIP恢复，原资产未改。critique-storage write/trend exit0，只有本次快照，无趋势结论。产品测试未运行（无产品变更），键盘/读屏/高DPI等未验收。

## 2026-10-16 T-029
74a597b完整check --all退出0：560 passed/210.93s，Pyright0、9合约、隔离wheel/真实OCR烟测。48ecb72取消guard和11b1d96高DPI缓存增量专项回归通过，最终独审绑定11b1d96无未解决发现。完整命令边界及首轮失败保留work/evidence/T-029/validation.md；真实10图原哈希不变但质量警告仍需人工科学审核。
- 2026-10-19 T050/main221a2df：规划文档链接/PDF blob一致性、policy、diff、handoff容量均exit0。policy扫描0产品文件不证明产品通过。PDF文本初次GBK控制台失败，UTF-8重读exit0；归档目录缺失已由main原始blob恢复。产品测试/GUI/安装/科学评分未运行，后续文档审查见T050证据。
- T050方案fa61c29独立文档审查无阻塞，精确回执/链接/PDF/归档/diff exit0；PR16为Draft，远端检查以最终head为准。本轮仅规划，不合并或实施产品。
- T050后续澄清：当前方案942ecaa增量独立文档审查通过，按蛋白行分别管理槽位，检查exit0；无产品测试或修改。
- T050方案66f0b67：S1/S2批准与独立OCR功能保留的增量独审无阻塞；回执/diff/链接/PDF/容量exit0。无产品或安装验证。
