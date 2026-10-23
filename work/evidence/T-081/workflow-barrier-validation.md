# T081 全批裁剪阶段门槛验证

2026-10-23，北京时间；Windows 本机，活动树 wb-lab-installer，分支
`codex/t081-prominent-crop`，基线 d08b16bc0f632ee08f4d621f255469c416046593。
本记录对应未提交工作树；最终提交、独审及 CI 由任务收尾绑定，不能据此宣称已合入。

## 已实现与兼容

- 新顺序配置使用 workflow@5：所有 crop done 且具有匹配来源、ROI、有效几何和
  原值资产前，compose/measure/export 均不可领取；其他 pending crop 仍可执行。
- 明确继续/重试以 cropBarrier=true 调用采用规则用例，旧 v4 当前草稿进入 v5，
  既有成功 crop、阶段尝试、测量和历史资产不改。仅打开不迁移；旧 v3 严格暂停和
  v4 部分 Fig 继续的直接调用仍兼容。完整已完成旧项目不自动升级或重算。
- v5 未完成裁剪时禁用后续界面入口、项目快照/灰度表导出；保存工作草稿可用。
  修正后只重新执行该行与依赖项。独审预检指出独立输出适配器也需同一v5门槛，
  已补发布前统一校验；v1–v4 历史快照 API 行为保持。
- 契约：docs/contracts/wb-intake-workflow-v5.md。算法实现由同任务另一并行分工处理，
  本记录不代表科学裁剪准确率。

## 命令与结果

1. `uv run --locked --no-sync pytest tools/wb/tests/test_intake_crop_barrier.py tools/wb/tests/test_intake_sequence.py tools/wb/tests/test_intake_workflow.py -q`
   首轮 exit1：26过2败，新增 fixture 仅写 needs_review 阶段未建立定位失败证据，
   真实 review_intake_crop 拒绝该状态。使用 fail/record 公共用例建立合法未定位证据，
   保持产品校验不变后，同命令 exit0：28 passed / 2.10s。
2. 一次 Qt 批次运行以下四个节点，exit1：3过1败 / 12.47s：
   - tests/test_intake_delivery_ui.py::test_v5_blocks_downstream_modes_until_all_original_crops_are_saved
   - tests/test_intake_delivery_ui.py::test_new_batch_can_continue_ready_groups_despite_another_review
   - tests/test_instrument_intake_desktop.py::test_v5_attempts_remaining_crop_then_pauses_before_any_fig_or_output
   - tests/test_instrument_intake_desktop.py::test_v4_blocked_first_fig_keeps_second_running_then_repairs_without_repeating_success
   使用命令 `uv run --locked --no-sync pytest <上述四节点> -q`。新 v5 worker 测试
   已运行到正确禁止导出；失败为断言读 native label，而命令错误实际存于
   bridge.snapshot().status。改为检查真实页面快照，未移除拒绝断言。
3. 仅重跑新 v5 节点 `uv run --locked --no-sync pytest tests/test_instrument_intake_desktop.py::test_v5_attempts_remaining_crop_then_pauses_before_any_fig_or_output -q --tb=short`，
   exit1 / 33.26s。读取其已保存 revision19 草稿确认：两行 crop 已 done，成功行
   compose/measure done，修正行因过长测试标签在25像素高显示 ROI 中不能容纳而
   compose failed，故 v5 正确阻止最终 export。保留产品标签约束，把合成标签改为 P1。
4. 仅重跑上述节点，附 `--show-capture=no`，exit0：1 passed / 7.41s。断言覆盖其他
   crop 完成、所有下游阶段 attempt=0、显式导出拒绝、修正后完整输出、成功 crop
   资产和步骤原样复用、两张合成原图字节不变。没有扩大等待时限。
5. 只读真实用户快照 `.local/T081/user-latest-project.json`，使用 read_figure_project、
   adopt_intake_crop_barrier、approve/claim 公开用例，exit0：v4→v5 后除workflow外
   全部载荷相同、阶段历史完全相同；全批裁剪未完成，compose/measure/export
   领取全部为 None；源 JSON 字节未改变。不改用户原工程/N。
6. `uv run --locked --no-sync ruff check`（本分工Python源文件与定向tests清单）最终
   exit0，All checks passed；先前新增代码排版/一处缺失import错误已按实际规则修复。
   `uv run --locked --no-sync pyright`（同工作流/桌面/诊断/定向tests）exit0，0 errors。

Qt日志出现既有 SKIA/mailbox 提示，未宣称GPU根因已修复。未运行全量本地测试、
独立审查、远端必需检查、构建或新安装验证；这些由T081后续阶段负责。

## 发布API预检修正

非作者预检发现无ticket的 export_intake_outputs、先归位后检查的
finalize_intake_delivery、export_intake_table 可绕过宿主v5门槛。统一接入
require_intake_crop_barrier，在任何发布写入/创建目录前拒绝；宿主复用同一用例，
避免两套条件漂移。materialize 仍可归位原图和已完成raw裁图。

`uv run --locked --no-sync pytest tools/wb/tests/test_intake_crop_barrier.py::test_v5_public_publish_apis_reject_before_writing_but_v4_keeps_partial_outputs -q --tb=short`
首轮exit1：三发布API拒绝且目标不存在断言已过，后续“允许阶段归位”的测试没创建
合法输出父目录，触发原有父目录校验。补上归位控制阶段所需父目录（在拒绝断言之后），
未改产品路径校验；同命令exit0：1 passed / 2.24s。
该用例真实调用三发布器，对v5检查新目标不创建、已有阶段目录全部文件字节不改，
对v4确认三个发布器仍实际输出部分结果；同时确认v5原图/已完成原值裁剪阶段归位可用。
没有运行Qt或全量测试。

## 真实 180 目录页面流程与导航诊断

主执行者在同一 Windows 活动树使用实际 180 原图、原工程相同的 `(1)` 来源选择，
在新工作区按用户明确修正的 Fig 1 N=4、Fig 2 N=2（另两组保持 N=5、4）验证。
不修改原工程，前后核对原图 SHA-256。以下为真实 Qt/WebEngine 页面与 worker，
运行环境为 `QT_QPA_PLATFORM=offscreen`、
`QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu`，不等同于干净 Windows 安装验收。

实际命令由主执行者提供：

```powershell
$env:QT_QPA_PLATFORM='offscreen'
$env:QTWEBENGINE_CHROMIUM_FLAGS='--disable-gpu'
uv run --locked --no-sync pytest .local/T081/test_actual_180.py -q --tb=short *> .local/T081/actual-180-ui-test.log
```

同一 ignored 脚本先后修改了诊断启动方式，各轮使用独立输出目录；不能用最终脚本
反推此前代码。以下以各轮保留日志、project/status/page-failure 为准：

- `actual-180-v2-test.log`：exit1，1 failed / 62.43s。直接 bridge 启动，9 crop、
  4 compose、4 measure、export 已完成且完整目录存在，但等待页面自动进入 results
  的 15 秒断言超时；该轮不能记作完整页面验收通过。
- `actual-180-v3-test.log`：exit1，1 failed / 64.32s。增加初始 session route 接收等待，
  仍直接 bridge 启动；处理和输出完成，页面仍停 intake。保留的
  `actual-180-v3/page-failure.json` 显示 automation follow/complete 为 true，
  follow 按钮为“跟随当前阶段”，无本地分组/裁剪/拼图/定量草稿，抽屉已关闭。
  v2/v3 均使用上述 pytest 入口及参数，日志分别保存于各轮名称。
- `follow-trace-test.log`：exit1，1 failed / 36.88s。短诊断在等待 follow 按钮文字时
  超时，脚本未在 finally 保存调用栈，故没有得到可确认根因的 trace。
- `actual-180-ui-test.log`：exit0，1 passed / 51.95s。通过页面控件填写 4 个 Fig 的
  N/蛋白、选择 9 个实际来源，聚焦并点击实际 start 按钮；无需手动确认裁剪，
  9 crop、4 Fig 成图、4 组测量与最终导出完成，页面自动到达 results 且不 busy。
  已确认完整拼图 PNG/TIFF、灰度汇总 XLSX/CSV、项目恢复 ZIP 和 index.json 存在，
  输出 complete=true，原图字节未变。证据为 `.local/T081/actual-180-ui/accepted.json`、
  `project.json`、`status.json`、`results.png` 及该工作区 outputs。

**导航根因：UNKNOWN。** 静态检查发现系统 route/状态回调也可经 switchMode 调用
noteBrowse，且“收到 route”未证明 route token 已消费；这些仅为候选解释。
正常 DOM 启动已通过，不据此把 direct bridge 失败归因为已证实的竞态，也没有为
这次诊断修改产品导航。此前失败目录和日志保留，未把失败改写成通过；本轮结果也
不证明“80% 独立项目全部自动通过”的科学准确率。

## 测试截图输出隔离

`tests/test_intake_delivery_ui.py::test_visible_delivery_controls_and_unsaved_layout_guard`
此前固定写入 `.local/T080/delivery-ui`，后续重跑可能覆盖 T080 历史截图。现仅增加
`tmp_path: Path` fixture，并将输出目录改为 `tmp_path / "delivery-ui"`，使宽/窄页面
截图分别留在本轮独立临时目录；产品动作、截图保存断言、布局和草稿门禁断言均不变。
这两行测试改动之后本分工未运行 Qt 或全量测试，未宣称新的截图已生成。
静态检查 `git diff --check -- tests/test_intake_delivery_ui.py` exit0；
`uv run --locked --no-sync ruff check tests/test_intake_delivery_ui.py` exit0，All checks passed。
