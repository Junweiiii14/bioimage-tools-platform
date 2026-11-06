# P021 最终增量独审：pass（本任务工程范围）

2026-11-06，独审窗口 `01a1af0d-808e-7131-ae29-237aded27938`（local）。PR73：https://github.com/Junweiiii14/bioimage-tools-platform/pull/73。

- reviewed base：`aa3302ad2980dfeec1ac6f7776fec6176f18fcda`
- reviewed candidate：`3f425b5ba5804b5d542980f3410ddda2d177c9cb`
- 首候选：`002743256fce89b6a2fb1fb32696138d1bf11a09`；R01修复祖先：`0f4cac55f98ebde0bccefa2de46ef11573cd06e8`。
- 独立树：`C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-review-p021`；自有 `.local/reviewer-venv`，Windows CPython 3.12.14。最终 tracked clean。未修改作者树、产品、模型、原图、历史成果或安装。

## 结论与范围

**pass**：固定核分割/BCA研究方法接入既有P009画布、模板保存与新输入复用、执行及已提交结果，在本任务工程范围内通过。原R01、R02及非阻断N01均关闭，没有剩余实质问题。不是任意跨实验图、插件装卸、Agent、科学准入、真人可用性或安装更新的完成声明。必需CI仍待终态，由规划窗口核对后决定正常PR集成。

首候选的 `changes_required` 报告保留在 `work/evidence/P-021/independent-review-0027432.md`，不改写历史失败。本次审查覆盖修复增量及受影响路径；未变的schema/科学调用/结果完整性和原生操作证据沿用首候选报告，未重复全部科学或界面矩阵。

## 问题关闭

| 编号 | 独立复验与结论 |
|---|---|
| P021-R01 / P2 | `nuclei_cli.py:28–32`、`bca_cli.py:28–30`先以公开API读取/验证输入，再创建工作区，传递已验证Input。0f4上的原回归1 passed / 1.04s、exit0；独立BCA摘要不匹配和确认字段错误均拒绝且无新工作区；有效输入字节、单位、位深/形状保留。最终head的9项回归再次包含原失败测试。关闭。 |
| P021-R02 / P2 | `web_ui/workflow_authoring.js:694–703, 739–750, 955–959`将两研究入口加入上下文动作，只在真实workspaceChanged时撤销就绪状态。最终head独立重放原两例失败输入：旧图隐藏、开始页显示、保存/运行禁用；点击禁用按钮不发起操作。dirty拒绝不打开对话框，保留旧图、工作区、标题、dirty状态及实际保存能力；BCA选CSV后取消板记录、核分割取消源选择均保留旧上下文。失败后重新打开原项目，文档ID及保存后的标题恢复。关闭。 |
| P021-N01 / P3 | `web_ui/index.html:66`首页已如实列出WB与固定核分割/BCA方法、模板及科学语义限制。关闭。 |

修复复用现有输入对象、workspaceChanged信号和上下文状态，未增加执行引擎、接口框架、依赖或重复算法。新增测试覆盖真实边界，未改弱原断言、容差、skip或门禁。

## 最终head实际检查

环境：上述独立venv；Qt测试设置 `QT_QPA_PLATFORM=offscreen`、`QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu`。GPU fallback/shared-image诊断保留，不将测试成功解释为物理GPU问题已解决。

1. `.local/reviewer-venv/Scripts/python.exe -I -B -m pytest -q tests/test_research_authoring.py tests/test_research_authoring_web.py tests/test_workflow_authoring_web.py::test_web_editor_saves_and_runs_actual_fixture tests/test_nuclei_ui.py::test_changed_source_rejected_before_workspace_creation`：**exit0，9 passed / 26.33s**。覆盖研究装配/模板、BCA真实运行、两个入口新增回归、WB三节点真实样例及原R01。日志 `.local/final-3f425b5-pytest.log`。
2. `.local/reviewer-venv/Scripts/python.exe -I -B -m pytest .local/ui-review/test_r02_context_recheck.py -q -s -p no:cacheprovider --basetemp .local/ui-review/r02-3f425b5-tmp`：**exit0，2 passed / 4.45s**。这是独立反例复验，未重复作者测试实现。证据 `.local/ui-review/receipt-r02-3f425b5.md`、`r02-new_bca-results.json`、`r02-new_nuclei-results.json`。
3. `.local/reviewer-venv/Scripts/python.exe -I -B .local/native-review/cold_read-3f425b5.py`：**exit0**。新进程未提供模型配置、未加载StarDist/TensorFlow，仍能校验并读取首候选原生运行的已提交46核成果；标签SHA仍为 `fc707624198066c884fd4c328802c71cf0a89376a99ac913c0df0194cc84299f`。旧运行与当前计划仅host_runtime_source版本不同，matches_run=false符合源码变化后的失效口径，不冒充当前代码重算。证据 `cold-result-3f425b5.json`、`cold-read-3f425b5.log`。
4. `.local/reviewer-venv/Scripts/python.exe -I -B tooling/rule_context.py check --base aa3302ad2980dfeec1ac6f7776fec6176f18fcda --head 3f425b5ba5804b5d542980f3410ddda2d177c9cb`：**exit0**。
5. `git diff --check 0f4cac55f98ebde0bccefa2de46ef11573cd06e8 3f425b5ba5804b5d542980f3410ddda2d177c9cb`：**exit0**。全PR原有P020历史报告EOF空行提示已在首审披露，未要求改历史文件或为此另开提交。
6. 直接核对完整base/head差异清单与R01/R02增量：无算法包、第三方本体/权重/冻结参考、依赖锁或门禁改动；本轮不新增包，不需要新增wheel隔离矩阵。原报告中的接口/来源核验继续适用。

冷读探针的初版曾在0f4上错误要求跨源码提交matches_run=true，exit1；原脚本及解释保留为 `.local/native-review/cold_read-initial.py`、`cold-read-initial-result.txt`。检查运行环境摘要规则后改为核对历史结果完整性、相同科学节点字段及仅host_runtime_source变化，最终head按上述命令通过；未改变产品、保存结果或原测试预期。

## 沿用证据与未验边界

首候选独立16项回归、21条schema/模板检查、BCA两次真实worker及完整性反例、1440×940原生窗口实际选择公开图并运行46核，详见原报告。R01独立证据 `.local/provenance-r1/receipt.json`。以上明确绑定原执行提交；最终UI修复未改变算法/执行器，不能把沿用证据写成最终head重跑的科学实验。

未在最终head执行本机全量；作者混合源码全量exit1 / 1770 passed、唯一旧R01，仅作诊断，既不遮盖失败也不转写成准确候选通过。第二张18核、主题/960宽度为作者证据；本次未重复原生大链、未新测内存/性能、真人、OS IME/物理DPI、目标机或安装。科学/化学准确性、LoQ、训练重叠及患者独立性继续保留。

最终读取PR73时head/base与本报告一致、OPEN/DRAFT；rules-context和desktop-environment成功，Windows/Ubuntu foundation仍IN_PROGRESS，native-case为SKIPPED。**不宣称全部CI通过。** 上游负责等准确候选必需CI终态、正常集成、记录main和交付状态及释放开发树；本窗口不合并、不发布、不替作者释放树。归档此报告后若仅增加收据，核对纯证据diff即可，无需重复科学链。
