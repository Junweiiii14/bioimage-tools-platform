# T-017 批量元信息与缩略图验证

2026-10-14，本机Windows，base0c8fc3f，feat/T-017-project-metadata-batch。wb-tool0.15.0、bioimage-app0.10.0；Python3.12.14、uv0.13.0、PySide6/Qt6.12.0，锁定数值/OCR依赖不变。规则回执rules-context.json已随范围记录；docs/module-map更新后刷新并读取差异。

## 实施

只读有界XLSX/CSV → 明确表头/列/完整键 → 可编辑提议/目标 → 勾选行与字段 → 严格模型原子应用。共同值和字面文件名分段共用提议/应用。名称与顺序不改测量，N/空位撤回审核，保留原run/OCR/归一化配置但拒绝旧有效值。后台原图128边缩略图/显示缓存、坏图继续和重开按需加载；后台表解析和迟到取消/关闭/编辑保护。无schema/积分/外部依赖变化。

## 命令与结果

所有命令在仓库根，前缀uv run --locked --no-sync。

| 检查 | 结果 |
|---|---|
| pytest tools/wb/tests/test_figure_project.py tests/test_project_measurements.py -q | 26通过，36.26秒，退出0；已有拼图/OCR/定量路径 |
| pytest tools/wb/tests/test_project_metadata.py -q（最终单元组） | 23通过，0.85秒，退出0 |
| pytest tools/wb/tests/test_project_metadata.py tools/wb/tests/test_project_analysis.py tests/test_project_metadata_ui.py -q（增加坏DEFLATE反例前） | 48通过，5.24秒，退出0 |
| pytest tests/test_project_metadata_ui.py -q（截图组） | 6通过，4.79秒，退出0 |
| pytest tests/test_figure_desktop.py tests/test_project_metadata_ui.py -q（修复关闭回归） | 13通过，7.48秒，退出0 |
| pytest tests -vv -o faulthandler_timeout=15（停滞诊断） | 145通过，98.74秒，退出0；未复现、无超时栈 |
| dev.py check --all（最终） | 退出0：335测试110.95秒、Ruff224文件、Pyright0、9导入合约、4wheel/5隔离安装场景全部通过；无超时栈 |
| uv lock --offline / uv sync --locked --all-groups --offline | 退出0，仅两个本地包版本变化，第三方依赖未变 |
| git diff --check | 退出0 |

新增测试覆盖：重复文件名/输入键/目标、未匹配/大小写、缺列/非法列、空白与0、明确清空、项目名冲突、选中位置排序、非法N/空槽/原子拒绝、文件名段数、过期草稿、共享/内联富文本、公式缓存与数组区域/合并、坏坐标/共享索引/重复节点、宏/外链/DTD、坏ZIP/DEFLATE、压缩/行列/单格/区域预算、嵌图不解码。Qt覆盖字段与行选择、手改公式/目标、保存重开、真实测量4000/空/0不变及N变化失效、v5归一化保留、取消/关闭/晚到编辑、坏图继续、位深/像素/缩略图。项目用例另验证完整OCR原文/关联/已验证值、归一化与run在改名后保留、N变更后不复用旧值。

相对T-016新增31项测试，无旧预期/容差/skip/ignore削弱。独立wheel额外覆盖CSV读取/匹配/应用API且普通导入不加载Qt/OCR，旧像素/worker/安装后OCR全部保持。最终完整日志ignored .local/requirements-review/T017-check-all.txt。新增解析失败Qt用例确认旧书/预览/草稿不变。

## 失败记录与修复

- 首次元信息用例4失败：递归model_dump使严格LaneROI成为dict。改为保留原字段对象后严格验证，预期未改，21通过；后续边界反例累计23。
- 新Qt测试首轮收集失败：仓库使用importlib模式，测试辅助导入须tests.test_project_measurements；修正导入，不改产品规则。Pyright的tifffile.imread宽重载改为TiffFile.asarray，无ignore。
- 首次实际用户Excel解析拒绝：6个嵌入TIFF使全包解压约59MB，实际表XML约54KB；仅对真正解析的XML计预算，完全忽略图像。新增33MiB嵌图与大重复合并区域反例，不提升单XML/格数预算。
- 首次完整门禁：1失败/332通过，112.17秒，退出1。test_close_during_batch_import_keeps_completed_rows期待1行，新增关闭早退误丢当前已接受原图。恢复原契约“完成当前行、停止后续”，保留代际拒绝，未改该测试或期望。13桌面组合复核通过。初始日志保留在.local/requirements-review/T017-check-all-initial.txt。
- 此轮未复现旧Qt原生Aborted；仍不能视为根因修复。
- 第二次完整门禁在约72项后停滞约3分钟，观察日志不再增长、专属pytest进程仍存活；确认PID15824/父38388为本次测试后停止，退出1，停滞日志保留T017-check-all-stalled.txt。带线程超时诊断的145仓库测试随后通过，未取得失败现场栈，根因UNKNOWN。检查新测试同步逻辑后将waitUntil纳入finally释放、guard超时改为受控ValueError而非无回复的AssertionError，不延长超时/改变成功断言；另加解析失败保留旧书/预览/草稿测试。最终全门禁启用PYTHONUNBUFFERED=1及仅打印栈的faulthandler_timeout=20，不改变通过标准；不能把后续通过当作根因修复。

## 实际材料只读探针

ignored脚本.local/requirements-review/probe_metadata.py导入用户项目2张TIFF并显示2缩略图，再读真实Excel：1表、50×49、190公式/错误标记，按表头第2行演示明确列选择得47条提议，0绑定/0勾选；未将订单号猜为图像身份，未应用元信息。预览前后草稿一致，保存重开行一致，Excel/原TIFF的SHA前后全部一致。私有工作区/输入/截图不提交。

报告.local/requirements-review/T017-user-metadata.json；源码Qt截图T017-metadata.png和T017-user-metadata.png已查看，字段/缩略图/可改提议可见。使用QWidget.grab与pytest-qt，无原生CUA；不是完整包态或真实实验准确率验收。实际表只作为结构/异常输入证据，不推断科学值。

## 仍待完成

独立审查未执行，作者自验不替代；未推送、PR/远程CI/main集成或发布。真实实验对应/批量体验、大项目性能、最终Windows包/干净机/DPI/物理FAT仍待验。T-018准备统一结果CSV/归档；ZIP导入、模板/横向分段/交互缩放、旧工具衔接等继续按首版核对表推进。完整Goal未完成。
