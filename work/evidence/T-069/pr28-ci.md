# PR28检查与后继取证

b99aac43e3234223d619188fc862e981fa8239c4已通过最终集成只读独审（产品与fb95c91一致、发行与745d043一致，唯一T069回执/base5729cb8/23文件覆盖，独立rule check0），但首轮CI未通过。quality39428192375：Windows118646002913为954通过/1失败709.15s、child1，wheel未运行；仅grouped CLI报告120.094秒失败，完整数值/原值裁剪/worker/输出/重开/恢复/owned清理均完成，缺shortcut-settings。原报告覆盖phase，不能区分focus/open/save，也不能凭GPU警告认定图形故障。原日志.local/t069-pr28-windows-first-failure.log。

Linux118646002881：grouped CLI通过约6.7秒；后继test_accidental_new_entries_can_be_removed_without_losing_other_edits_or_sending_crop_undo已PASSED，fixture tests/test_intake_web_ui.py:466关闭等待挂起。后台Python栈StorageWorker.retire:116(moveToThread)，main在qtbot.waitUntil/tooling.qt_test_lifecycle.py:45；15分钟取消，整命令未通过，无实际故障时C++锁栈。原日志.local/t069-pr28-linux-first-timeout.log。不是PR27旧test_local_page_channel_and_drain路径，不混同根因。

## 快捷键就绪条件与可观测性

源码确证：诊断25ms轮询且只等待host idle/网页focus+catalog；bridge状态发布180ms后再异步入DOM，因此不蕴含网页busy=false。原键可被真实busy/modal/drawer/input/IME保护拒绝，单次发送不会重放。新增真实Qt键对照经实际WebChannel先交付busy快照：旧就绪条件仍true、新ready false，真实K被拒绝且记录busy=true；交付idle后未自动重放，再发单次Qt键才打开真实设置。此机制复现不证明旧CI具体trigger。

新诊断等待DOM同project/epoch、focus/catalog/idle且原modal/drawer/input/IME保护就绪，仍只发一次Qt键；保存和精确重载要求、120秒界限均保留，未改产品按键保护。报告schema1兼容增补failed_phase/shortcut_probe，window capture先于document stopImmediatePropagation记录真实事件。初始探针直接返回JS对象在本机PySide回调得空字符串，作者两项失败/128.61s、实际1；完整失败报告.local/t069-shortcut-probe-object-failure.json保留。改用JSON字符串传输，不改ready真假或成功预期。

传输修正后对照+真实CLI两项15.31s实际0；补保存回调观测后快捷键/诊断两文件共15项40.62s实际0（.local/t069-shortcut-ready-related.log），Ruff/格式/Pyright/policy实际0。没有重跑真实私图或本地完整门禁；数值、调度、后台销毁、依赖和断言期限未改。旧Windows原因仍未证实，等新回执。

## 手动完整前驱原生取证

原失败单项及同文件前五项未复现PR27关闭挂起，新PR28另一个fixture也在retire线程迁移挂起。新假设是全套前驱/进程状态；手动suite只执行原完整pytest，所属GDB660秒后SIGINT采全部线程，20秒宽限、超时恒124，原debugger码保留。手动job从6分钟改15分钟以容纳660秒取证，ulimit core0；普通PR/push命令、四必需contexts、15分钟时限及测试断言均保持。诊断不是门禁通过的替代。新运行前先沿用外部cancel控制。尚未执行suite，不声称root cause或修复。
