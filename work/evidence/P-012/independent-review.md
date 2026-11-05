# P012 独立审查

用户明确授权只读子代理独审。审查者 p011_independent_review，未修改源码或证据；本记录由主代理依据其返回结果整理，作者自验不算独审。

- 基线：ec7588ded1a7e8ac5febec5d2faed51e7ef0e0fc。
- 候选：76bd5b760a89c5115bea1d9456970dbdf8279daf。
- 范围：完整产品/测试差异、生成器及练习说明。
- 结论：两项基线 P2 在本次范围内关闭，无新增可确认问题。

顺序字段保留 input 的 reflow/局部绑定，change 不再销毁下一次点击目标；选择控件路径保持。后端保留匹配项目的有效 mode，前端按 allowedModes 过滤；editing、未就绪、未知 mode 回 intake。新增鼠标测试使用实际 Qt 事件，关闭重开用例释放旧宿主并核验结果页、导航记录、项目数据。

独立验证均 exit 0：

1. `node -` 提取真实 desktop_session.route 和 intake.allowedModes，六种情况覆盖 results/quant/review 恢复及 editing/未就绪/未知 mode 回退。
2. `uv run --locked --no-sync python -` 在临时目录运行生成器，核对两图 uint16、300×700、仅膜外一像素不同；二次运行 FileExistsError 且 SHA 不变。

为避免与作者全量门禁干扰，未并发执行 GUI/全套测试。旧非顺序网格仍沿用原重绘行为，本次不声称覆盖其交互。科学、真人学生与干净目标机未验。后续产品/测试变化需复审相关结论。
