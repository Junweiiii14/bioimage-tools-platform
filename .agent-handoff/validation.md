# Validation History

- 2026-10-18 662d767绑定独审5项0.37秒0；实际View两个自有原生观察进程actual0/noAV，显式parent/view无效后仍11无parent控件。后继补隐藏控件父归属，隔离生命周期旧红1failed/2.27秒、新绿连诊断6项2.21秒0，工作流/保存重开/定量重算12项18.09秒0、相关Pyright/Ruff/格式0。共享Qt试验caplog teardown KeyError保留，正式用独立进程未忽略错误。原生AV根因UNKNOWN，后继完整检查/绑定独审待做。

- 2026-10-18 efec471 check --all带退出清单/native observer：700passed/1failed、488.11秒，原child/外层1，wheel未跑；未复现AV。失败trace证实全局4208根超128根预算，新测试对象未入截断报告。测试隔离真实Qt根/来源表并补根/节点/容量反例，作者5项0.46秒0、相关Pyright/Ruff/格式0；后继完整检查/绑定独审待做。不是产品退出修复。独立三角峰解析36750在35%首次支持、准确36750，诊断原型0，无参考像素/产品注入；候选v2未实施。

- 2026-10-17 T042/base b32acff：context/doctor/smoke-env/policy/gh只读认证/8源图SHA检查均exit0。配置证据work/evidence/T-042/configuration.md；私有清单.local/t042。未跑产品测试/全门禁/重新识别/独审；doctor过时product_status不作产品结论。

- 2026-10-16 T035/25ac71d：两指定原图端到端与原值像素核对退出0；独审18专项退出0；首次全量581 passed但退出1、根因UNKNOWN，最终复查见work/evidence/T-035/validation.md，不把测试摘要等同进程成功。

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

## 2026-10-17 T-037 / fb6e461

完整check --all exit0：594 passed/396.92s、Ruff/Pyright/9合约/隔离wheel及安装桌面/OCR通过。前轮592pass1fail追加图缺分段已修且保留失败记录；初始领域pathlib边界也已修，未降低门禁。最终代码独审覆盖fb6e461，已知发现全部修复。视觉与实际Qt最终证据见work/evidence/T-037/validation.md。

| 2026-10-17 | T-041 | Windows/Python3.12.14借t021环境、本树src | 8文件pytest88passed；Ruff/strict Pyright目标通过exit0 | 首轮失败与环境配置过程见任务；全仓/真实8图/独审未运行 |

| 2026-10-17 | T-041独审修复 | 同前环境 | 标准显示/Qt/原生分段31passed exit0 | frame限制完整行；旧像素/manifest保留 |

## 2026-10-17 T040 real-data execution
Product f7a6651 independently reviewed; actual8sources/4Fig/48values and supervised workbook audited. Scripts finish/supervise/open passed, visible8row project.600pytest passed summary, fullcheck exit1 unexplained beforewheel; not gate success. Separate installed-wheels exit0. First automatic crop1/8, corrected8/8 reference-assisted;33/48quality warnings. Details work/evidence/T-040/validation.md; no private originals committed.

## 2026-10-17 T040 causal replays
HEADcc626d7/productf7a6651. deep-causal-replay.py and deep-boundary-replay.py each exit0; independent source-only diagnosis, no original/reference/project modification. Confirmed107/119/118membrane gate,8→7Marker deletion,4H_N2CVfallback,17/17old boundary reproduction. Report cross-reviewed by crop/quant/pipeline agents. Documentation only; no new fullgate or package claim.

- 2026-10-17 T042产品9eb5a1b：58相关测试、114倾角×N探针、8图正常网页工作台/导出/重开及48DOM结果、独立wheel/smoke/policy均exit0，产品独审完成；完整check因原生挂起人工停止exit1，desktop单模块10passed/exit0。所有失败和分进程诊断以work/evidence/T-042/validation.md为准，不能据passed计数报全门禁成功。

- 2026-10-17 GitHub日志：gh issue create退出0，Issue #6；gh issue view回读正文与本地副本归一换行后全等。只改文档，未重跑产品测试；既有全门禁失败状态不变。

- 2026-10-17 T043产品2e5021d：642完整check/361.62s含隔离wheel exit0，独审14项exit0；治理0b786cb独立44完整check/165.88s exit0，独审6负例exit0；合并树e0be945再次正式完整check，657passed/427.30s及全部隔离wheel exit0。8原图/12参考SHA与34原有未提交文件SHA保持；原生间歇挂起仍UNKNOWN。阶段整理8清单独审exit0，不替代历史产品CI。


- 2026-10-17 CI001：CI001之后最终产品树fa9c5f2正式完整check实际exit0：657passed/451.28s，全部隔离wheel含真实OCR完成。日志.local/t043/check-final-ci001.log；文档后继与此产品内容相同。 旧阶段自身环境8进程测试/10.89s退出0，guard模块双平台类型0；Windows全项目Linux目标因Qt平台存根8错不作为Linux CI，实际Linux以远端为准。

- 2026-10-17 CI003b4bc8ba：完整check --all实际exit0，658passed/497.50秒及全部隔离wheel/真实OCR；独审3项exit0。8原图工作台宿主导入/处理/保存重开exit0，SHA不变、参考未读，离屏截图空白不作视觉验收。CI00468c3265独审2项exit0，完整659正在执行，结果另记。


CI004产品68c3265正式完整check --all实际exit0：659passed/509.86秒，静态/架构/政策检查和全部隔离wheel、真实OCR/worker均通过；日志.local/t043/check-ci004-final.log，退出码记录.local/t043/ci004-final-gate.json。没有修改时限、预期、skip或依赖；通过不证明偶发超时根因。


CI006产品a811ccfd正式完整check --all实际exit0：668passed/508.54秒；Ruff/format/Pyright/import/policy及全部隔离wheel、真实桌面异步关闭/OCR/worker均完成。日志.local/t043/check-ci006-final.log，退出回执.local/t043/ci006-final-gate.json。保留原测试/时限/依赖，之前79f9070失败不抹去。


CI009产品57fd7ea正式check --all实际exit0：669passed/497.77秒，Observed child exit0/u32=0；Ruff/format/Pyright/import/policy及全部隔离wheel、真实桌面异步关闭/OCR/worker均完成。日志.local/t043/check-ci009-final.log，回执.local/t043/ci009-final-gate.json。原5秒等待/15分钟/全部断言/依赖不变。此前Windows与旧退出失败仍保留。


## 2026-10-17 T043本轮交付

产品57fd7ea本机669/497.77秒+全部wheel实际0；becb389远端run39025981922完整成功：Windows669/407.87秒child0、Linux669/178.49秒，两平台全部隔离wheel/dev最终成功，规则/桌面环境成功。CI009及T043本轮complete，T003/科学/交互/发布/历史UNKNOWN继续保留。8图正常工作台链0，8几何/48值状态保持，参考未读。独审复核远端两HEAD、入口/父路由、最新bundle/34原文件SHA和已发日志正文；9草稿PR未合main、6旧树仅锁定，其余原改动/旧结果保留。后继仅收尾文档，仍按规则/独审/安全普通同步完成。维护计划已给简单报bug材料与后续维护步骤，无自动调度。


## 2026-10-17 CI010 Linux退出SIGSEGV

0d仅文档后继Linux669/146.29秒后SIGSEGV主线程noPythonframe，exit245/wheel未跑；同HEAD Windows669/346.68秒child0+wheels/dev成功。T043重开in_progress，旧成功/失败全保留；CI010只增显式GDB观察/0与17与真实SIGSEGV控制，不猜测性修Qt清理，不改产品/断言/15分钟。作者相关8项2.49秒0，双平台模块类型0；Linux控制/全检待真实执行，独审待绑定。

- T044锚定上下文阶段：112相关20.79秒0（含旧文档/worker/OCR/schema）、既有网页9项27.89秒0、新快照1项1.98秒0、入口12项4.17秒0，全项目Pyright/Ruff/格式/Node语法0。8原图当前Web正常导入8worker/新导出/重开关闭实际0，.local/t044/workbench-anchored/validation.json，原SHA/参考未读，CSV48槽13valid35review，背景不足2/旧21。旧205全检不覆盖新阶段，最终完整门禁/绑定独审待做；离屏GPU告警不作视觉验收。e6d1abd独审2项2.33秒0关闭归属P2及核父路由。

- T044 3a830fb正式check：696passed/488.23秒后AV，原child3221225477/c0000005、dev/外层-1、wheel未跑，实际失败；native-exit.md新证据1线程Qt父子/包装器析构，精确根因UNKNOWN。独审18项11.36秒0/P2不变target清人工参数；后继作者38项29.70秒0+新API/公开桥接2项2.00秒0、相关类型/Ruff0，待绑定。29未扩展原面积/bounds/flags与完整成图像素保持。

- T044 9f96f5c绑定独审2项1.64秒0，P2关闭。四组Qt-only控制observer均附着、exit0/无fault，未复现非产品修复。新增可选qt_exit_inventory观察器2项0.34秒0/相关类型Ruff格式0，源码/描述见T044/native-exit.md；绑定审查和必要完整检查待做。

- T044诊断容错：694279f独审2项0.38秒0，后继故障注入旧1failed/0.58秒1、新3passed/0.45秒0，相关类型/Ruff/格式0；未改原测试结果/时限。提交绑定复核及带对象清单的必要完整检查待执行。
