# P020 作者候选证据

首轮独审修复与后续检查状态见 [review-fixes.md](review-fixes.md)，下文保留首个候选的历史自验，不将其中“正在运行”视作当前状态。
Windows CI 后续唯一失败及最小测试等待修正见 [ci-reopen-wait.md](ci-reopen-wait.md)。

2026-11-06，Windows 本机、锁定 uv 环境、当前桌面源码。PR base 为 `1c819aeaae9813fdc29606cbad463b08a191fbab`；起点 `6c06283190c044491c862d5961f9e3b9f6b800e9` 的 P019 收尾随本轮保留。准确 candidate 在 PR 与上游审查请求中冻结。独审/CI/集成未完成，以下均为作者自验。

## 实现与复验入口

- [操作说明](../../../docs/runbooks/unified-workbench.md)：`uv run --locked --no-sync python -m bioimage_app` 启动当前源码；旧安装与快捷方式未更新。
- 首页三工具同骨架卡片；研究标记与环境准备独立。BCA 使用原有 PlateRecord、BcaHost、WorkflowSession、Workspace 和 P019 完整核验器，没有新增数值方法或共享平台特判。
- BCA 新板默认不确认实验事实；加载 JSON 保留摘要。结果仅从核验后的完整提交加载。导出再次核验，单独目录保存完整精度；显示舍入不回写。失败/取消保留已保存历史并标明旧结果。
- 首页编排按钮进入 P009 真画布，只支持已注册 WB 模块。未增加 BCA/核分割节点、插件系统或 Agent。
- 核分割实际准备指南可打开，模型路径保持原配置方式；返回首页不取消任务。WB 方法和旧项目保留。
- 第三方实现、模型、参考数据、原图、冻结方法/schema、依赖、锁文件、门禁无修改；仅新增桌面适配与展示。未测内存/性能收益，不声称轻量化指标达成。

## 已执行验证

以下命令均在活动树运行，Python 命令前缀为 `uv run --locked --no-sync`。Qt 定向测试使用 `QT_QPA_PLATFORM=offscreen`、`QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu`。

| 检查 | 结果 |
|---|---|
| `pyright` 本轮 bridge/results/window/测试文件 | exit 0，0 errors / warnings |
| Ruff check/format 本轮 Python；新增证据脚本 Ruff | exit 0 |
| `python -m tooling.web_quality` | exit 0，四个门禁自测通过 |
| `pytest -q tests/test_nuclei_web.py tests/test_nuclei_ui.py tests/test_bca_host.py` | exit 0，10 passed / 9.33s |
| `pytest -q tests/test_bca_web.py tests/test_bca_ui.py tests/test_project_navigation_session.py tests/test_workflow_authoring_web.py` | exit 0，22 passed / 64.24s |
| `pytest -q tests/test_wb_student_results.py` | 3 passed（与首轮核分割脚本一起运行时整体因下项失败而 exit 1） |
| 实际核分割 `.local/p020_nuclei_test.py` | 最终 exit 0，1 passed / 31.01s；已保留复验脚本 `nuclei_check.py` |
| 最终截图 `.local/p020_capture_test.py` | exit 0，1 passed / 22.87s；已保留复验脚本 `capture_check.py` |
| `maintain_handoff.py --check` | exit 0，无容量警告 |
| `git diff --check` | exit 0，只有工作树 CRLF 通知 |

真实 BCA 回归从 WebChannel 选择合成 CSV/记录，实际启动 worker，核验 S1=5008.680555555556 µg/mL、4组 partial 空汇总，导出后新 Python 进程重开同 run/source SHA；篡改临时结果被拒绝。另测未确认记录拒绝、实际 worker 取消无结果、返回首页保留结果、焦点及合成中文 composition 事件。

核分割使用已有固定研究环境/模型和公开 Ganglioneuroblastoma_10.tif，不下载、不改模型。真实输出 46 个核，新进程同 run/source SHA，见 `nuclei-run.json`。首轮脚本在 WebChannel 就绪前点击帮助而超时，修正脚本等待后通过；没有以调整产品测试预期掩盖失败。

## 全量检查及已知缺项

`python dev.py check --all` 第一轮因新测试空行格式失败，已修正。第二轮未设置 CI Chromium 参数，出现 GPU context lost 并持续无进展，作者中断，exit 1，不能算通过。第三轮使用 CI 的 `--disable-gpu` 参数，正在运行；日志 `.local/p020-check-ci-env.log`，最终结果待补。前两轮日志 `.local/p020-check-all.log`、`.local/p020-check-all-final.log` 保留本机，不提交长日志。不得把已通过的定向检查写成全量成功。

计划校验脚本仍报告历史 P010 缺 reviewed commit（脚本 exit 0）；未改旧审查证据，也未扩为本轮修复。独立审查与必需 CI 待准确候选。科学适用/化学准确性/LoQ、真人学生操作、真实 OS 输入法、物理 DPI/目标设备、安装包及用户安装更新均未验。

## 有界视觉核验

`screenshots/` 共16张：四主题首页各1440×940/960×720；BCA表单、BCA结果、核分割结果和真实WB编排画布各两尺寸。最终全部查看，未发现裁断主要动作、重叠或错误主题。960首页下部需滚动，编排画布允许水平滚动；表单与表格独立滚动。不是静态 HTML 模拟，内容来自当前 WebWorkbenchWindow 和实际提交。

首批发现英文状态/长小数影响扫描后集中修正；最终确认仅修复截图采集等待（fonts/viewport/transition/compositor），使用 offscreen 软件路径重采。此前原生采集存在过渡帧与旧尺寸残留，已排除。没有追加审美改版，DESIGN/token保留。

Impeccable detector仅运行一轮：18px符号、原有hover对比度、indeterminate进度和旧暗色glow等静态提醒保留；未把静态提醒当成数值对比度或可访问性认证。未做屏幕阅读器/真人可用性评估。研究截图不是科学准入证据。

## 协调

作者/唯一写入者：`01a1b02f-dc63-7573-94bb-014c0cb2aadc`。上游 `01a19bfd-f3ab-7502-86da-9f61953d1c8a` 派固定独审 `01a1af0d-808e-7131-ae29-237aded27938`，host local。独审应独立检出准确 candidate；不切换共享树。作者保留写入所有权、待审期间只补明确验证收据或按回传修复，不自行合并。
