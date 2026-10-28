# R12 条件性架构台账

核验基线462aa4e。规模本身不是重写理由；以下先记录读写/继续执行契约与触发条件，最终以本轮回归和R06实际变更更新结论。

## 12a 历史项目链

`application/crop_suggestions.py::read_figure_project`对严格整数schema1–15静态分派；输入最多16MiB，不按数据中的模块名加载代码。以下类逐层继承。序列化保留自身schema，功能采用经显式用例升级，不在读入时重算历史值。

| schema / 模型 | 样例来源和读写证据 | 继续执行边界 |
| --- | --- | --- |
| 1 WBFigureProject | `test_laboratory_compatibility.py::legacy_project`；bb5601a独立旧renderer金样摘要 | 旧行/模板；可显式添加检测/定量 |
| 2 WBReviewProject | 同上，suggestions字段 | 建议来源/坐标保留；应用后才变ROI |
| 3 WBAnalysisProject | 同上及`test_project_analysis.py` | 已提交run身份重新核验，不因重开重新测量 |
| 4 WBProjectOCR | 同上及项目OCR测试 | OCR原文/机器证据/人工绑定保留，失败重新识别不替换 |
| 5 WBNormalizedProject | 同上及明确配对归一化回归 | 明确映射/对照，不猜配；坏分母不填零 |
| 6 WBRestoredProject | 同上及`test_archive_restore.py`相关归档验收 | 外来历史不冒充本机run，原历史ZIP不递归执行 |
| 7 WBLayoutProject | `test_laboratory_compatibility.py` schema7采用/恢复；`test_laboratory_layout.py` | 布局采用保留已完成测量/OCR/归一化身份 |
| 8 WBAutomaticProject | `test_automatic_wb.py`及自动项目回归 | 自动建议版本/警告保留，不静默升级识别策略 |
| 9 WBPartitionProject | `test_fig_partition.py` | 原图OCR证据和独立泳道计划保留；取消保留旧项目 |
| 10 WBIntakeProject | `test_instrument_intake.py` | 清单对应不等于处理结果，明确确认后产生执行计划 |
| 11 WBIntakeWorkflowProject | `test_intake_workflow.py`重开/中断恢复 | 未知running不自动恢复为成功或重新执行 |
| 12 WBIntakeCropProject | `test_intake_crop_v2_compatibility.py` | 旧crop证据/来源/N保持；显式修改才失效 |
| 13 WBIntakeFigureProject | `test_intake_figure.py`及`test_intake_crop_v2_compatibility.py` | 成图/原值定量身份保持，坐标仍来自原图 |
| 14 WBIntakeOutputProject | `test_intake_output.py` | schema13旧表保持；失败不转pending/0，输出新目录 |
| 15 WBIntakeGridProject | `test_intake_supervision.py`及instrument_intake_view重开 | 网格设置保留，不重新计算已验证量值 |

schema1–6现有金样测试逐一保存/重开/渲染/ZIP/恢复并比对旧RGB与完整manifest SHA。其余主要为合成构造与版本化回归，不冒称每版本都有用户原始历史工程。workflow@4→@5是独立策略版本，已有`test_intake_crop_barrier.py::test_explicit_v4_continue_upgrades_without_rewriting_success_or_history`证明显式继续保留成功裁图/历史；不能与项目schema混淆。

当前无新增schema要求，也未在R01确认跨继承层缺陷；不拆继承。触发：新schema需要、复现跨层字段丢失/读取错误、或有预算依据的校验超时，届时仅迁移一个历史读取边界。R09性能测量可能提供后续触发依据；当前不称实测全部满足。

## 12b 请求类型

WBJob仍为53个显式操作与公共可选字段。R01仅把终态收口从分派主体分离，独审已核分派AST与基线完全相同；现有未知操作/缺字段反例和AST分支穷尽检查保留。当前缺陷不要求全量请求类型迁移。R02可通过统一TIFF入口配置政策，不需要替换所有job。暂缓typed preview，触发是必填字段混用的真实缺陷或单链维护需求，不能删旧分派覆盖来迁就重构。

## 12c 发行身份

现有10个iss含原windows_test、默认Candidate以及8个可选通道。T081实际活跃交付为Laboratory；其余脚本是仍保留的独立测试通道，是否被员工使用UNKNOWN，不能据代码未默认调用而删除。

所有通道有独立AppId、默认目录、包名、设置命名空间和入口；R06必须保留这些身份。当前仅记录重复，待R06实现时判断是否有明确收益收拢profile选择；没有需要则有据暂缓，不强行合并iss。测试安装须使用可弃目标且不变更客户正在使用通道的卸载注册。

## 本轮实现后的条件复核

R06 `516d7c0`、R07 `34824e1`及R09窄优化`e6b78b4`均准确独审Accepted。科学冻结10文件与原LF摘要一致；持久schema1–15和WBJob分派未改变。最后全门禁及安装事实另行记录，以下是架构条件判断，不冒充它们通过。

- **12a暂缓**：R09实测触发的是全量显示构造/传输调查，已经做局部索引和去重；没有证据将剩余耗时归因于继承深度，也没有新增schema或已复现跨层读取丢失。旧矩阵/原坐标/算法/人工证据继续保留，不借性能指标重写历史读取链。
- **12b暂缓**：R01终态修补及R02资源准入未要求改WBJob全部请求；R05只迁移宿主/视图状态端口。未知操作/缺字段及分派覆盖保持，未新增可证明必填字段混用的单链缺陷。仍按上文真实触发条件演进。
- **12c局部复用后暂缓全面收拢**：R07为可弃验收直接复用原laboratory模板的可选AcceptanceId宏及受限设置分支，未加第十一份iss。旧/新默认真实预处理一致，本次合成安装器摘要也一致；三个锁定ISCC编译exit0，19实际Qt通道设置独立通过。已有十种默认身份未合并/删除，用户数据无blanket卸载删除；新验收身份具有独立AppId/目录/设置/启动器。没有将其余仍可能使用的测试通道折叠成laboratory。实际安装仍待R11，模板编译不能代替登记核对。

R09剩余性能调查线及后续条件见r09-disposition.md，不因此自动触发三项大重构；若最终验收发现新的直接阻断，应重新评估对应小边界，不能用这份暂缓结论忽略实际缺陷。
