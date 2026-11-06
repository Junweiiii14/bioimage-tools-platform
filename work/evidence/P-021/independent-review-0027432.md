# P021 初审：changes_required

2026-11-06，独审窗口 `01a1af0d-808e-7131-ae29-237aded27938`（local）。绑定 PR73，base `aa3302ad2980dfeec1ac6f7776fec6176f18fcda`，candidate `002743256fce89b6a2fb1fb32696138d1bf11a09`。

独立树 `C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-review-p021`，独立 `.local/reviewer-venv`，`uv sync --locked --all-groups --offline` exit0。未改作者树、共享环境、产品文件、原图或旧安装。受审范围为固定核分割/BCA方法接入既有 P009 画布、模板、新输入、执行及结果，未扩为任意跨实验图、装卸或 Agent。

## 阻断问题

**P021-R01 / P2：源准入失败前已经创建工作区。** `apps/desktop/src/bioimage_app/nuclei_cli.py:25–39` 与 `bca_cli.py:27–35` 提取输入复用时，将 read/expected SHA 或板记录校验移至 Workspace.create 后。已选核图字节变化或 BCA 板记录错配被拒绝时，仍留下新工作区，破坏既有“失败不建项目”的承诺。

该问题由作者全量失败先定位，独审直接核源并单独执行原 `tests/test_nuclei_ui.py::test_changed_source_rejected_before_workspace_creation`：exit1，1 failed / 1.36s，失败在第165行 `assert not workspace.exists()`。不能归因于 GPU，也不能修改原断言。最小修复：公开 API 先读取并校验，之后创建工作区，将已验证 Input 传给导入复用，保持摘要校验。修复 `0f4cac55…` 已提供，另行绑定复审，不改写本候选失败事实。

**P021-R02 / P2：初始化失败后新空工作区仍显示旧图可运行。** `web_ui/workflow_authoring.js:694–696` 的上下文动作列表遗漏 new_bca/new_nuclei，相关错误处理在:737。真实 WebChannel 复现：先创建有效 WB 三节点图，再选 BCA 合成 CSV+无字段记录 `{}`，或核分割 uint16 TIFF。准入正确拒绝，宿主却已切新工作区且 projection=null；页面仍显示旧 WB 图/来源/“最近保存的流程通过预检”，保存和运行启用。再次运行得到旧 document ID 不存在。未发现原工作区或原图损坏，不扩称数据损坏。

最小修复：实际 workspace/session 已切换后的初始化失败撤销旧就绪状态；在切换前因 dirty 拒绝或文件选择取消时保留旧草稿及保存能力。复用现有 workspaceChanged 足以区分，无需新框架。两例独立命令 `.local/reviewer-venv/Scripts/python.exe -I -B -m pytest .local/ui-review/test_context_failure.py -q -s -p no:cacheprovider --basetemp .local/ui-review/context-tmp`：exit0，2 passed / 4.44s（断言观察到的缺陷）。证据 `.local/ui-review/new_bca-failure.json`、`new_nuclei-failure.json`、`receipt-0027432.md`。0f4cac55 的 UI 未变，此发现同样适用其未修改部分。

非阻断 P021-N01/P3：`web_ui/index.html:66` 首页仍称 BCA/核分割尚未接入画布，与本次入口不符；可随实质修复更正文案，不另开循环。

## 已独立验证

1. 既有研究、编辑、会话及 WB 真实样例：`uv run --locked --no-sync python -I -B -m pytest -q tests/test_research_authoring.py tests/test_research_authoring_web.py tests/test_workflow_authoring_store.py tests/test_workflow_authoring_bridge.py tests/test_workflow_authoring_session.py tests/test_workflow_authoring_web.py::test_web_editor_saves_and_runs_actual_fixture`，exit0，**16 passed / 85.45s**。独立 venv，Windows CPython3.12.14，offscreen Qt / --disable-gpu。该成功不能覆盖 R01 原失败。
2. 独立 schema/模板脚本 exit0 / 6.73s，共21条检查记录：schema1只读不改写，显式save/bind升v2并保留旧资产；新输入核图SHA/shape、BCA CSV+record正确替换；模板冷读和新项目复用、覆盖原模板拒绝；方法/模块版本及执行路径参数注入拒绝；Bridge捕获配置后，后续QSettings修改不改变已创建宿主配置。未启动科学worker。证据 `.local/schema-template-review/run-0e8ea4d257/receipt.json`、`check_bindings.py`。
3. 独立 BCA 两次真实 WorkflowAuthoringSession/worker运行 exit0：均 completed_with_issues，4个partial均值为空；同项目绑定新输入后旧成果matches_run=false且旧字节不变，新执行不复用旧缓存。新进程冷读exit0；选择samples但破坏未选wells、破坏真实run.request两例均IntegrityError/exit2。证据 `.local/provenance-review/receipt.json`、`probe.py`，损坏只施加在独立合成副本，不修补以掩盖失败。
4. 原生 Windows 独立窗口实际点击首页→编排→核分割入口，用原生文件对话框选公开 Ganglioneuroblastoma_10.tif 与本树独立输出目录，看到固定方法目录/单节点/真实端口/原始输入/预检；点击运行，通过真实既有StarDist worker得到 completed，页面显示46核与原坐标uint32标签叠加。标签SHA `fc707624198066c884fd4c328802c71cf0a89376a99ac913c0df0194cc84299f`，与P015已见图参考一致。没有 mock 计算/执行/提交。
5. 原生启动使用本树独立宿主venv、QSettings和Documents根；模型worker为已有 `p015-research/worker-env/Scripts/python.exe`，固定模型为 `p014-research/models/2D_versatile_fluo`，仅调用未升级。记录 `.local/ui_review_launcher.py`、`.local/native-review/authoring-events.ndjson`、`native-result.json`。项目 `工作流-20261106-194316-0c1bbf`、document `b133bbe625d74831b6474a781aeabe52`，窗口1440×940。GPU fallback日志保留，不解释为已修复物理GPU问题。原生BCA选择路径未重复，真实BCA编辑/模板/运行由上述WebChannel测试和独立反例覆盖。
6. 结果读取复用同一冻结执行/请求/完整资产校验，公开API负责科学输入与展示。固定算法整体作为节点，未复制算法公式或新建执行引擎。算法、公共包、锁、门禁、冻结参考保护路径零diff；21条模板检查不等于科学准入。
7. 准确 base/head rule_context check exit0。`git diff --check base head` exit1，唯一提示是随P020收尾归档的旧独审报告第55行 EOF 新空行；这是文档空白非产品阻断，未为此改历史证据或要求单独提交。tracked 干净。

## 未验及回传

不宣称全部CI、本机全量或科学验收通过；作者全量已有真实失败，修复后须新head必需CI。未重复未变科学/主题/性能全矩阵；第二张18核及作者各主题960截图是作者证据，不冒称本主审重拍/重跑。科学准确性、LoQ、训练重叠/患者独立性、真人/OS IME/物理DPI/目标机/安装仍未验；本轮真实46核只证明工程调用与既有参考一致。

R01、R02及非阻断文案均已回传规划窗口，由原开发窗口集中修复。本报告保留0027432结论；新head只增量复审修复和受影响路径，未变证据可沿用。审查者不合并/发布或释放作者树，报告由上游一次归档，不为纯收据另推产品提交。
