# T081 首轮CI与精确验收策略迁移

PR42初始HEAD `1eb780c45f0d21dfe47f36479367197416ee6793`，独审Accepted后运行真实required CI。规则和桌面环境success；Windows foundation **2 failed /1289 passed /688.02s，exit1**，轮次39968732556/job120465414553。完整日志ignored `.local/T081/package/ci-windows-initial-job.log`，未把失败写成功，wheel未执行。

两个失败都在完整流程done之后：正常GUI测试仍严格要求 `intake_crop@3`；安装自动流程诊断也拒绝新crop@5。诊断记录已有9个stage事件与最终完整输出，不能将GPU/mailbox伴随日志推断为失败根因。按新workflow@5契约将这两处精确期望改为@5，不扩大接受版本集合、不删除原值/固定N/未人工确认/worker/结果页断言。

限定复验：offscreen/disable-gpu，`uv run --locked --no-sync pytest tests/test_instrument_intake_desktop.py::test_reliable_sequence_needs_no_crop_confirmations_and_shows_images_and_table tests/test_intake_diagnostic_lifecycle.py::test_automatic_flow_diagnostic_checks_unattended_crop_and_visible_images -q --tb=short`，**exit1，1passed/1failed16.60s**。GUI已过；诊断后续仍精确要求旧 `instrument_guided_geometry@2`，继续拒绝新版guided prominent。将第三处精确期望改为 `guided_prominent_band_geometry@1`，保留倾角、同组引导方向、原uint16逐像素检查与全部后续断言。

再仅跑上述 `test_automatic_flow_diagnostic_checks_unattended_crop_and_visible_images`，**exit0，1passed9.08s**，`.local/T081/package/policy5-guided-focused.log`。两次限定复验合计确认两个原失败路径均通过；不重复全量。算法、裁剪/调度/发布产品逻辑和依赖/门禁没有因此改变，真实180无需重复计算；新准确提交仍须独审与四项required成功。

当时Linux同轮尚在运行，最终状态以GitHub真实收据为准；若新HEAD触发服务器默认concurrency取消旧轮，记cancelled，不能记通过。首次gh run view对未完成整轮取job日志失败，改用job/logs取得完整Windows日志；先前运行中Linux job/logs为404 BlobNotFound，不作为测试结果。
