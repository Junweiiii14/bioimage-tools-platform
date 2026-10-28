# 最终源码集成独立复核

## 审查绑定与结论

独立审查者 `/root/independent_review`，非本轮实现作者。对 `44ee78c36a0edb5d6cd9bd0798bbca3e25edd4da` 相对基线 `18b5cf6de0c83b8c67f26433a6059d8dabf1f381` 的整体差异，以及后续修复 `d1036c2bf40e7cac91c979e993d5053e148cb710` 相对 `44ee78c` 的准确差异，均给出 **Accepted（源码集成与条件处置）**。两次范围合并覆盖截至 d1036c2 的全部 tracked 代码与门禁变化。

此结论不代表目标完成。44ee78c 完整门禁实际失败已保留；修复后的冻结全门禁、真实构建、新检出与安装态验收仍需各自真实证据，不能沿用旧测试通过记录。

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
