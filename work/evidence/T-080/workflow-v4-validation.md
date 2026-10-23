# T080 失败组继续处理 v4 验证

2026-10-23；P4 子代理扩展执行已批准 P3 的“失败项目的其他可处理组继续”。
环境与基线同 `delivery-validation.md`：Windows/PowerShell/Python 3.12.14，锁定项目
环境，基线 `2d2c9727ec93c7a625e46964696788f06f8f4834`，未自行提交。
作者自验不构成独立审查；最终提交、全仓门禁、私有素材和安装包验证由主任务绑定。

## 现状证据和实现

旧 `intake_workflow@3` 任意 needs_review/failed/cancelled/interrupted 会全局返回无
下一票据，并使 pending_ready 为 0。已有两 Fig 真实页面测试明确断言第一行待复核
时第二行 pending、后续阶段 attempt=0；这不是“失败组继续”的实现。

新增版本 `intake_workflow@4`，新批次配置默认使用，历史 v3 保持：

- 按原清单及 crop→compose→measure 优先序选择可执行项，保留各 Fig 本身依赖。
- 自动裁图需复核/失败、成图失败、测量失败只阻断依赖它的 Fig；其他 Fig 可继续。
- 当前可执行非导出项都退出后可领取 export 票据；部分结果继续使用真实导出核验，
  `complete=false`、errors 非空、export=failed，不把缺口变成零或完成。
- 修正一个缺口只重置它及其依赖，其他成功 Fig/运行保持；封存目录重试使用新代。
- 用户取消仍停止整批；票据/输入摘要/CAS/旧回复守卫保持。
- 应用层 revision/sequence/figure 复用、桌面自动接受/跟随/显示允许 v3/v4。
  主代理及旋转子代理分别处理网页、安装烟测和 `accept_automatic_intake_crop` 接点。

公开契约：`docs/contracts/wb-intake-workflow-v4.md`。

## 命令、退出码与范围

所有命令前缀 `uv run --locked --no-sync`。Qt 串行，环境变量
`QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu`，沿仓库 offscreen 配置。

| 命令 | 结果 | 退出码 |
| --- | --- | --- |
| `pytest tests/test_instrument_intake_desktop.py::test_v4_blocked_first_fig_keeps_second_running_then_repairs_without_repeating_success -q --tb=short --show-capture=no` | 1 passed，18.10 s | 0 |
| `pytest tests/test_instrument_intake_desktop.py::test_sequence_real_page_two_figs_pause_continue_stage_barriers_and_reopen tests/test_instrument_intake_desktop.py::test_reliable_sequence_needs_no_crop_confirmations_and_shows_images_and_table tests/test_instrument_intake_desktop.py::test_sequence_start_never_launches_before_exact_cas_commit -q --tb=short --show-capture=no` | 5 passed，27.79 s | 0 |
| `pytest tools/wb/tests/test_intake_sequence.py tools/wb/tests/test_intake_workflow.py tools/wb/tests/test_intake_execution.py tools/wb/tests/test_intake_output.py -q --tb=short` | 40 passed，8.03 s | 0 |
| `pyright <下列7个文件>` | 0 errors / warnings / informations | 0 |

静态精确参数：

```text
tools/wb/src/wb_tool/application/intake_workflow.py
tools/wb/src/wb_tool/application/intake_revision.py
tools/wb/src/wb_tool/application/intake_sequence.py
tools/wb/src/wb_tool/application/intake_figure.py
apps/desktop/src/bioimage_app/intake_workflow.py
tools/wb/tests/test_intake_sequence.py
tests/test_instrument_intake_desktop.py
```

新真实集成使用合成平图和有明显条带的第二张原图，从 WebChannel 顺序配置入口启动。
第一 Fig needs_review；第二 Fig crop/compose/measure 均 done，测量具有实际成功进程
与 RunRecord；部分输出有可恢复 ZIP/灰度汇总，完整标记为 false，未处理 Fig 没有
伪造测量。手工确认第一张原 ROI 后新代所有阶段 done、complete=true；第二 Fig 的
run、attempt、claim 精确保持；旧 ZIP 及两个原图字节不变。

旧 v3 严格暂停测试通过明确的历史策略夹具继续运行原页面断言；没有将旧测试全部
机械改为 v4。新配置单元断言改为 v4 是版本变化本身；旧 v3 领域 barrier/pause 测试
未改。CAS 失败/取消用例在新默认策略下通过。

## 失败与修正说明

- 新 Qt 用例首轮使用中文蛋白名而未配置字体，第二 Fig 正确在成图阶段报“需要导入
  相应字体”，且输出明确不完整。该用例要隔离“第一组故障、第二组正常”，因此换为
  ASCII 标签后通过；未改字体验证。真实中文标签成图仍需要有效字体，由主任务检查。
- 新纯阶段 schema11 用例误期望 pending_ready=1。既有 UI 契约只有 schema14+
  才能对外宣告可输出，故更正夹具预期为 0，仍验证后台下一个 export 票据和真实
  schema14 桌面的部分输出。未放宽低 schema 导出门禁。
- 类型检查曾报告测试从模块间接读取导入函数及 Optional 快照下标；已改为公开 API
  导入和显式 None 断言，无新增 ignore、skip、xfail。

上述最终结果不代表完整产品门禁/科学准确率/安装包验收已完成。测试后已通知主代理
Qt 空闲，停止启动 Qt，避免与后续真实素材/安装验证竞争。

## 独审发现的重开继续缺口

独审发现：v4 调度可跳过第一组 needs_review，但公共 `continue_intake_sequence`
仍先拒绝 needs_review，导致重开后 pending_ready 大于零却不能继续。现仅 v4 在
无新 crop 且存在真实 pending_ready 时原样返回当前快照，交由宿主保存/启动；不
偷偷 retry 待复核项。所有可运行工作退出后仍要求人工确认，v3 严格暂停不变。
摘要过期、活动阶段等既有前置约束不变。

公共 API 参数化测试分别覆盖 v3/v4：序列化重开、过期摘要拒绝、v4 不改首组状态
与 attempt、直接领取第二组，其他组也待复核时恢复人工提示。旧 continue 用例显式
保留 v3 夹具，以保留历史严格行为断言。

桌面真实集成用例补强为：首组 needs_review 已提交、第二组尚未领取时在调度边界
注入一次停止，重开同一工作区，再通过 WebChannel 的无 ROI continue 继续。第二组
完成真实运行和部分输出，首组状态/attempt 未改变；随后人工修复首组全部完成，
第二组运行、attempt、claim 不重做，旧 ZIP 和原图字节保持。

`uv run --locked --no-sync pytest tests/test_instrument_intake_desktop.py::test_v4_blocked_first_fig_keeps_second_running_then_repairs_without_repeating_success -q --tb=short --show-capture=no`：
1 passed / 10.21 s，exit 0，仍使用 `QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu`。
后端 delivery/sequence 合并 25 项 exit 0，详见 delivery-validation.md。
本轮静态 5 文件检查最终 exit 0，无新增 ignore、skip、xfail；测试通过后仅把测试
暂停点的反射引用改为类字典读取并格式化，行为相同，未再次占用 Qt。
