# P012 工程验收与交接

2026-11-05：本项工程范围完成。[PR62](https://github.com/Junweiiii14/bioimage-tools-platform/pull/62) 正常 squash 合入 main `f30ea5d515a8fedaece994edc6cb583db752d536`，2026-11-05T14:47:31Z。最终候选 `dd99855b57a8b18c57e33c0f2917987988b6cab3`；fetch 后候选与 origin/main 文件树 diff 为空。未绕过规则或发布安装器。

## 逐项完成核验

| 要求 | 当前证据 |
|---|---|
| 空项目真实 GUI 导入、自动分析 | [walkthrough](walkthrough.md)：两张合成 uint16 TIFF、Fig 1/五泳道/Target/Reference，真实窗口和原生文件对话框操作，四阶段完整提交 |
| 必要身份、对应与归一化 | S1–S5 显式 1:1 配对，S1 演示实验/组/生物/技术重复，其他身份留空；ratio-only 与 single-control 数值、未确认及缺对照行为均实际走查 |
| 表图导出、保存重开 | 三份 XLSX 与 PNG；XML 逐条断言、PNG 实际查看；原始 SHA、持久化配对/身份/确认、分析 run ID 及新旧输出保留核验 |
| 仅修确认障碍 | 字段失焦吞点击、重开丢页面两项 P2；实际 Qt 单击和完整关闭重开回归；不改算法/schema/统计口径 |
| 非私有练习及学生任务 | [生成器与短练习](../../../examples/wb-first-use/README.md)，版本准备、五步任务和旁观者观察项；uint16/像素等价/拒绝覆盖独立核验 |
| 绑定提交独审 | [独审报告](independent-review.md)，产品/测试 `76bd5b760a89c5115bea1d9456970dbdf8279daf` 两项关闭、无新增发现；后续只有文档变化 |
| 正常 PR 与必需检查 | 最终 rules-context、desktop-environment、Windows/Linux foundation 全部 success；PR62 已 MERGED |
| 科学/学生/目标环境边界 | 本文、练习、任务及风险入口明确未验，未把合成走查当科学或真人验收 |

## 验证终态

[最终 quality run42044467802](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/42044467802)：

- Windows job127304139622：1703 passed、10 warnings、1154.86s，随后独立 wheel 场景及 check --all 完整通过；job22m15s。
- Linux job127304138957：1699 passed、4既有 Windows shell/private-CPython skip、10 warnings、669.38s，随后 wheel 及 check --all 完整通过；job13m38s。
- rules-context run42044467841 success；desktop-environment success。native-case 是既有手动诊断条件分支，本次正常 PR 跳过，不属于未运行的必需门禁。
- 旧候选 quality run42040701702、42041925936 因后续文档推送被自动取消，不计为通过。

本机 Windows / Python3.12.14 / 锁定 uv：

- 定向新增回归与三组端到端：4 passed /30.44s，exit0。
- 首次 `dev.py check --all`：静态/类型/导入/web 门禁通过；pytest1701passed/2failed/10warnings/1264.29s，exit1。失败为既有 `test_rotation_preview_and_one_real_click_commit[False/True]` 画布刷新超时，伴随 GPU context-lost/SKIA 日志。该命令没有进入 wheel 阶段，原失败保留。
- 采用 CI 相同 `QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu`、`PYTHONUTF8=1`，两项失败加新增用例：6 passed /28.64s，exit0，仍有 mailbox 日志。未改断言、超时、skip 或门禁；不宣称原图形故障根因已解决。
- 单独补完 `python -m tooling.installed_wheels`，offscreen/--disable-gpu，exit0；含原值 TIFF/PNG、OCR、真实 worker、存储、重开及图形工作流，保留 GLES/shared-context 日志。
- 素材生成/已有目标拒绝及 SHA 不变、导出值/空身份/PNG 尺寸和原始输入 SHA 断言 exit0。持久化分析 run ID 仍为 `a89e3c6203134cceb30b516100a17c81`、`5af4aa8369794b4c9103b4774919518a`。

## 接续与边界

用户明确要求连续自动推进，已立即向上游“调研软件商业化路径”（01a19bfd-f3ab-7502-86da-9f61953d1c8a，local）转达，上游明确接受“完成→验收集成→回传→派发下一项”。本次最终回传后由上游核对依赖继续派发，不等待用户重复催促。发布/外联/花费/数据用途与科学验收仍按已有授权边界。

真实样本配对、组别、重复、原软件背景口径仍 UNKNOWN。科学适用性、真人学生独立试用、干净 Windows/GPU/DPI 及外部 Excel/WPS 未验。实验室在用安装未替换，试用准备人员启动本次源码版本。原 dirty 树未改；非私有走查项目/输出留在 `../p012-first-use`，不覆盖历史。原基线 GUI 正常退出exit0；另开修复版窗口后因用户输入/最小化停止控制，未把这次手工复查计为通过。

合入后收据只记录实际结果，本地保留随下一正常任务带入；不为文档收据另开重复全量 PR。
