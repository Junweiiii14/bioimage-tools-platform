# CI-007：原生诊断辅助函数平台边界

- 状态：in_progress；T043既有CI修复授权。
- bbf3cc5远端Linux job117368898962在Pyright报告windows_native_stacks.py:78的4项WinError/get_last_error平台属性错误，尚未运行Linux pytest；Windows仍在运行，保留当前作业不人为取消。
- 仅为_processes辅助函数补显式非Windows拒绝，保持现有capture/_capture_process入口拒绝，避免Linux类型分析进入Windows专有属性；不改类型配置/ignore/依赖/退出/时限或产品行为。
- 验证诊断与dev环境8测试，Windows及Linux目标模块类型检查，绑定提交独审；产品完整门禁仍绑定a811ccfd的668/508.54秒exit0，明确不冒充新Linux完整通过。

- 实现1021662绑定独审无阻断，作者8项2.07秒0、两平台模块类型0；审查者独立两平台类型0。远端新候选待推送/完整复验，保留bbf Windows当前作业。
