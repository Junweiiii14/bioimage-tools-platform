# R08 上下文精简与原门禁保持

2026-10-28，Windows / PowerShell / 锁定 uv 环境；实施前 HEAD `05c1a16abc3283d0cee03fbd3cdebfe0996a1682`。这是独立治理范围，不改产品或科学语义。最终提交独审、回执重载和冷启动独立验收由集成人员继续；本记录不把文件整理等同目标完成。

## 核验与最小范围

`tooling/rule_context.py` 的 CORE 七份、RECOVERY 四份、receipt schema1、基线/指纹/范围/历史来源验证全部保持。当前仅有根自有 AGENTS，因此 `--scope .` 与 desktop/任务/证据/handoff 范围产生相同规则集合；不能宣称窄 scope 在本仓库现状自动减少字节。原算法已支持祖先/目标子树规则，新增真实 Git 仓库测试验证其语义。

- 风险/待办原文完整归档后，入口改成当前任务指针、科学/环境/旧原生 UNKNOWN 等恢复必需边界及历史索引。所有原 `[ ]` / `[x]` 与未验/失败记录保留，不因归档改成完成，也不按旧“当前”措辞重启已交付工作。
- 模块地图保留现行目录职责、实际桌面入口、schema15 与按范围读取的契约索引，将逐阶段叙述归档。新增产品包/公开 API/数值和 I/O 边界等规则保留。
- `docs/ai-workflow.md` 仅移除已过时的“当前任务未启动子代理”一句，保留并行规则。
- 规则 runbook 补 Dependabot 维护者接手、准确 base/head、任务/回执、必要检查/独审及基线变化重载流程；机器人不豁免，远端操作仍依已有授权。未新增高权限 PR 工作流或放宽服务器检查。

## 原文保存

先以二进制独占创建归档，逐字节与原文件比较成功后才替换入口；再与冻结 HEAD 的 Git 内容按 LF 归一比较完全相等。Git 换行规范可能使已提交归档采用 LF，故同时记原工作树摘要与可跨平台核验的 LF 摘要。归档保持原文，内部相对引用按原文件目录解释；当前入口的新链接另行逐项核验存在。

| 原文件 → 归档 | 原字节数 / 原 SHA256 | LF SHA256 |
| --- | --- | --- |
| `.agent-handoff/risks.md` → `.agent-handoff/archive/T082-before-context-risks.md` | 23432 / `dda8a41b5248e21cb836b400cdf736e8a3349157b163c587c2cbfd3583c2a6a8` | `026e4d9facac0a5a899976be20c6ad870a2ee145c9bae827e6ead1890d4c4cc3` |
| `.agent-handoff/backlog.md` → `.agent-handoff/archive/T082-before-context-backlog.md` | 15750 / `1526f4f5a7be5465b30d14064a9762dce608993418e4211c87bf21f023f04871` | `4b4fdfc50f9662dac2ad0071a29e61a320f104e4d5df8b171b37f661bde378ce` |
| `docs/module-map.md` → `docs/archive/module-map-before-T082.md` | 9173 / `792d6e7efc4dbc4b24f51e8d1d24e464fff5fff17d553d8a42af3154565af07a` | 同原摘要 |

## 实际阅读量

运行同一加载器 `load --task T-082 --scope . --base origin/main`，未使用 `--record`，在内存捕获完整 stdout，不跳过旧规则。before 的工作树读取替换为冻结 HEAD 的 Git 内容，after 为本次修改后的文件；二者任务同为 5441 字节，使用同一 Python/Git/算法。字节以 LF 归一 UTF-8 计，完整输出含标题及因规则变动追加的 BASE 原文。

| 加载内容 | before | after |
| --- | ---: | ---: |
| CORE 七份 | 33173 bytes | 30437 bytes |
| RECOVERY 四份 | 43893 bytes | 10115 bytes |
| 当前任务 | 5441 bytes | 5441 bytes |
| 当前文档合计（不含 BASE/标题） | 82507 bytes | 45993 bytes |
| 本轮实际完整 stdout | **87779 bytes / 796 行** | **68701 bytes / 705 行** |

完整实际输出减少 **19078 bytes（21.7%）**；当前文档负担减少 36514 bytes（44.3%）。后一个数不是本轮输出降幅，因为本轮修改核心文档后仍必须加载旧版规则。未为获得更小数字关闭这项约束；未来基线改变后的输出未在本次测量中冒充已验。

## 验证与余项

- `tooling/rule_context.py` 与冻结 HEAD 字节相同（LF SHA256 `25996d7bb7e834e5c780d8fd1701c342ad6d85d3b52ea78bebe9a0545c183ad1`）。从 Git 加载旧函数，对 `origin/main..05c1a16` 的旧已提交回执验证返回空错误列表；这不替代尚未提交 R08 的最终回执检查。
- 新增三个真实临时 Git 仓库用例：祖先/子树/override 被加载而兄弟规则不载入；有效范围通过、嵌套规则漂移拒绝且重载后通过；兄弟及相同字符串前缀的目录变化仍拒绝。全部原回执负例/断言保留。
- `uv run --locked --no-sync pytest tests/test_rule_context.py -q --tb=short`：**33 passed / 117.23s / exit0**。运行期间未修改规则测试或验证器；另行产品修补不进入这些临时仓库。
- Ruff check 与 format check 针对 `tests/test_rule_context.py` exit0；当前入口的全部本地 Markdown 链接存在；`git diff --check` exit0。
- agent-handoff `maintain_handoff.py --repo . --check`：changed=0、warnings=0、unresolved=0。仅检查，未修改集成人员拥有的其他交接文件。
- 最终提交、规则回执统一重载、准确提交独审、冷启动新代理交接及最终集成门禁尚待执行，不宣称已通过。
