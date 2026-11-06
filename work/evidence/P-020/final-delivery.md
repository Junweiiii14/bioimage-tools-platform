# P020 统一工作台工程 MVP 交付

2026-11-06，PR [72](https://github.com/Junweiiii14/bioimage-tools-platform/pull/72) 已按上游明确安排正常 merge，未绕过规则。main `aa3302ad2980dfeec1ac6f7776fec6176f18fcda` 与准确已审候选 `0d83f4dc75804e90291d408302027fe590286fdf` 执行 `git diff --exit-code` 返回0，文件树完全一致。活动分支已fast-forward到该main；后续仅本地收尾收据，随下一任务带入，不推纯收据触发CI。

## 可用入口与交付内容

在 `C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-plan-sync` 运行 `uv run --locked --no-sync python -m bioimage_app`。包身份仍是bioimage-app 0.14.0，准确行为由上述源码提交确定。操作见 [统一工作台说明](../../../docs/runbooks/unified-workbench.md)。

- 首页WB、核分割、BCA三张同骨架卡片，研究标记与准备状态分开；保留现有主题和专业能力。
- BCA选择CSV与明确板记录，真实worker→完整提交核验→逐孔/技术样本表→导出→新进程重开。原始身份、单位、partial及缺失值保留；失败/取消不发布成功或填零。
- 核分割可打开实际准备说明和固定HTTPS来源；返回工作台保留会话。
- 首页工作流编排进入既有P009真实WB模块画布。BCA/核分割尚未注册为画布节点，未实现完整插件卸载、跨实验组合或Agent。

截图：[首页](screenshots/home-forest-1440.png)、[BCA结果](screenshots/bca-result-1440.png)、[核分割结果](screenshots/nuclei-result-1440.png)、[960编排画布](screenshots/workflow-960.png)。共16张，来源为初审3056334当前源码实窗/实际提交；后续修复未改布局，新增行为另由精确候选的独立反例验证，不冒称旧图重拍。

## 准确候选验证

全部必需CI成功，均绑定 `0d83f4d…`：

| 检查 | 真实结果 |
|---|---|
| [quality 42204821003](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/42204821003)，Windows job127848703180 | 1767 passed / 10 warnings / 1018.15s；随后完整wheel及check --all成功 |
| 同run，Linux job127848702958 | 1763 passed / 4既有Windows专用skip / 10 warnings / 825.35s；随后完整wheel及check --all成功 |
| desktop-environment job127848703286 | success |
| [rules-context 42204821004](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/42204821004) | success |

native-case为按既有条件未选择的诊断job（skip），不是修改测试skip。未改依赖、锁、门禁或数值容差。

作者真实BCA/取消/损坏拒绝/重开及WB/导航验证、公开核分割46核与新进程身份核验、视觉范围见 [README](README.md)。R01/R02修复后17项通过，等待条件修正相关15项通过。精确规则回执、Ruff/Pyright/Web和提交hook通过。

指定审查者 `01a1af0d-808e-7131-ae29-237aded27938` 三份原报告逐字节归档：

- [3056334初审](independent-review-3056334.md)：changes_required，原R01/R02结论不倒改。
- [c9a4d42增量](incremental-review-c9a4d42.md)：pass，117身份单元格及原帮助链接反例通过，P3占用提示关闭。
- [0d83f4d最终增量](incremental-review-0d83f4d.md)：pass，受控延迟证实只收紧测试等待条件，生产/算法/依赖/门禁零变化；既有工程结论可沿用至准确候选。

独审原始探针仍位于 `bioimage-review-p020/.local/`，报告描述原路径和实际观测边界。自验不冒充独审，原始失败均保留：本机格式失败、GPU中断、旧单卡预期、Qt JS测试传输修正、c9a4d42 Windows旧等待条件失败，以及独审自写探针首轮假设失败。详 [review-fixes](review-fixes.md)、[CI定位](ci-reopen-wait.md)及独审报告。没有声称本机完整check成功或物理GPU根因已解决。

## 边界与交接

工程MVP完成；BCA化学准确性/LoQ、核分割科学适用、真人使用、真实OS输入法、物理DPI、目标设备、候选安装和用户旧安装更新未验。原图/历史/旧dirty树/用户旧安装未改，没有数据上传或模型下载。旧P010计划校验缺reviewed commit仍为历史缺项。

一次本地收尾后释放共享活动树，下一新任务由上游新窗口派发。本窗不继续扩后端。下一最小建议：先统一三工具的已保存项目入口与来源/重开路由，再按真实用例约束核分割/BCA可注册的节点端口；不把无关图像/孔板端口强行连接，也不先建通用插件框架。建议不是已实施或新增发布授权。
