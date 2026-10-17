# T-014 多源定量第一阶段验证

- 日期：2026-10-14；Windows，Python3.12.14、uv0.13.0、Qt6.12.0；本仓库锁定NumPy/Pydantic/tifffile/OCR栈。产品base5bea9d3，验证产品commit `79a675aeba70a0dbd5428a439dd23b694dce1f49`。
- 第一阶段记录时任务implementing；这里只覆盖多源定量、曲线、自动表与XLSX。后续项目OCR验证见ocr-validation.md；当前任务状态以任务文件为准，归一化、独立审查和最终产品验收仍未完成。

## 命令与覆盖

- 最终 `uv run --locked --no-sync python dev.py check --all` 退出0，产品提交79a675a：262测试（72.36s）、Ruff191文件、Pyright0、9导入合约、4wheel/5隔离场景全部通过。原始完整日志在ignored `.local/requirements-review/T014-check-final.txt`。
- `uv run --locked --no-sync pytest tools/wb/tests/test_project_analysis.py -q`：基础13例通过。解析三角积分、重复名称/不同SHA、空位/真实0/缺图、请求与RunRecord身份、JSON重复字段、坏资产摘要、过期几何/修订、终态失败。
- `uv run --locked --no-sync pytest tests/test_project_measurements.py -q -x`：最终5例通过（8.15s）。真实Qt编辑与后台WB进程、工作区提交/源SHA/运行ID、自动表/重开、人工基线4000→2500与未选源8000保留、XLSX数值；关闭第二行保留第一行且第二行cancelled；坏资产/外来run隔离、改ROI后stale、删除行同步去计划、运行中编辑拒绝批次覆盖。刷新表格后再读取/计算也保留未保存的新基线。
- `uv run --locked --no-sync pytest tools/wb/tests/test_project_analysis.py tools/wb/tests/test_worksheet.py tests/test_project_measurements.py -q -x`：导出共用代码阶段22例通过；之后增加恢复故障/旧批次负例并纳入完整门禁。
- `uv run --locked --no-sync pyright`与Ruff最终相关检查退出0，没有忽略、skip/xfail或容差放宽。
- `uv lock --offline`、`uv sync --locked --all-groups --offline`退出0。uv.lock只改本地wb-tool0.10→0.11、app0.5→0.6元数据，无第三方依赖升级。
- 隔离安装GUI场景新增v3计划/建议共存、旧读取器路由和XLSX导出断言。已存在的4wheel/5安装场景、单图GUI、离线OCR识别和静态OCR worker继续运行。
- `git diff --check`及产品提交hooks（Ruff/format/policy）退出0。无推送、PR、main集成或发布。

## 失败及修复

1. 开发初次把严格dataclass经model_dump变成dict再校验，13基础例全部失败；改为原类型字段重建，并保留严格模式。
2. 新的结果损坏负例发现list_runs会因一份坏结果整体失败；增加通用StorageCommand(run)调用既有Workspace.get_run逐项核对，坏行留空，另一源仍有8000；平台完整性检查保持。
3. 首轮完整门禁262例（70.73s）及隔离安装退出0后，自查发现刷新表格可重置编辑器dirty却未保存新参数。修复为重设编辑器前接受当前模型，扩展Qt基线回归并重新执行完整门禁。没有把首轮结果当作最终提交证据。
4. 中间格式/严格类型错误修正为明确列表/回调类型与公开类型导入；没有降低检查标准。

## 界面和科学边界

源码Qt截图 `.local/requirements-review/T014-measurements.png` 已查看：泳道边界、空槽、原曲线/基线、结果表可见；使用合成技术数据。原先的包态物理Esc限制仍遵守，未操作原生Computer Use。没有用用户原图编造条带边界、实验真值或准确率。

结果加载64 MiB、GUI每页200槽、XLSX每表200000单元格的限制明确记录；未宣称大项目性能验收。CLX按用户说明排除。历史Qt原生中止本轮未复现，根因仍UNKNOWN。作者自验不算独审，未执行远程CI、干净机、最终打包/DPI/物理FAT或用户完整工作流验收。
