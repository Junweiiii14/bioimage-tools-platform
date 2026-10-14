# Validation History

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
