# 原生诊断跨平台guard

bbf3cc5远端Linux job117368898962在Pyright失败4项，定位_processes里WinError/get_last_error仅Windows属性；pytest未运行。保留日志.local/t043/ci006-linux-failed.log，未将此前Windows本地完整668通过当作Linux证明。

仅在该辅助函数开头显式拒绝非win32，保持外层capture/_capture_process已有平台边界。没有type ignore、类型配置/依赖/门禁或产品退出协议变化。

本机Windows Python3.12.14，诊断/dev环境8passed/2.07秒/实际exit0；模块pyright --pythonplatform Linux与Windows均0 errors/0 warnings/实际exit0。Windows目标覆盖实际原生采集/退出码/归属，Linux目标只是静态模块证据，真实Linux完整检查仍需远端新候选。绑定独审后更新阶段清单。

不重复Windows产品完整测试：该guard在Windows分支为false，不改变已验证a811ccfd产品或Windows诊断实现；此前668/508.54秒及全部隔离wheel完整exit0保留绑定，新增诊断分支按相关测试复核。没有把定向结果写成新全量通过。bbf3cc5 Windows远端仍运行时保留作业，取得真实结论后才推后继。
