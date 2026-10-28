# R09 首轮快照优化

动机来自准确基线244c5da的四场景实测（r09-results.md），不是推断180ms轮询每次重建。两个上界的热构造/JSON、点击、载荷和内存均超预设调查线；两小例与idle保持线内。先做局部索引和重复传输消除，没有降低样本规模、缩略图质量、结果数量或阈值。

- 以rowId一次索引cells，替代每行扫描全部cells；全局/每行次序、有效零/缺失/失败及row摘要保持。
- 完整cells只传一次，rows不重复results；网页setState一次Map回填引用，显式旧results及无cells的旧partial输入保持原处理。没有合并quant.table，其待配置状态与cells原始积分语义不同。
- 仪器来源复用公开intake_snapshot已生成的sources，避免第二次model_dump；仪器/行的同SHA显示PNG经既有sourcePreviews传一次，网页恢复preview。独立高分辨率zoom不改，无新图片服务器/缓存框架。
- 显式显示契约见`docs/contracts/wb-workbench-snapshot-v1.md`；只改显示wire，持久项目schema、科学定义、保存和导出不变，旧完整/演示输入仍支持。

新增3个真实WebChannel测试 **3 passed/4.64s/exit0**（`.local/T082/r09-compact-ui.txt`）：结果顺序、0/None/失败/rawIntegral、共享引用、旧显式结果、跨epoch渲染失败回滚/恢复与草稿保持、两来源/两行实际图像naturalWidth及独立zoom。后端新增全局次序/孤立历史cell保留及row摘要断言；既有intake重开测试由inline读取改为shared引用可解析，并加强为等待实际三个缩略图naturalWidth>0，不是删去图像行为断言。

联合命令：`pytest tests/test_workbench_snapshot_compaction.py tests/test_web_bridge.py tests/test_instrument_intake_desktop.py tests/test_intake_web_ui.py tests/test_web_boundary_diagnostics.py tests/test_group_review_workbench.py tests/test_quant_session_identity.py tests/test_project_navigation_session.py tests/test_workbench_lifecycle.py tests/test_workbench_advanced.py -q --tb=short`，**141 passed/153.89s/exit0**（`.local/T082/r09-compaction-regression.txt`）。锁环境及进程局部软件渲染，已有mailbox诊断保留。Ruff/严格Pyright、JS门禁及4负例通过，无skip/xfail/容差/门禁削弱。

非作者只读预审未发现阻断；独立Node VM取原244c5da与新setState函数，50组紧凑/旧完整、显式结果及partial输入比较等价，包括特殊rowId、顺序、失败、零和orphan，确认共享引用且不回写旧state嵌套对象。预审未运行GUI，尚不是准确提交Accepted。

准确提交独审及同输入/环境/预算性能复测待执行；不能宣称已达预算或将R09结项。baseline及全部原始警告保留。
