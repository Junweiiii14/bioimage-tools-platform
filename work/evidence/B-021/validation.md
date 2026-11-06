# B021 验证记录

环境：Windows PowerShell，隔离工作树 `bioimage-independent-review`，初始源码基线 `6bd4680530dc4697f8d394a96fd288723222ddb8`。文档命令以 `UV_PROJECT_ENVIRONMENT` 指向现有 `bioimage-plan-sync/.venv`，只执行 `--locked --no-sync` 命令，不安装或修改共享环境。候选提交与最终CI稍后补记。

| 检查 | 结果与范围 |
|---|---|
| 首次 `uv run --locked --no-sync python dev.py context --task B-021 ... --record` | exit 0；建立任务后加载适用规则；新增规则后必须再加载 |
| `git diff --check` | exit 0；文档空白检查，不代表产品通过 |
| `uv run --locked --no-sync python dev.py policy` | exit 0；233产品文件边界扫描，既有来源检查；不代表所有算法完整性或科学正确 |

本任务无产品代码、锁文件或门禁实现变化。本机不重复运行产品全量/GUI/科学/目标机测试；正常PR必需CI仍执行。本方案不是产品合规结果。P017候选审查另行绑定其提交并记录，不混入B021产品验收。

规则变化说明：AGENTS新增一条持续独审入口，ai-workflow新增候选回传/新任务新窗的执行约定；没有新增或削弱服务器检查、容差、skip或审批系统。
