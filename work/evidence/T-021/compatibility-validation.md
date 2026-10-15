# T-021 旧格式与科学身份兼容性验证

日期：2026-10-15（Asia/Shanghai）。执行者：compatibility 子代理，独立工作树
`C:/Users/70236/.codex/worktrees/t021-compatibility/bioimage-tools-platform`，
分支 `codex/t021-compatibility`，被测实现基线 `82d673ac98920e9f5ebf7216ee12d96677065165`。
本提交只增加测试及此证据，不修改实现、API、已有测试或门禁。

## 独立旧实现预期

以 `git worktree add --detach C:/Users/70236/.codex/worktrees/t021-legacy-golden/bioimage-tools-platform bb5601a`
建立 T-021 之前的独立工作树，退出 0。使用当前工作树独立 `.venv/Scripts/python.exe`
和锁定依赖，但在新 Python 进程 `sys.path` 首位放置旧工作树的 `tools/wb/src`
及旧仓库根；实际 `wb_tool.__file__` 确认来自 `t021-legacy-golden`。

旧进程通过 `runpy.run_path` 加载新增测试文件中的 `legacy_project` 样例构造器，
只调用旧版公开 `read_figure_project/render_figure/export_figure_bundle`。
分别生成 schema 1–6 的 project.json、manifest.json、baseline.zip。
样例仅含合成 uint16 TIFF、重复蛋白名、不同 Fig 宽度、空泳道及缺图行；
v4+ 保存未识别的明确 OCR 输入，v6 保存确定性空 ZIP 作为不递归解包的历史资产。
科学计算配置/历史运行在这六个小样例中为空，带完整状态的迁移另见下表。

旧基线实际输出均为 356×166 RGB，像素 SHA256 为
`85df49a9cc54a89ba012b1f9b9fc87096fdb3016efb32c248fb5a99c044820a6`。
六个完整 manifest SHA256 固定在新增测试 `LEGACY_MANIFEST_SHA256`，包含旧项目字段、
坐标、原图摘要和显示映射，未删字段或修改容差；新实现不能重新生成这些预期。

旧进程生成后，另一个使用新实现的 Python 进程逐一读取这些实际旧 ZIP，执行
`inspect_project_archive` 和 `stage_project_archive`；从 staging 原图重新渲染，
完整 manifest 与旧文件逐字节比较，RGB 摘要与上述旧实现相同。
生成脚本及检查脚本本次退出均为 0，合成运行产物留在本工作树 `.local/legacy-fixtures/`，
不提交生成 ZIP 或私有样本。

复现不需要固定绝对临时路径：独立载入旧工作树公开 API 后，对版本 1–6 调用
新增测试的 `legacy_project(location, version)`，保存旧 `model_dump_json()`、
`render_figure(...).manifest_json` 和 `export_figure_bundle(...)`；切回新 API 对
同一 ZIP 检查/stage，并用 staged.assets 提供的 SHA/path 重渲染及逐字节对照。
版本、解释器及依赖必须与本次锁版本一致，字体像素摘要不能跨字体版本任意重录。

## 兼容矩阵

| 输入 | 读取/JSON保存重开 | 显示兼容 | ZIP证据 | 结果 |
|---|---|---|---|---|
| schema1 | 保持原类型/版本/字段 | 旧完整像素和manifest golden | 实际旧ZIP检查/stage；新ZIP检查/stage | 通过 |
| schema2 | 同上，建议字段保留 | 同上 | 同上 | 通过 |
| schema3 | 同上，定量字段保留 | 同上 | 同上 | 通过 |
| schema4 | 同上，OCR输入状态保留 | 同上 | 同上 | 通过 |
| schema5 | 同上，归一化字段保留 | 同上 | 同上 | 通过 |
| schema6 | 同上，历史来源保留 | 同上 | 同上，历史ZIP仍作为原字节资产 | 通过 |
| schema3已完成测量→schema7 | 原row/ROI/请求/run原样保存，旧读取器明确拒绝7 | 明确拆成两段不改定量身份 | 独立JSON文件保存重开 | 通过 |
| schema5完整状态→schema7→ZIP恢复 | OCR明确绑定/确认、归一化配置、当前请求和run均保持 | 恢复前后RGB完全相同 | 3条历史运行、结果资产重新核验 | 通过 |
| 未来8/99或布尔/字符串版本 | 明确拒绝 | 不渲染 | 不伪造成功 | 通过 |

保存旧格式时断言未添加 `composition/layout_style`，没有静默迁移旧manifest。
schema7测量例包含解析已知信号4000、8000、16000、真实0、排除空值及缺图空值；
显示改序/分段后逐个比较全部科学字段与状态。
ZIP恢复例使用已有合成真实像素积分及明确OCR/归一化配置，不宣称执行了真实OCR模型推理。
恢复后从暂存请求/结果资产重新构建 LoadedProjectResult，逐格比较；原始run身份保留，
同时明确标记“归档历史证据”及实际ZIP SHA，避免把外来运行称为本机观察。

## 实际命令与退出码

环境：Windows，CPython3.12.14，uv0.13.0；独立 `uv sync --locked --all-groups` 退出0。
Pillow12.3.0、NumPy2.5.4、tifffile2026.9.20、Pydantic2.14.1、pytest9.1.1、
Ruff0.17.0、Pyright1.1.414，未改锁文件。

| 命令 | 退出码/结果 |
|---|---|
| `uv sync --locked --all-groups` | 0 |
| `uv run --locked --no-sync python dev.py context --task T-021 --scope tools/wb/tests --scope work --record` | 0；回执由主代理统一提交 |
| `uv run --locked --no-sync python .local/generate_legacy.py` | 0；旧实现独立生成六版本golden及ZIP |
| `uv run --locked --no-sync python .local/check_legacy.py` | 0；新实现接受六个真实旧ZIP并保持manifest/RGB |
| 首次新增测试 | 1；10通过、1失败，原因见下 |
| 同一失败单测 `-vv`诊断 | 1；仅来源展示标签差异，未修改实现 |
| 新增12项测试单独运行 | 0；12通过 |
| 初次ruff检查 | 1；新增行101字符，随后仅格式化修正 |
| `uv run --locked --no-sync pytest tools/wb/tests/test_laboratory_compatibility.py tools/wb/tests/test_laboratory_layout.py tools/wb/tests/test_archive_restore.py tools/wb/tests/test_project_analysis.py -q` | 0；73通过，6.92秒 |
| `uv run --locked --no-sync ruff check tools/wb/tests/test_laboratory_compatibility.py` | 0 |
| `uv run --locked --no-sync ruff format --check tools/wb/tests/test_laboratory_compatibility.py` | 0 |
| `uv run --locked --no-sync pyright tools/wb/tests/test_laboratory_compatibility.py` | 0；0错误/警告 |

首次测量测试把 schema3 与7的完整表格对象直接相等，失败源为既有schema6规则：
旧schema3的来源展示列为空，继承历史证据支持的schema7明确显示“本机运行”。
修正测试先独立断言来源标签正确，再只规范化该显示标签并逐格比较所有其他字段；
ZIP恢复同样先核对归档来源与SHA，再比较科学值/状态/身份，没有放宽数值容差或忽略失败。

本轮未发现需修改产品实现的兼容缺陷。以上不是所有历史用户项目覆盖证明，
未运行GUI/模型识别/完整产品门禁/独立wheel/独立代码审查；由主代理在整合提交上执行所需检查。
