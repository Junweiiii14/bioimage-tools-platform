# T-009：Fig/行名 OCR 与结果表自动写入

- 状态：implementing
- base commit：34831e4
- 上位目标T-003：完整WB软件；用户明确首版必须拼图Fig/行名OCR和结果表自动写入。

## 范围/必读
tools/wb、apps/desktop、tests、tooling、docs、work、.agent-handoff、pyproject.toml、uv.lock、README.md。
读取根规则、架构/模块地图/编码规范、WB/桌面README及公开契约；旧wbquant-improvements只读。

## 行为/验收
本地OCR有真实引擎与模型版本/摘要，不以手工输入或空成功替代识别；识别Fig/行名、保留位置与置信度，失败可人工修正。
拼图区域/行名/列与稳定lane/band身份显式关联；定量仍来自原TIFF快照，不读取OCR显示副本的灰度。
结果表按当前已确认关系自动更新，失败/排除/缺失/待复核保持状态与空值，不转零；同Fig泳道顺序显式保存。
导出新文件而不覆盖原输入/已有结果，命名字符串不能变Excel公式；文档与算法版本及旧v1兼容须说明。
真实OCR合成标注图、位置/匹配/歧义反例、数值自动写表、GUI保存重开/过期结果和隔离安装验证。

## 当前阶段
先冻结旧OCR/worksheet/table_export来源与语义，实测本地CPU识别，随后接入领域/worker与Qt表格复核。
独审/远程CI/产品打包与整体退出仍待办。T-008偶发原生中止风险保持跟踪。

## 后端子阶段
已实现真实离线PP-OCRv6、模型摘要守卫、分块坐标/去重/取消检查、Fig/行名空间建议、显式绑定/有效signal自动填表、无覆盖字面XLSX。
完整自验199tests/9导入合约/4wheel5场景；核心不加载OCR，GUI安装场景真实OCR。独立读取器验证数值和Unicode。
当前仍implementing：专用OCR worker、Qt人工修正/确认与实时写表、文档版本/旧兼容、跨图关联等尚未完成。
