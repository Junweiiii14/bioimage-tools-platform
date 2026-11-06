# P020 增量独立审查：pass

2026-11-06，审查窗口 `01a1af0d-808e-7131-ae29-237aded27938`（local）。本次工程 MVP 范围通过，无剩余已确认阻断；待准确候选必需 CI，由规划安排集成。

- PR：<https://github.com/Junweiiii14/bioimage-tools-platform/pull/72>
- PR base：`1c819aeaae9813fdc29606cbad463b08a191fbab`
- 初审候选：`3056334e15dca4ea70fc9929b65761e214692136`
- 本次准确候选：`c9a4d4247242c7212a28b6653ca5cba7c292cdc8`
- 直接审查增量：`3056334..c9a4d42`，12 文件。初审完整报告仍为 `.local/independent-review-3056334.md`，保留原 changes_required，不倒改历史结论。
- 独立检出与 venv：`C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-review-p020`、其 `.local/reviewer-venv`。原生审查窗口已正常退出 exit 0 后，才将本审查者独立树切到新准确提交；无 tracked 修改、无作者树/安装版/模型操作。

## 问题闭环

| 编号 | 结果 | 独立复验证据 |
|---|---|---|
| P020-R01 / P2，身份被翻译冲突 | 关闭 | 复用初审未改的双 ID CSV 与明确记录，经真实 WebChannel→worker→核验提交→页面，blank 与 空白保持不同；样本和逐孔表全部 117 个身份单元格等于底层原值，role/status/reason 仍本地化。run `da31d4be58dd491893564ca8fee1091b` |
| P020-R02 / P2，帮助链接导致空白 | 关闭 | 两个新建实际 NucleiBridge.help() 窗口分别鼠标点击模型与 P014 来源；使用 QDesktopServices.setUrlHandler 捕获真实 openUrl 分派，没有替换被测 API。精确得到预期 HTTPS URL，正文两次均 1012→1012 字符且全文/摘要相同、source 保持空。file/http 锚点不分派，也未启动分析任务 |
| P020-N01 / P3，占用时静默返回 | 关闭 | 使用已有 unavailable 回调表示其他工具占用，点击开始显示“请等待当前任务完成，或先取消运行。”；不启动 session、保留既有结果。没有为测试另开第二个真实 worker |

R01/P3：`.local/plugin-review-p020/test_r1_frontend.py`、`r1-receipt.md`、`r1-frontend-results.json`；独立 `python -I -B -m pytest ... -q -s -p no:cacheprovider --basetemp .local/plugin-review-p020/r1-tmp`，exit 0，1 passed / 3.59s。旧输入与旧反例未覆盖。

R02：`.local/p020-r02-c9a4d42/help-links.json`，独立复现 exit 0。此补充探针只读复用 `bioimage-plan-sync/.venv/Scripts/python.exe`，显式加载本审查树的 `nuclei_bridge.py`（回执记录实际 implementation 路径），未同步共享环境或启动 worker；不将其称为独立安装测试。下述主审 17 项则全部在本审查树独立 venv 中运行，包含帮助链接回归。固定基线 `1c819ae…` 的来源文件确实存在且是有效 JSON，blob `126da8bfb7c4a2223ddd088fb43fda18be02240c`。本复验确认桌面 URL 分派契约，不宣称实际启动 OS 默认浏览器、联网下载或模型安装成功。

## 增量与验证

- 修复仅调整枚举展示、固定文档外链处理和复用已有占用提示，职责与控制流清楚；未发现需要新增公共抽象或额外校验框架的理由。未改上游算法、权重、方法版本、科学参数、公开契约或依赖。
- `tests/test_platform_home_scroll.py` 唯一变更为 installed-tool 数量 `1→3`，与已独立观察的三工具卡片一致；WB 草稿、背景刷新不跳转和导航断言均保留。没有改超时、容差、skip/xfail、类型忽略或门禁。BCA 测试保留原 S1/LOW 场景并追加冲突 ID 场景，仍验证真实运行、导出、新进程重开和损坏拒绝。
- 独立定向命令：`uv run --locked --no-sync python -m pytest -q tests/test_bca_web.py tests/test_bca_ui.py tests/test_nuclei_ui.py tests/test_platform_home_scroll.py`，**exit 0，17 passed in 15.16s**。Windows / CPython 3.12.14，独立 venv，offscreen Qt / `QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu`。
- `python -m tooling.rule_context check --base 1c819aeaae9813fdc29606cbad463b08a191fbab --head c9a4d4247242c7212a28b6653ca5cba7c292cdc8`：exit 0。
- `git diff --check 3056334… c9a4d42…`：exit 0。
- 相同增量对 tools/bca/src、tools/nuclei/src、tools/wb/src、packages、pyproject.toml、uv.lock、.importlinter、.gitattributes、.github、tooling、.agents、work/evidence/P-018 执行 `git diff --exit-code`：exit 0，无差异；与初审保护证据相接。
- 已核作者 review-fixes.md 如实保留失败与中止记录。旧全量 check 中止 exit 1 不计通过；本独审未重跑不受影响的全量测试或科学/视觉矩阵。
- `gh pr view 72` 核对 head/base 均与本报告一致；检查时 PR draft/open，rules-context、desktop-environment SUCCESS，两项 foundation IN_PROGRESS，native-case SKIPPED。不把独审通过写为全部 CI 通过。

## 适用范围与回传

初审 35 项定向、原生 BCA 导入/显式记录/真实核验提交，以及首页→真实 P009 三节点合成 WB 流程运行/提交的未变链证据继续适用；原生图与作者主题截图仍标其原始候选，不冒称已为新候选重拍。相关身份与帮助行为以本次新证据为准。

本结论是三工具统一工作台/BCA 桌面工程 MVP 的范围通过，不代表 BCA/核分割节点已注册、完整插件卸载/跨实验编排完成，亦不等于科学准确性/LoQ、真人体验、OS IME、物理 DPI、目标机、发布安装或用户旧安装更新验收。

向规划窗口回传准确候选 pass 和上述限制。原开发窗口保持共享树所有权直到规划安排集成与释放；审查者未合并、发布或改写作者代码。完整必需 CI 通过后才能按既有流程集成；若候选再发生实质变更，核对实际增量。报告可由上游一次归档到 P020 证据，不为纯收据要求新的产品提交或重复全量循环。
