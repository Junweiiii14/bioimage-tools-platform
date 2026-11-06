# P023 独立审查回传

2026-11-06 · 审查窗口 `01a1af0d-808e-7131-ae29-237aded27938` · **结论：pass，本机独立目录候选范围通过；必需 CI 尚未全部完成。**

- PR：<https://github.com/Junweiiii14/bioimage-tools-platform/pull/75>
- Base：`b13e71aa5aaebe91edecde44f386fc20ef693b19`
- Candidate：`5dbfb394763227cb9a0befc1e28fd5a5c11a3334`
- 独立 detached 检出：`C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-review-p023`；tracked clean。
- 原作者继续持有 `bioimage-plan-sync/codex/p023-local-candidate`；本审查未修改产品、原作者环境或 tracked 文件，未合并、发布或释放共享树。
- 任务：`work/tasks/P-023-local-candidate.md`；按 `docs/plans/independent-review.md` 审准确增量及交付承诺。研究算法、方法参数和科学矩阵未变化，不重跑未变矩阵。

## 审查对象与结论依据

冻结工件：`C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-plan-sync/.local/releases/runtime-5dbfb3947632-acceptance-p023-local/app`，入口 `BioImageWB-Acceptance.exe`，版本 `0.14.0`，通道 `wb-acceptance-p023-local`，设置命名空间 `Acceptance-p023-local`。

独立核验 7,900 个 payload 文件，506 个 Git archive 文件及 308 个已安装源码/资源；六个实际 wheel 的字节摘要与旧 `969347929eefabe1d23009f653846d58ef899a05` 工件、双方 manifest 均一致。私有解释器及 sys.path 全部位于该候选内，六产品 distribution 齐全；宿主候选不混入 StarDist/TensorFlow/csbdeep，固定核 worker/模型仍外置。

额外进行六个受管包的双向集合核对：共 509 个文件，等于 308 项 Git 源码/资源、200 个有对应 Git Python 源文件的缓存、1 个已验证版本/完整 SHA/通道的 build-identity.json；未知额外源码/资源、缺失、symlink/junction 均为 0。全 payload 中另有 1,006 个运行生成缓存，明确不认证其字节，不把缓存摘要等同源码摘要。

主审以真实最终 EXE 从仓库外启动，无开发 PYTHONPATH、调试端口或离屏环境覆盖，观察到正确标题及 WB、核分割、BCA 三入口。首次截图时窗口最小化，按工具提示激活并刷新后成功；未据失败截图判断界面。正常 Alt+F4 关闭，持有原进程句柄得到 **exit 0**，随后窗口消失；HKCU `Software/BioImageTools` 的全部设置前后哈希一致，changed_settings_keys 为空。记录中的 211.748 秒包含人工观察等待，不是启动时延测量。

旧 `9693479` 的三工具真实 worker、正式结果、冷重开、模板换新输入、设置跨重启和三次正常退出属于**作者证据**。子审只读复核 40 个现存资产/结果的 SHA 全部一致及 8 个成功 worker 正式记录；旧提交到本候选的六包源码/资源、锁、运行时核验器及原生启动器未变，实际六 wheel 亦完全相同，因此限定沿用其功能证据。此次最终目录完整性与原生启动/关闭是独立实测；未将旧 worker 运行改称新 SHA 独立执行。

## 冻结摘要

以下 SHA256 在最终 EXE 执行前匹配，正常退出后再次核对仍一致：

| 文件 | SHA256 |
|---|---|
| build-manifest.json | af8dc3fb8868a3a57528e3417d56a50d673b804e6663f4e0b86243a7920877fb |
| payload-files.json | ac0f02e299d7b9e3cd53868c92de6f7ea7e0b90bb9d2c03304bfea60306a5ab6 |
| BioImageWB-Acceptance.exe | b112d76395588e438e09bfff5408359d2e7d45e520ceb35880e6fa0ad81a4a30 |
| source-code.zip | abb62ddccc8065cf0ea10d16cfba14eb67c86ba91917bf4f85f9dbc819dd4274 |

## 检查与证据

环境：Windows x64，独立 Python 3.12.14，解释器 `.local/reviewer-venv/Scripts/python.exe`。离线锁定同步 `uv sync --locked --all-groups --offline`，exit 0；所有 editable 指向审查树。以下路径均相对该独立审查树。

| 命令或检查 | 真实结果与证据 |
|---|---|
| `python.exe -I -B -m pytest -q tests/test_runtime_integrity.py tests/test_candidate_acceptance.py` | exit 0，49 passed / 38.65 秒；`.local/p023-packaging-tests.log`；测试使用既有 Windows 离屏 Qt 设置，未声称物理 GPU 验证 |
| `python.exe -I -B .local/verify_p023_artifact.py` | exit 0；最终摘要、7,900 payload、506 archive、308 installed resources、六 wheel 实字节相同、私有运行时及身份；`.local/final-artifact-audit.json` |
| `python.exe -I -B .local/launch_final_candidate.py` + Computer Use 原生观察/正常关闭 | exit 0；原进程 PID 45788，stdout/stderr 记录与设置摘要均在 `.local/native-review/`；`window-observation.json` 与 `exit.json` |
| `python.exe -B .local/boundary-review/check_build_boundaries.py` | exit 0 / 8.52 秒；7 个参数边界探针、六 wheel/三 extras/摘要约束/目录模式先于 Inno 返回；`.local/boundary-review/build-boundaries.json` |
| `python.exe -I -B .local/provenance-review/probe.py` | exit 0；Markdown 纯 CRLF 等价被记录；payload 字节变化、正文变化、BCA 代码变化、核源码缺失、3 个越界路径均拒绝；额外源码反例见 N01；`receipt.json` |
| `python.exe -I -B .local/provenance-review/audit_actual_files.py` | exit 0；实际六包双向文件集合、身份与缓存来源；`actual-candidate-file-set.json` |
| `python.exe -I -B .local/ui-review/check_evidence.py` | 最终 exit 0 / 0.34 秒；40 文件及作者 worker/重开/设置证据一致；`evidence-receipt.json`、`receipt-5dbfb39.md` |
| `python.exe -B -m tooling.rule_context check --base b13e71aa5aaebe91edecde44f386fc20ef693b19 --head 5dbfb394763227cb9a0befc1e28fd5a5c11a3334` | exit 0，回执匹配实际 base、scope 与规则版本 |
| `git diff --check <base> <candidate>` | exit 0；最终 `git status --porcelain=v1` 为空 |

UI 证据探针首次 exit 1 是审查脚本错误要求即时 BCA 捕获含运行身份；README 已披露即时捕获，后续 reopen-identities 才含完整身份。首稿、失败说明已保留于 `.local/ui-review/check_evidence-first-attempt.py` 和 `first-attempt.txt`，未修改作者证据或降低产品预期。

本次 uv-build 仍为 `0.13.6`。子审通过[官方 PyPI 元数据](https://pypi.org/pypi/uv-build/0.13.6/json)及实际下载的 Windows x64 wheel 独立核对 1,188,395 字节，SHA256 `2a2350fbea9a3cf578481b5efc2d333f0477f26696aa615d312866acd170acf6` 与新增约束一致；未安装或执行所下载 wheel。算法、权重/冻结参考、产品公开契约、uv.lock、固定原生工具链与门禁未更改；未发现本增量引入多余产品抽象或重复业务规则。

## N01：来源核验器单向集合覆盖不足（非阻断）

位置：`tooling/candidate_acceptance.py:143–166`。verify_source 逐一检查 Git 已知源码，却不枚举受管产品包的额外源码；独立合成目录加入 `bca_tool/untracked_helper.py` 并按构建流程重新冻结 payload，verify_payload 和 verify_source 均通过。此单向逻辑在原四包版本已有，不是本次 CRLF 放宽引入。

这表明通用核验器不能单独证明“没有额外源码”，**不证明本候选存在污染**。支持的构建路径从 clean commit、全新空 runtime site 和固定后端/摘要 wheel 开始；本审又实查六包集合，未知额外文件为 0。因此 N01 不阻断 P023 当前本机候选交付，不以合成反例扩大为未发生的损坏。

后续若改进该核验器，最小处理为核对六包实际文件集合与 Git 派生集合，仅明确允许并单独核验构建身份及缓存例外；以已存在的额外源码反例验证。无需新增框架、科学矩阵或在本候选上重跑全部历史流程。建议由上游保留此项，随直接相关任务处理。

## CI、未验边界及上游下一步

GitHub 查询确认 PR75 的 base/head 与本文完全一致。quality run `42233985746` 中 desktop-environment 成功、Windows/Linux foundation 均仍在 `dev.py check --all`；rules-context run `42233985802` 成功。**本文不是全部必需 CI 通过的声明。**

未执行安装器，未替换旧安装/快捷方式/关联，未签名、发布、下载大模型或执行新科学矩阵。独审未重新构建整套发行目录；核对的是冻结作者工件。未验干净 Windows、真人操作、物理 DPI/GPU、科学适用性、峰值内存及冷缓存时延。README 的体量为明确标注的旧基线实测，不把源码或权重体量当完整依赖体量。P022 Linux 收尾挂起和更早原生问题 UNKNOWN 原样保留，当前一次正常退出不证明根因消失。

回传上游后，由上游核对准确 SHA 的必需 CI，再按已有授权正常 PR 集成、核对集成内容、归档本回执及最小证据、向原作者确认共享树释放，之后派发新任务。任何相关实现变化须复审该增量。本文通过不等于科学准入、用户安装更新或公开发布授权。
