# 人工复核安装诊断时序修复

范围：`apps/desktop/src/bioimage_app/installation_check_sequence.py`，不修改产品复核、
工作流或裁剪语义。Windows/Python 3.12.14/锁定环境；工作树基线
`2d2c9727ec93c7a625e46964696788f06f8f4834`，尚未提交。

根代理首轮源码 `--verify-sequence-installation` 失败，保留
`.local/T080/source-sequence.json` 和日志。诊断把选中原图/切换页面的 JavaScript
`true` 回调误认成“已点击保存继续”，实际尚未执行 `commitCrop` 即检查保存结果。
现用 `selected` / `submitted` 区分导航完成与提交完成。

第一次修正后的独立报告 `.local/T080/source-sequence-review-sync.json` 仍失败，
真实产品拒绝“请等待当前阶段退出”。原因是 v4 正在整理部分快照时，宿主 I/O
回调之间短暂 idle；诊断仅据 busy/paused 提前选择复核。现在同时要求阶段账本无
running 且 pending_ready=0；提交时还要求页面与真实 workflow digest 一致、页面
无运行票据。保存证据检查适用于真正的 WBIntakeCropProject，不错误要求必须先有
WBIntakeOutputProject。仍要求实际 e.reviewed 持久化，未将 JavaScript ACK 当作 CAS。

最终新报告 `.local/T080/source-sequence-drained-review.json` passed：13 项检查全过，
errors=[]，8.875 s，真实 worker PID 40900/35512，两次实际人工复核、两个 Fig 保存、
40×120 uint16 原值裁剪、缺失不填零、全部阶段事件、自动页面导航、完整目录与 ZIP、
重新打开后旧运行/输出保持、原图摘要保持、所属资源关闭和窗口释放全部验证。

实际命令（Qt 串行，`QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu`）：

```text
uv run --locked --no-sync python -m bioimage_app --verify-sequence-installation .local/T080/source-sequence-review-sync.json
  exit 1，失败保留
uv run --locked --no-sync python -m bioimage_app --verify-sequence-installation .local/T080/source-sequence-drained-review.json
  exit 0，passed / 13 checks / 8.875 s
uv run --locked --no-sync ruff check apps/desktop/src/bioimage_app/installation_check_sequence.py
  exit 0
uv run --locked --no-sync ruff format --check apps/desktop/src/bioimage_app/installation_check_sequence.py
  exit 0
uv run --locked --no-sync pyright apps/desktop/src/bioimage_app/installation_check_sequence.py
  exit 0，0 errors / warnings / informations
```

报告由独占新文件创建，不覆盖以前失败；未减少 required checks、旧科学/像素断言或
真实 worker/恢复检查，未增加 ignore/skip/xfail。未重跑其他大套。最后仅补诊断注释，
不改变已验证行为。Qt 已释放，可冻结提交并绑定独立审查。此结果是源码环境工程验证，
不声称新安装包或干净 Windows 验收通过。
