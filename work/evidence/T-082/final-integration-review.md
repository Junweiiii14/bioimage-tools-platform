# 最终源码集成独立复核

## 审查绑定与结论

独立审查者 `/root/independent_review`，非本轮实现作者。对 `44ee78c36a0edb5d6cd9bd0798bbca3e25edd4da` 相对基线 `18b5cf6de0c83b8c67f26433a6059d8dabf1f381` 的整体差异，以及后续修复 `d1036c2bf40e7cac91c979e993d5053e148cb710` 相对 `44ee78c` 的准确差异，均给出 **Accepted（源码集成与条件处置）**。两次范围合并覆盖截至 d1036c2 的全部 tracked 代码与门禁变化。

此结论不代表目标完成。44ee78c 完整门禁实际失败已保留；后续冻结全门禁、真实构建、新检出与安装态验收现已有各自证据，见文末增量记录，未沿用旧测试通过记录冒充最终状态。

## 整体集成审查

- R01/R02 终态与资源准入、R03/R05 选择和操作结果、R09 渲染/失败恢复交互未发现新的实质冲突；构建来源到候选/隔离安装验证没有绕过入口。
- 科学冻结十文件 Git blob 与原始基线及冻结摘要一致；uv.lock、pyproject、旧规则/导入验证器、历史 schema reader 保持。没有改动领域/用例算法定义、让显示数据进入定量或削弱科学容差。
- 原行内预览断言的变化对应共享传输协议，已有实际图像显示与完整结果保持检查；没有用删除测试或放宽通过标准隐去失败。
- 独立重算 R09 八份原始 JSON 和两份摘要清单，结果与文档相符；所有残余超线及小例回退明确保留，R09/R12 条件处置范围可接受，不等于性能全面通过。
- 整体源码审查时树 clean；该审查未运行测试、GUI 或构建。44ee78c 之后的证据/文档变化不会被冒充为此前审查运行过。

## d1036c2 行为复核

独立命令（本机 Win11，进程局部 `QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu`）：

`uv run --locked --no-sync pytest tools/wb/tests/test_standard_display_ui.py tests/test_web_quant.py::test_anchored_snapshot_keeps_target_distinct_from_sampling_context tests/test_image_review_workbench.py::test_graphical_crop_undo_redo_revoke_geometrical_confirmation -q --tb=short`

结果 **4 passed / 1.91s / exit 0**。另以 `uv run --locked --no-sync python -`、离屏 QApplication 和真实 FigureProjectView 运行五组独立临时探针，exit 0：同行两轮 undo/redo 再 undo 的 frame；跨行多历史 ROI/N、身份及其他行保持；同行与跨行不完整 N 编辑拒绝且历史游标/控件不变，修正后恢复；合法后续 empty-slot 元数据使旧 N 无效时拒绝，纠正后仍可 undo/redo。

探针设计前期三次使用 mixed_resolution 小图改变 N，被既有越界/empty-slot 规则拒绝；改用既有 ratio_crop_view 的同尺寸合法几何夹具后完成上述验证。这些是探针输入适配，未修改产品约束或测试容差。

修复只避免同一语义行的额外选择提交，完整编辑校验仍在任何选择/控件/历史变化前；跨行仍提交有效编辑。旧历史条目不保存全部 frame，未扩承诺跨行或保存后撤销的 frame 行为。量化替身只适配新 selected_row_id，原 target/context 断言保持。

## 日志与差异检查边界

`git diff --check 44ee78c d1036c2` exit 1，仅报告收录的原始失败文本 `final-check-44ee78c-failed.txt` 三处 pytest 源代码上下文尾空格；产品/测试差异无空白错误。保留失败日志内容，不因格式检查改写原失败材料，也不将整个 delta 的该命令写为 exit 0。

R09 原始 32 份 JSON/log 已逐文件比对复制到 [r09-raw](r09-raw/README.md)，以便新检出取得原始采样，不只依赖忽略目录里的摘要。目录的证据文件属性仅保留这些字节，未改产品/脚本换行约定。

## 最后源码修复与冻结证据

后续私有Python验收首次真实暴露wrapper自写pyc，`f5d7ac9e05b0d701818ceced7277edd09d10024b` 最小修复获得同一非作者准确差异 **Accepted**：独立5测试21.13s/exit0，真实PS5.1/7特殊路径与exit7传递，已有缓存仍拒绝；见 [r07-private-runtime-repair](r07-private-runtime-repair.md)。随后的4份文档冻结提交 `ed830e1d3bab3d0c8c57f3766a898991e8a0f431` 增量同样Accepted。科学十文件、公式/schema/既有导出未变。

非作者独立审计 ed830e1 完整门禁 **1503 passed / 756.15s + installed_wheels / exit0**，核对准确HEAD/clean与日志/exit摘要；没有把d66655b旧1501通过替代它。随后实算Temp外最终安装器SHA `5c49309132a8152c8b095dd255acdcef9adf02ecfa68175e36a6de83be724268` 和manifest、PS5.1/7新检出7794文件/requests/previous失败链、真实升级、schema1–6、双诊断、卸载均给出 **Accepted**，详见 [r11-execution](r11-execution.md)。

卸载独审实算173文件摘要/大小，核对当前验收键/5快捷方式/launcher/privatePython/uninstaller消失，设置marker和Lab摘要保持；实际1300残留与报告相同。第一诊断没有worker PID，资源关闭检查不声称逐PID观察；第二诊断的两个worker退出有明确记录。双诊断stderr错误、Temp98零长文件遗失UNKNOWN、科学与物理环境未验保留。此阶段仅只读证据审计，没有再次启动产品/测试或清理缓存。

## 最终交接差异独审与治理检查

非作者 `/root/independent_review` 对准确 `ed830e1d3bab3d0c8c57f3766a898991e8a0f431..9ec7b1d0a1b2983b22ef6b7e784276ba9242269c` 的19文件差异给出 **Accepted**，检查时HEAD相符/clean。产品、测试、依赖锁、工具与门禁实现无变化。回执结构只改变 `docs/ai-workflow.md` 摘要，实算Git blob SHA `14f2bc28505cd1774bda2de15246d4924985ec36308574abb8e150918124bb79` 一致，base/scope/其余规则保持。原T045 work-log内容完整归档（仅段间空行归一），T046起旧记录逐字保持。

已提交ZIP与原件相同，183成员CRC/大小/SHA及本地原字节全部独立核对；9份acceptance的request/previous-report及两诊断引用可在归档中全部解析，7份Lab快照实算一致。只收文本，无原图/模型/安装器/项目二进制或原设置值，额外凭据及内嵌图像模式扫描0发现，不声称通用检测保证。新读者可从 [最终冷启动记录](final-cold-start.md) 区分当时未提交文件、实际小变更与早先只读R08，以及不同阅读字节口径。

独审确认源码/构建源与后续交接HEAD区分正确，全部实际数字/失败链/UNKNOWN/未验边界有证据；未发现剩余可执行工程或本机最小验收遗漏。R10仍需真实材料/负责人判断，列明外部环境未验；R09/R12有据处置，不制造重复测试或扩展整改。

独审指出的非阻断文字修正已落实：JS四项是“门禁与协议自检（含受控负例）”，第四项为typed producer wire保持；task R04同步精确表述；work-log明确深路径失败绑定较早d66655b；补最终冷启动链接。本收据与阻塞恢复状态是收尾记录，不改产品或为通过检查削弱要求。

治理验证：Root真实刷新 `dev.py context --task T-082 --scope . --record` exit0，对比此前已完整读过的输出逐节核对，未变部分摘要相同，变化部分以UTF8回读；没有手填规则哈希。`dev.py policy`扫描173产品文件/exit0；handoff维护首次将1段旧work-log先归档，再次changed=0/warnings=0/unresolved=0；新文档及入口本地链接检查158处/0缺失。`git diff --check ed830e1 9ec7b1d`独立exit0，`rule_context check --base origin/main --head 9ec7b1d`exit0。提交hook policy通过，Ruff/web因无相关源码变化明确skipped，不当作新产品测试通过。整体base差异含早期原始失败日志三处尾空白的历史边界仍见上文。
