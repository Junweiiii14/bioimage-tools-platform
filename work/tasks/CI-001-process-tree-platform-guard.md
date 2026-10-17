# CI-001：进程树清理的跨平台类型分支

- 状态：in_progress；T043分阶段远端CI修复，用户已授权完整门禁修复及安全同步。
- Linux严格类型检查发现close中访问仅Windows初始化的_kernel，历史阶段2–8同源失败；Windows检查不暴露此问题。
- 最小修复：close明确限定Windows句柄分支，保持Windows Job Object实际关闭及POSIX无句柄语义，不加类型忽略、不改变检查配置或预期。
- 验证：Linux目标Pyright、Windows目标Pyright、真实进程树取消/清理回归、绑定提交独审；最终开发树再次完整检查。
- 各阶段精确base与集成清单随实际前置更新，历史回执/失败日志均保留；原图和旧结果不动。


状态更新：本地实现、绑定独审、阶段传播与最终完整门禁完成；各远端实际Linux/Windows检查以PR实时为准。
CI001之后最终产品树fa9c5f2正式完整check实际exit0：657passed/451.28s，全部隔离wheel含真实OCR完成。日志.local/t043/check-final-ci001.log；文档后继与此产品内容相同。
