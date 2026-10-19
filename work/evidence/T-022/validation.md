# T-022 验证记录

环境：Windows 11 build 26200 / Python 3.12.14 / Qt 6.12.0；协调 worktree，codex/t022-workflow-ui。所有演示为独立合成工作区，未改真实实验数据或旧演示。

## 第一轮流程重构（049824681ad15c6e31d2095be9196e6fa6045c40）

- `uv run --locked --no-sync python dev.py check --all`：退出0，494 passed / 175.39s，Ruff284、Pyright0、9导入合约、4wheel隔离环境烟测通过。日志 `.local/qa/T-022/check-all.log`。最后新增的欢迎页失败反馈测试在该次收集之后写入，另行专项5通过；不能把494写成包含此新增项。后续视觉修改须重新验证。
- 新工作流专项：导航不改draft/generation/dirty、无效半填回退、有效编辑保留、五类导出信号、欢迎/菜单busy、欢迎打开失败反馈。
- 原15桌面/模板专项通过；独立审查另跑29项/42.95s通过，绑定1bd9640..0498246，未发现确定产品回归。
- 原生截图：初次暴露白底白字/容器黑底/窗口撑高967/OCR空态文案；一批修复后实际1280×900及1100×780。独立Impeccable reviewer四项均resolved，verdict ship仅覆盖其修复列表。
- Impeccable detector 一次输出 `[]`，Python/Qt覆盖有限，不代替截图。
- 旧截图测试从QTabWidget索引改为show_section，仅适配导航，科学业务断言未削弱。

## 第二轮视觉提升

用户明确要求更加精美并同时使用Taste。实际方向抽取和原生适配见taste-direction.md。

- 产品最终提交 f71083be2264e40ba574746ba4e9cd7a5d761965；全门禁 `uv run --locked --no-sync python dev.py check --all` 退出0：498 passed / 173.99s、Ruff287、Pyright0、9合约、4wheel隔离环境。日志.local/qa/T-022/check-release.log。
- 此前中间提交8bbadd7的全门禁497通过/171.56s；不能代替最终检查。
- 实际Qt截图1280×900及1100×780；第二位独立视觉审查先指出表头截断、横向溢出和泳道标签对比度，修复后确认全部resolved，disposition ship仅覆盖此列表。
- 独立代码审查覆盖0498246..8bbadd7（16专项/21.70s）及8bbadd7..f71083b（8专项/4.40s），均退出0，无新增可操作问题。详见independent-review.md。
- Taste网页浏览器检查不适用于此原生Qt程序，未运行；截图与测试不冒充网页检查。

## 旧 WBQuant 对照

用户经对照明确只需风格/布局大致相似，不保留旧操作。继续Qt并按旧版视觉布局做有限调整；后续提交专项检查另记。见wbquant-workflow-comparison.md。

## 验收边界

本机源代码、合成数据及自动化工程验证；真实实验准确率、旧Qt原生中止/停滞根因、大图性能、物理DPI/最终包态及干净Windows验收未完成。未推送或发布。

## 最终旧版视觉参考适配（32a2d18）

- 只改布局与OCR页面归属；原图检测参数左侧浅色窄面板、深色画布右侧，保留四步自由导航。旧版操作不迁移（用户明确）。
- 作者工作流/桌面专项17通过9.74s，Ruff/Pyright/提交门禁通过；独立相同专项17通过9.02s。
- 重新生成原生1280×900与1100×780截图；独立视觉对三张变化截图给ship。全部合成数据，截图生成程序正常退出0。
- 最终 `uv run --locked --no-sync python dev.py check --all` 退出0：500 passed / 173.83s、Ruff289、Pyright0、9合约、4wheel隔离环境（含实际OCR worker）通过。日志.local/qa/T-022/check-wbquant-layout.log。

- 已启动可交互演示，ready.json记录真实PID41120，Windows窗口标题“WB - 合成演示 / 新工作流”，启动stderr为空。旧F006窗口保留；不操作用户其他窗口。
