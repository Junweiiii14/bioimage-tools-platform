# B-009 验证与交付

日期：2026-11-02（Asia/Shanghai）。环境：Windows PowerShell、Python 3.12.14（uv locked/no-sync）、Node v26.7.0、已有Playwright与本机Edge headless。规划树HEAD bb5601addda64fa96fa007612ceda0a0e1ed9b74；保留原dirty，本轮未commit/push。产品树只读基线见baseline-audit.md。

## 实际执行

| 命令/检查 | 退出码/结果 | 范围 |
|---|---|---|
| `uv run --locked --no-sync python dev.py context --task B-009 ... --record` | 0；范围与规则变更后重载 | scopes与规则摘要见rules-context.json；非发布基线证明 |
| `uv run --locked --no-sync python work/evidence/B-009/revise_plan.py` | 0，一次性迁移 | v3 Markdown归档；旧HTML副本及摘要见previous-version.json；不得再覆盖新源 |
| `node work/evidence/B-009/build_html.cjs` | 0，最终内容修正后重建 | canonical和本地交付副本一致；13章/51表 |
| `uv run --locked --no-sync python work/evidence/B-009/validate_blueprint.py` | 0 | 3个JSON、6节点静态示例；标题/锚点/本地证据链接、交付副本一致；无外部脚本 |
| `node work/evidence/B-009/verify_html.cjs` | 0，最终重建后复验 | 1440px/390px、检索/空检索/跳转、菜单、打印CSS、字体；无页面错误/网络请求/页面横向溢出 |
| `uv run --locked --no-sync python work/programs/scientific-agent-platform/check_plan.py` | 0 | 转读bioimage-v0：P001 done/P002 in_progress，其余planned；并非4.0新依赖已接入 |
| `git diff --check -- docs/ai-workflow.md docs/module-map.md AGENT_HANDOFF.md .agent-handoff` | 0，仅Git行尾提示 | 已跟踪文件空白检查，不是全产品门禁 |
| `uv run --locked --no-sync python C:/Users/70236/.agents/skills/agent-handoff-skill/scripts/maintain_handoff.py --repo C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-tools-platform --compact-if-needed` | 0，unresolved=0 | 自动归档1段旧work-log，原记录保留 |

已实际查看desktop.png与mobile-delivery.png，文本、导航和路线布局可读。其他视图经浏览器结构与交互检查，不宣称逐屏/全部打印页人工检查。当前HTML沿用本地已有字体内嵌；外部证据链接仍需网络，本地文件链接不保证跨机器有效。公开发布须另用便携构建核验。

## 内容复核

非作者research代理复核模块科学边界、自动化、扩展及路线，与当前源码事实交叉检查。首轮发现：第7章旧串行顺序残留、registry仍指旧卡、WorkflowSpec与新对象命名未映射；均已修正。顺手更正11.2旧V顺序、B007历史视觉措辞及ScientificAsset“现有”误称。最后绑定摘要和结论见content-review.md。

文档最终摘要由document-validation.json记录：Markdown `5a1eb003deacbad724c348937900530a29a2f9eb9b8b956eff1cc43b7068b62b`；HTML `8af568702e21836bd4bec52a49b0a41d12c1ff1ef0c7b0203926efb81ad67359`。这是内容审查，不是绑定产品提交的源码独审。

## 未运行与边界

未运行产品check --all、科学方法实验、性能/安装/目标Windows/用户验收、在线audit或远程CI；没有修改产品树、安装外部算法、下载新实验数据、发布远端或发送其他聊天消息。官方资料核验与本地源码审计不等于外部工具接入成功。

## 交付

- `docs/plans/research-platform-rd.md`与`.html`：4.0完整方案。
- `.local/deliveries/B-009/outputs/科研数据平台完整研发总方案_模块化工作流平台版_20261102.html`：相同HTML本地交付。
- v3源归档、旧HTML本地副本、当前计划入口/任务状态权威转读与handoff更新。
- 下一轮从bioimage-v0当前P002继续；M路线新卡/依赖需在权威树接入，不在本旧规划树假激活。
