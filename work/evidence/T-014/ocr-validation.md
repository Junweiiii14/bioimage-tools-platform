# T-014 项目OCR关联阶段验证

- 日期：2026-10-14；Windows、Python3.12.14、uv0.13.0、Qt6.12.0，既有锁定离线OCR/数值栈。
- 代码提交：`05e5d5631ad4249bb2fc3b89c2265c6460a372eb`；此阶段base `e2b9b6b`，同任务定量代码 `79a675a`。作者自验，独审未执行。
- wb-tool0.12.0 / bioimage-app0.7.0。项目schema v4，继续读取v1/v2/v3；原定量公式、模型版本和平台字段保持。

## 实际命令

- `uv run --locked --no-sync python dev.py check --all`：退出0，268测试（79.48秒）、Ruff198文件、Pyright0、9导入合约、4wheel/5隔离安装场景。日志在ignored `.local/requirements-review/T014-ocr-check-all.txt`。检查后仅更新任务/研究/验收文字与交接，无产品代码更改。
- `uv run --locked --no-sync pytest tests/test_project_measurements.py tools/wb/tests/test_project_analysis.py -q -x`：中间版本23例通过（16.78秒）；随后增加晚到导入保护和绑定列表回归，最终单独桌面9例通过（16.64秒），并纳入268全量。
- `uv run --locked --no-sync ruff check . --output-format concise`、`ruff format --check .`、`pyright`：最终退出0。中间长行/闭包类型收窄修正，没有忽略、skip/xfail或容差放宽。
- `uv lock --offline`、`uv sync --locked --all-groups --offline`：退出0；锁文件仅本地wb-tool0.11→0.12、app0.6→0.7版本，无第三方依赖升级。
- `git diff --check`与产品提交hooks：退出0。规则回执已随module-map版本刷新；安装场景增加v4读取、真实OCR输出的显式绑定和XLSX验证，未削弱旧场景。

## 有效性与生命周期

合成两个不同SHA原图具有相同蛋白名称，OCR拼图含Fig1A/2B。实际Qt+worker+存储验证确认绑定后的六槽为4000、空、0、8000、16000、0。名称修正撤回确认，确认后恢复同一原图值，原图行标签不被偷偷改写。来源表保留OCR run、目标row_id与测量run/source/lane/revision，等号开头标签按字面字符串导出，无公式。

核心负例包含错误资产摘要、外来文档运行、错OCR来源、缺失token和不存在目标；旧v3读取器拒绝v4。重开验证RunRecord与资产，再核对原文副本。OCR结果损坏使关联表为空/ocr_unavailable，同时另一原图的有效8000仍可读。改ROI后即使重新审核也不给旧关联数值。绑定候选随原图审核变化更新，保存人工名称编辑。

真实识别取消保留之前OCR和关联；识别期间关闭等到进程/线程退出，期间编辑拒绝后到结果。导入期间新编辑也不被覆盖。成功重新识别重建未确认行，人工绑定/确认是进入有效表的必要条件。

## 用户材料与界面

只读探针 `.local/requirements-review/probe_project_ocr.py` 通过真实项目宿主导入、识别、保存和重开一张用户组合TIFF；15个原始token、11个未确认/未绑定行，源SHA前后相同，所有值为空。总流程91.05秒包含导入/识别/关闭/重开，不是OCR单独性能测量。工作区、JSON和截图都在ignored `.local/requirements-review`，不提交私人材料。

已查看源码Qt截图 `T014-project-ocr.png`（私人组合图）和 `T014-project-ocr-synthetic.png`（解析样例）：原文位置、可编辑名称、确认、明确来源选择及自动结果可见。未调用被用户停止的原生Computer Use；截图不等于最终包态/DPI验收。

## 保留限制

每项目当前一张独立TIFF拼图，最多512个OCR行；生成PNG与PNG/JPEG识别、归一化、批量元信息、统一归档/导入、模板精修仍见首版核对表。没有真实人工真值/准确率结论，不擅自确认用户实验关系。Qt历史偶发Aborted根因仍UNKNOWN，本轮通过不是修复证据。未执行独审、远程CI、最终Windows打包/干净机/物理FAT或用户完整工作流验收；T-014进入review，整体Goal保持active。
