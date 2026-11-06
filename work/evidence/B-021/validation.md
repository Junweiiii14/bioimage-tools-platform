# B021 验证记录

环境：Windows PowerShell，隔离工作树 `bioimage-independent-review`，初始源码基线 `6bd4680530dc4697f8d394a96fd288723222ddb8`。文档命令以 `UV_PROJECT_ENVIRONMENT` 指向现有 `bioimage-plan-sync/.venv`，只执行 `--locked --no-sync` 命令，不安装或修改共享环境。候选提交与最终CI稍后补记。

| 检查 | 结果与范围 |
|---|---|
| 首次 `uv run --locked --no-sync python dev.py context --task B-021 ... --record` | exit 0；建立任务后加载适用规则；新增规则后必须再加载 |
| `git diff --check` | exit 0；文档空白检查，不代表产品通过 |
| `uv run --locked --no-sync python dev.py policy` | exit 0；233产品文件边界扫描，既有来源检查；不代表所有算法完整性或科学正确 |
| 新增规则后重复完整context加载 | exit 0；逐段读取输出及旧规则差异，更新当前回执 |
| 8份文档的本地链接核对 | exit 0；27个路径，无缺失；AGENTS为6811 bytes，小于8 KiB |
| `maintain_handoff.py --repo . --compact-if-needed`及`--check` | 均exit 0；自动归档1条日志，最终0 warnings/0 unresolved，原snapshot另留存 |
| `uv run --locked --no-sync git commit ...` | exit 0；3946f75，policy提交钩子通过，Python/Web无改动明确skip |
| `python -m tooling.rule_context check --base origin/main --head HEAD` | exit 0；精确6bd4680→3946f75回执覆盖通过 |

PR69 已创建；准确3946f75文稿经上游交叉核对无阻断，提出的两处适用范围说明已合并。CI/主线集成未在此阶段宣告成功。P017只读独审另已回传上游，证据不作为B021产品验收。

本任务无产品代码、锁文件或门禁实现变化。本机不重复运行产品全量/GUI/科学/目标机测试；正常PR必需CI仍执行。本方案不是产品合规结果。P017候选审查另行绑定其提交并记录，不混入B021产品验收。

规则变化说明：AGENTS新增一条持续独审入口，ai-workflow新增候选回传/新任务新窗的执行约定；没有新增或削弱服务器检查、容差、skip或审批系统。

## PR68集成后的基线更新

核实origin/main为f8f69b51e01446ffed6301dec99d2cf28fcdb85c；42df0eb正常合并主线，archive/snapshot文本冲突按保留双方历史解决，未改产品。B020主方案及HTML沿用已集成内容。B021协议正文仍为b093209，未增加新要求。

上游授权按白名单采用本地0d134926ecb8b2ecd0f1692847d067f8dc123fbe的P017任务done、final-delivery、objective-audit、review-and-validation和必要handoff完成事实，不整体合入该本地提交；它不是已可在GitHub访问的提交。P017两份rules-context/integration-context仍逐字节等于main f8f69b5，未删改。0d134原加载事件保留在原本地提交/开发分支；B021唯一当前回执重新覆盖实际main及所有本次改动，不把P017旧加载事件当当前验证，也不修改门禁来兼容多清单。

独立核对确认b2eaccd、f8f69b5、c74e6cc文件树相同；纯收尾14文件不含产品/算法/依赖变化。P017的18/18低于计算LoQ、体积/空白SOP、科学/用户/安装限制原样保留。活动树已登记P018；本审查树不复制其未集成任务或修改其状态。

最终推送前：重新加载context、policy、git diff --check、handoff维护及check均exit 0。21份Markdown共213个相对链接；首次通用扫描发现原样归档snapshot内1条历史相对链接从归档目录不能解析，按原snapshot所在目录验证存在，212条现行路径直接存在，第二次核对exit 0；不改写原始档案。AGENTS为6811 bytes。独立子代理只读核对本轮收尾无阻断：方案正文等于b093209、P017两份回执等于main、新开发任务指针不覆盖活动树状态。准确最终commit/CI/主线结果在PR69与最终回传绑定；本段不提前声称CI通过。
