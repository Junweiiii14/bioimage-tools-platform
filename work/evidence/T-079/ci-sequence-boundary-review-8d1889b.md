# T079 CI 顺序流程等待修复独立审查

**结论：Accepted（测试同步修复）；新的最终HEAD完整CI仍待通过。** 未发现降低原预期、删断言、增加时限、skip/xfail或更改产品来掩盖失败。62d91b0首轮Linux失败及修复中的中间失败全部保留，不把本机独立通过当作新Linux/Windows CI已成功。

- base：`62d91b0d1f20f78bbdbb5728410bfa575188bbf3`
- reviewed head：`8d1889bca2f6fa5ab6a9291ad6a85f79076d0fe6`
- 活动树：`C:/Users/70236/.codex/worktrees/wb-lab-installer/bioimage-tools-platform`
- 分支：`codex/t079-laboratory-delivery`
- 审查时间：2026-10-23 11:26:22 Asia/Shanghai / 03:26:22 UTC。
- 审查文件：`tests/test_instrument_intake_desktop.py`，函数 `test_sequence_real_page_two_figs_pause_continue_stage_barriers_and_reopen`。
- 绑定提交仅该文件35行新增/3行删除。实际测试文件字节SHA256：`288030d18b82cf040f1e8604944b5464cc8fed7c7b381276ef1de522ae225ae5`，独立运行前后和提交对象均一致。

本次为非作者只读审查及独立测试。未创建代理、修改产品/测试/脚本、操作用户进程或重跑远端CI。只新增本报告；作者当前任务记录改动保留。测试夹具与缓存均在经绝对路径验证的自身TEMP目录。

## 真实失败和独立诊断

阅读 `.local/T079-linux-initial.log` 的实际失败段和结尾：62d91b0的Linux完整测试为 **1 failed、1222 passed、10 warnings、463.71s、exit1**。失败位于原1435行：预期第二个crop停在`needs_review`，实际读取为`['done','running']`。这份失败不能由之后重跑成功覆盖。

逐项核对产品现有保存/执行调用链：

1. `IntakeWorkflowSession._advance()`先claim阶段，将ledger持久化为running，再以after回调调用`_execute(ticket)`。
2. `_persist()`先`host.end_phase()`，再调用`host.save(after=..., transform=..., install_guard=...)`。
3. `FigureWindow.save().saved()`安装已保存项目、更新保存代际并把busy置false，随后继续after回调；已保存不等于后续执行结束。
4. 原`wait_saved()`仅判断`not operation_busy and not has_unsaved_changes`，因此不能表达“下一人工复核点已到达”，也不能表达网页快照已包含该点。

源码和可控延迟均支持“观察条件不足”的诊断。失败发生于阶段状态读取；这不是科学数值比较失败的证据，也不据此宣告科学准确率已验。

## 修订是否削弱预期

审查base..head全部差异。三阶段的保存等待改为：初次crop边界`needs_review,pending`；第一条人工裁剪完成后的`done,needs_review`；最终必须是`WBIntakeOutputProject`且全部步骤done。每处仍要求host不busy、无未保存更改，等待仍为20秒。

循环开始的网页等待由单独`!state.busy`强化为同一页面快照中不busy并匹配本轮完整crop状态串；原10秒不变。原`commitCrop()`之后run按钮必须可用的断言完整保留。后端终态不能代替网页快照就绪，两层等待覆盖不同边界。

亲自以AST比较base函数和当前函数的全部`assert`节点，**28条对28条，逐节点AST完全相同，exit0**。其中保留类型、策略版本、精确阶段状态、后续阶段attempt=0、两个Fig和analysis数量、真实worker PID/succeeded、complete输出、真实表可见与尺寸/行数、页面经过四模式、每份已保存阶段快照的屏障、重开attempt不变、归档ZIP不变、原图字节不变。未调整科学容差或数值预期，未更改其他测试函数。

亲自执行：

`git diff --exit-code efd8d4f8fa9cd6c3b86a291d49ede9ad54bb971b 8d1889bca2f6fa5ab6a9291ad6a85f79076d0fe6 -- apps packages tools tooling pyproject.toml uv.lock .github`

**exit0、无差异**。安装产品、配方、依赖锁和门禁保持efd版本，实验室安装器无需因这一测试同步修复重建。最终CI仍必须覆盖含测试修复的新准确HEAD。

## 反例、修复中间失败与独立运行

审读作者 `.local/t079_sequence_experiment.py` 及三轮结果。helper只在本进程以QTimer推迟第二个crop的实际`_execute`，其余真实网页/保存/worker流程保留；不修改产品源码。

| 证据 | 实际结果及含义 |
|---|---|
| 作者500ms原测试red，t079-sequence-red.log | **1 failed / 2.46s，raw pytest exit1**；捕获`['done','running'] busy=False dirty=False`，随后原1435断言精确失败，复现CI状态 |
| 作者仅修后端边界的第一次green，t079-sequence-green.log | **1 failed / 2.51s，raw pytest exit1**；失败转到原run按钮断言，网页快照尚未跟上，不能被记作成功 |
| 作者补网页匹配终态后的green2 | 作者报告 **1 passed / 6.80s，exit0**；原500ms中间claim仍被捕获 |
| 作者正常目标及相邻回归 | 作者报告 **2 passed / 14.10s，exit0**；不冒充本审查亲跑 |
| 非作者独立750ms延迟实验 | **1 passed / 7.15s，raw pytest exit0，外层exit0**；详见下段 |

独立实验实际命令为 `uv run --locked --no-sync python -`。stdin中自写pytest插件，没有执行作者helper：使用`pytest_runtest_call`和本进程MonkeyPatch包装原`IntakeWorkflowSession._execute`；在两行项目的第二个crop claim已保存时捕获实际状态，并以`QTimer.singleShot(750, session.host, ...)`调用原执行函数。没有伪造执行结果、跳过保存或替换worker。

环境 `QT_QPA_PLATFORM=offscreen`、`QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu`，Windows字体目录；pytest仅选择上述完整原测试，`--basetemp`与`cache_dir`指定自身TEMP。实际捕获：

```json
{"crop":["done","running"],"busy":false,"dirty":false,"delay_ms":750}
```

随后整个测试通过，原28条断言均实际执行。外层还断言延迟恰好触发一次、捕获状态正确，以及运行前后测试源SHA未变。事后以`git show 8d1889b:tests/test_instrument_intake_desktop.py`确认提交字节与同一SHA一致。

该实验独立验证修订能跨过原失败窗口，并继续验证网页按钮、真实执行、输出和重开。未独立运行Linux或全1223测试；软件图形回退stderr仍出现，未把本机offscreen通过外推到物理DPI/GPU。

## 收口边界

本测试修复 **Accepted**。原62d91b0完整CI失败保持有效历史记录，必须等待含修复及最终证据提交的新HEAD四必需CI全部成功，再执行正常合入/整理/冻结。

此前冻结helper的两项审查发现已通过静态复核关闭：精确9项额外路径allowlist并拒绝stage全树reparse/越界；随包报告从固定CI HEAD的`git show`原始字节读取。它仍须随新最终HEAD重绑闸门，并单独限定本次已审测试差异；不能继续使用62d91b0失败收据或宣称未来冻结完成。本次未执行GitHub整理或桌面冻结。
