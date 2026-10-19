# T-041 标准显示行策略

状态：已实现、集成及独审；全门禁未通过（见T040）。范围：WB实验室显示版式、显示来源及schema、相关契约和测试。

用户授权：同Fig原图ROI可有不同分辨率/位深，定量和原值裁剪仍使用原始样本；显式standard_lane_ratio@1显示策略按泳道单位宽120（可1200）和4/5高度生成RGB8显示图。旧默认native_samples@1保持原行为。32M像素预算保持。

验证计划：异原生尺寸同Fig、可回源manifest、旧native拒绝异宽、原样本不变、预算拒绝及既有回归。独立审查由协调任务安排，未完成前不宣称独审通过。

实施完成，已由协调任务集成并独审至f7a6651。基线3539f802018f597d56a7bf8cdd8e36af14c627e9，分支codex/t040-standard-display。

新增DisplayFrame及FigureSlice.display_frame：仅显式标准显示可用，有限数值/正宽高/±30度，四角约束原ROI和图像内。manifest每实际标准段含source_to_output矩阵及采样身份。双线性仅显示，不进入原值裁剪或定量。Qt真实FigureProjectView roundtrip保留policy/unit/frame，几何编辑清除frame。

检查环境：Windows、CPython3.12.14；借用t021-coordination/.venv，PYTHONPATH显式指向本工作树全部成员src。
- 首轮58定向测试：56通过/2失败(exit1)。一项预算负例fixture实际低于32M，改为增加缺图行构造真实超限；另一项native manifest冻结hash因新增默认style字段变化，产品修复以保留原native manifest表示，未改冻结预期。
- 新frame+Qt专项首轮4通过/1失败(exit1)：既有Qt重建columns顺序与原元组不同，改为按Fig列映射及slices核对；不改变产品列行为。
- 最终8测试文件88通过(exit0)：test_standard_display、test_standard_display_ui、test_laboratory_layout、test_laboratory_decode、test_laboratory_compatibility、test_figure_template_io、test_figure_image_export、test_figure_project。
- Ruff目标文件检查exit0；Pyright strict目标7文件exit0（.local/pyright-standard.json仅配置本树src及借用环境，不降低规则）。第一次直接Pyright因本树空.venv导致依赖解析失败，临时config第一次绝对include被忽略没有检查产品，随后修相对include并实际通过；不将前两次视作有效通过。
- 全仓check、真实用户8图及独审未运行，由协调任务负责；原科学算法/依赖/锁文件/门禁未改。

独审P1修复：display_frame仅允许first_lane=1且last_lane=row.lane_count的完整原行；部分泳道段明确拒绝，防止整行frame重复采样却声称分段泳道。ROI四角限制未放宽。新增3泳道[1,1]/[2,3]重复整行frame负例；标准显示/Qt/既有native拆段与冻结manifest专项31通过exit0。Pyright首次新增测试list缺类型报3项，补FigureSlice类型后复查；不降低规则。

协调结论：P1修复后独审无新增发现；8真实样本显示/回源/位深及Excel独立复核完成。全量测试输出600passed，但check最终exit1、原因UNKNOWN，不能声明全门禁通过。
