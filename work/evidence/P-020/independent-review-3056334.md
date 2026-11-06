# P020 独立审查：changes_required

审查窗口：01a1af0d-808e-7131-ae29-237aded27938（local），2026-11-06。依据 docs/plans/independent-review.md，按本次工程 MVP 范围审查。此报告不表示科学准入、真人体验或安装验收通过。

- Base：`1c819aeaae9813fdc29606cbad463b08a191fbab`
- Candidate：`3056334e15dca4ea70fc9929b65761e214692136`
- PR：<https://github.com/Junweiiii14/bioimage-tools-platform/pull/72>（检查时 OPEN / draft，head 与本报告一致）
- 独立检出：`C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-review-p020`
- 独立环境：该树 `.local/reviewer-venv`；`UV_PROJECT_ENVIRONMENT` 指向该环境，`uv sync --locked --all-groups --offline` exit 0。未修改作者共享树、旧 dirty 树、安装版或模型。
- 范围：三工具工作台、BCA 明确记录→真实 worker→核验结果→展示/导出/重开、核分割准备帮助、P009 编排入口、会话与旧项目保护、自研增量简洁性及上游保护。不追加全插件卸载矩阵、BCA/核分割节点注册、Agent 或交付安装。

## 必须修复

### P020-R01 / P2：结果表翻译样本标识，制造身份冲突

位置：`apps/desktop/src/bioimage_app/web_ui/bca.js:102`，同一渲染函数用于样本和逐孔表。

`meanings[value] || value` 对所有非数值列生效，因而用户自定义的 sample_id、plate_id、technical_replicate 也被当作枚举翻译。合法不同样本 `blank` 与 `空白` 均显示为“空白”；一个有效研究估计与另一个 partial 结果会显示同一身份。tooltip 保留原值不能消除主表身份错误。

独立最小复现：仅将合成 CSV 的 S1 改为 blank、LOW 改为空白，并更新板记录摘要；经真实 WebChannel→worker→已核验提交，底层样本 ID 为 `[blank, 空白, HIGH, NEGATIVE, PARTIAL]`，页面为 `[空白, 空白, HIGH, NEGATIVE, PARTIAL]`。run `a1bd5c4466d94f6095d145ecef3d35a1`。

最小整改及复审：仅对 role/status/reason 等明确枚举列本地化；身份字段逐字保留。用上述两个 ID 验证样本及逐孔表，保留既有状态原因翻译。无需改变算法或新增框架。

证据：`.local/plugin-review-p020/test_frontend_edges.py`、`identity-results.json`、`receipt.md`；完整合成输入及提交项目保留于该目录。观察缺陷的探针 exit 0 / 1 passed（断言当前缺陷，不是假称正确行为）。首次探针因 Qt 直接数组回调转换失败 exit 1，改为 JSON.stringify 后复跑；产品和科学预期未改。

### P020-R02 / P2：准备指南链接点击后清空帮助，无法完成来源访问

位置：`apps/desktop/src/bioimage_app/nuclei_bridge.py:85–93`；`web_ui/nuclei_setup.md:17`。

实际帮助创建 QTextBrowser 后仅 setMarkdown；openExternalLinks=False，无锚点处理。分别在全新 NucleiBridge.help() 对话框中点击模型下载、P014 来源链接，均从 998 字符变为空白：HTTPS 被内部导航且未打开浏览器，相对链接没有可解析的 base。首次配置用户不能用指南访问所需来源，并丢失说明。

最小整改及复审：固定 HTTPS 链接交由系统浏览器处理；来源链接改为实际帮助环境可解析的地址。各验证一次链接点击与帮助文本保持即可，不改变模型或安装环境。独立 offscreen QTest 证据 `.local/p020-doc-visual-review/help-links-fresh.json`，exit 0；较早的连续导航探针另存，最终结论采用两个全新窗口的结果。

## 非阻断建议

P020-N01 / P3：`bca_bridge.py:169–170` 在其他工具占用时静默 return；`bca.js:123` 的开始按钮仍亮，原消息仍提示可以开始，但没有 session 启动。可复用 choose 已有的等待/取消提示，无需新增全局状态框架。证据 `frontend-edge-results.json`。没有错误计算，不另开整改循环。

## 独立验证与证据界限

1. 独立定向命令：`uv run --locked --no-sync pytest -q tests/test_bca_web.py tests/test_bca_ui.py tests/test_project_navigation_session.py tests/test_workflow_authoring_web.py tests/test_nuclei_web.py tests/test_nuclei_ui.py tests/test_bca_host.py tests/test_wb_student_results.py`；exit 0，**35 passed in 110.03s**。环境 Windows / CPython 3.12.14 / offscreen Qt / `QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu`。运行保留 Chromium GPU mailbox 警告，不据此宣称所有 GPU 环境通过。包括真实 BCA 提交、导出、新进程 read_result 重开、损坏拒绝及会话回归；这些是独立运行已有测试，不标为原生手工导出操作。
2. 独立最小反例 exit 0：板记录摘要不符在创建项目前拒绝；已选 CSV 后续改变报 source_digest/failed，无项目结果；初始化立即取消落盘 cancelled，attempts=0/results=0。证据 `.local/bridge-review-799c27ea/receipt.json`。未发生成功伪装或旧结果覆盖。
3. 独立前端反例 exit 0：后台刷新保留中文值与焦点、换 CSV 撤销三个明确确认、加载记录摘要不会被新 CSV 自动覆盖、摘要错配被真实 WebChannel 拒绝。合成 composition 事件不冒充操作系统 IME 实测。
4. 原生可视桌面：独立窗口 `P020 Independent Review - 3056334`，1440×940；使用原生文件对话框选择仓库合成 CSV 和显式 record.json，真实 worker 运行至已保存并核验；S1 显示约 5008.681 µg/mL，四个受限样本汇总留空并注明 partial。通过滚动查看、返回首页；首页工作流入口打开真实 P009 编辑器，说明目前支持 WB，创建三节点合成流程成功。启动器和事件记录见 `.local/ui_review_launcher.py`、`.local/ui-review/bca-events.ndjson`。仅将 Documents 输出根重定向到本树 `.local/ui-review/documents`，QSettings 也独立；没有 mock 计算、提交或科学状态。未操作作者 GUI 或旧安装。
5. 原生画布追加验证：点击运行合成流程，页面报告 triangle_u16 已完成；落盘 verify/analyze/publish 三个节点均 publication=committed、quality=complete。证据 `.local/ui-review/workflow-commits.json`；项目为该目录下 `工作流-20261106-181132-eead82`。未据此扩称完成本轮未变的所有编排操作。
6. 静态核验：复用已有 WorkflowSession 与 P019 verified_outputs；成功消息在完整提交后读取核验，导出重新核验来源并使用新目录。没有新增通用算法框架；算法 src、公共 packages、依赖/锁、边界检查、固定 skills、P018 冻结参考无 diff，专项 `git diff --exit-code` exit 0。保护清单及 P019 收尾归属见 `.local/p020-doc-visual-review/protection-check.json`。
7. 作者提供的 11 张代表性 1440/960/主题截图经本轮只读观察未见主要动作遮挡，说明和来源边界清晰；不是审查者重拍全矩阵，也不构成真人、屏幕阅读器或物理 DPI 验收。
8. `python -m tooling.rule_context check --base <上述base> --head <上述candidate>` exit 0；`git diff --check <base> <candidate>` exit 0；结束前 tracked 状态干净。没有运行独审全量 check --all，35 项不能代替全部门禁。
9. GitHub connector combined status 未返回 check-run 信息，随后 gh pr view 核对：rules-context、desktop-environment SUCCESS；两项 foundation 仍 IN_PROGRESS，native-case SKIPPED。不宣称 CI 全绿。上游另转述作者全量在约36%中止 exit 1，并定位旧 tests/test_platform_home_scroll.py:30 仍要求单工具卡；本候选静态确认该断言为 1。后续允许随本任务真实三卡更新为 3，但须独审准确差异，保留 WB 草稿/导航断言及所有容差、超时、skip 与门禁。

未验：科学准确性/LoQ、真人首次使用、操作系统 IME、物理 DPI、目标机器、发布安装、全部依赖/模型体量和性能；本次无依赖/算法变化，不追加无关大矩阵。核分割模型运行沿用作者本轮证据及有效历史范围，不把其 46 核宣称为本主审重新执行模型所得。

## 回传与下一步

结论 **changes_required**，阻断项仅 R01/R02；CI 与旧卡片断言更新待准确新候选。已通过授权线程消息向规划窗口回传实证，规划已转原开发窗口修复。新候选只复审实际增量、两条修复反例及受影响回归；与此候选相同的其他证据可沿用。审查者未改产品实现、未合并、未发布；修复与必需 CI 满足后由规划安排正常 PR 集成与下一任务。

