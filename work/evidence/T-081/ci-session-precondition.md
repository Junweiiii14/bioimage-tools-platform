# T081 R2：关闭会话测试的空闲与新编辑前置条件

2026-10-24，北京时间；活动树 wb-lab-installer，分支
`codex/t081-restore-auxiliary-tiff`，源码基线
`c3df3a5d7e123562980db0d4e77cc94b52d31b24`。本增量只修改测试前置条件，
不修改产品、状态机、保存/关闭门槛、依赖或 CI 配置；最终提交、独审和新 required CI
由后续收尾绑定，本地定向通过不代替该过程。

## 原失败与证据边界

PR43 的 [Windows foundation job 120582706708](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/40002723621/job/120582706708)
实际 **1 failed / 1294 passed / 759.97s，pytest exit1**。Linux、桌面环境、规则检查
成功不能替代该 Windows 失败。原日志保持在
`.local/T081/package/r2/ci-windows-c3df3a5-initial.log`，SHA256
`239D8A49DE045125F3D1D073D0A0E0519E58CA162FB05BCEC16AA061F842E7B8`。

原日志 1872–1918 行：
`test_busy_cancel_rechecks_draft_then_unsaved_changes_before_shutdown` 已通过
busy→cancel→confirm_draft→discard→confirm_dirty→return 的原有断言。
再次 pause_auto_save(True) 后立即 close，原第377行要求 confirm_dirty，实际是
confirm_busy。1963行保留完整失败计数；失败未改写为成功。

代码对应：

- `web_window.py:424–444` 在关闭时先检查 operation_busy，再检查未应用草稿和
  has_unsaved_changes。因此真实工作仍在执行时 confirm_busy 是正确保护。
- `web_window.py:460–466` 的 return 恢复 idle 并调用 pause_auto_save(False)。
- `figure_window.py:1627–1633` 取消暂停时可重新启动未保存编辑的自动保存；再次暂停
  仅停止定时器，不排空或取消已经启动的后台请求。
- `figure_window.py:1366–1405` 的 refresh_project_table 有真实 worker 和回执，
  其完成回调前 operation_busy 保持为 true。

原测试再次 close 前只断言 visible/unsaved，没有确认工作已结束，也没有在可能
发生的保存之后建立新的未保存编辑。CI 的 confirm_busy 可确定当次关闭走了忙态
保护；原日志没有保存所有 WB job/GUI 请求时序，**具体是哪项后台工作仍 UNKNOWN**。
下面的受控读表反例证明该测试缺少必要前置，不能倒推 CI 当时一定在自动保存。

## 有界受控反例与修正

ignored 诊断 `.local/T081/package/r2/test_session_return_control.py` 调用原测试函数，
在 return 解开暂停后启动真实 refresh_project_table。仅将其实际 fill_project_table
调用延迟到下一次 GUI 事件循环释放 Event；原计算、回执和关闭逻辑仍正常执行。
它不赋值 busy、不伪造结果、不更改状态预期；无固定睡眠。Event 有3秒失败兜底，
通过时必须观察实际 worker 进入且及时释放，不能把兜底超时记作通过。

修改前的原函数在相同末尾断言真实失败：**1 failed / 2.62s，exit1**。
`session-return-red.json` 记录 return 后 stage=idle、busy=true、unsaved=true，
实际 worker 已进入；再次暂停仍 busy=true，close 后 stage=confirm_busy、资源未关闭。
原日志为 `session-return-red.log`，没有覆盖后续结果。

仅在测试第二次 close 前增加：暂停后用3000ms预算等待 stage=idle 且
operation_busy=false，再按该测试既有 generation 编辑方式建立一份新的未保存编辑，
确认 has_unsaved_changes 后继续原关闭/保存流程。保留全部原 visible、草稿捕获、
confirm_busy/cancel/confirm_draft/confirm_dirty、has_unsaved_changes 和最终
resources_closed 断言。原3000ms取消阶段等待及20000ms资源关闭等待不变；未放宽
状态集合、删断言、扩大时限、重复点击或通过 sleep 碰绿。

同一受控诊断加原节点、相邻“丢弃未应用草稿不等于丢弃未保存项目”节点一次运行：
**3 passed / 3.98s，exit0**。`session-return-green.json` 显示实际 worker 被事件循环
释放，最终 busy=false、unsaved=false、resources_closed=true；日志为
`session-return-green.log`。没有额外跑全量或重复循环。

## 命令与环境

Windows 本机，CPython3.12.14（AMD64）、PySide6/Qt6.12.0；Qt 由本分工串行独占。
两轮共同设置：

```powershell
$env:QT_QPA_PLATFORM='offscreen'
$env:QTWEBENGINE_CHROMIUM_FLAGS='--disable-gpu'
```

红例（未改产品/原测试）：

```powershell
$env:T081_SESSION_CONTROL_REPORT='.local/T081/package/r2/session-return-red.json'
uv run --locked --no-sync pytest .local/T081/package/r2/test_session_return_control.py -q --tb=short *> .local/T081/package/r2/session-return-red.log
```

绿例（测试前置修正后）：

```powershell
$env:T081_SESSION_CONTROL_REPORT='.local/T081/package/r2/session-return-green.json'
uv run --locked --no-sync pytest .local/T081/package/r2/test_session_return_control.py tests/test_project_navigation_session.py::test_busy_cancel_rechecks_draft_then_unsaved_changes_before_shutdown tests/test_project_navigation_session.py::test_discarding_unapplied_draft_does_not_also_discard_unsaved_project -q --tb=short *> .local/T081/package/r2/session-return-green.log
```

静态检查均 exit0：

- `uv run --locked --no-sync ruff check tests/test_project_navigation_session.py`
- `uv run --locked --no-sync ruff format --check tests/test_project_navigation_session.py`
- `uv run --locked --no-sync pyright tests/test_project_navigation_session.py`：0 errors/warnings。
- `git diff --check -- tests/test_project_navigation_session.py`

gh auth status 和 gh pr view 43 的只读检查 exit0，确认本次 job/source 身份。
Qt 的既有字体/GPU提示未作为本失败根因；旧 Linux native UNKNOWN 也未由本修正解决。
