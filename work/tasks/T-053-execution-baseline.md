# T-053：E0执行基线与集成/验收地图

- 状态：done（E0工程基线；真实仪器标注与目标机验收仍待后续）
- 日期：2026-10-19
- base commit：536f04eed4de72d9a9a7c8eb6b7afbf065f7be15（产品65ff278）
- 授权：用户批准E0–E7连续实施，各阶段验证和非作者独审通过后自动进入下一阶段，不设定时任务。
- 依赖：T-052已交付计划；保留其所有既存未提交文件。
- 范围：docs、work/tasks/T-053-execution-baseline.md、work/evidence/T-053、.agent-handoff；仅修正文档事实和建立基准/验收地图，不改算法、格式、依赖或门禁。
- 必读：根AGENTS，T-052执行计划、T-050需求v2、T-051任务与契约；architecture/module-map、各现存包README与公开API。
- 目标：正确源码/运行/安装入口、远端main/产品提交关系、消费者与兼容矩阵、独审覆盖缺口、可复验性能测量协议。真实真值缺失不猜测。
- 验收：doctor/smoke-env/启动路径验证、policy、文档链接及diff检查、绑定提交独审；保留历史Qt根因UNKNOWN，下一任务E1。
- 回滚：仅撤销本任务文档提交，不触碰原图/结果/旧树/T-052已有成果。
- 独审：independent_review绑定c57bfcf..1bbd91d，无阻断，允许E1；性能溯源建议在631b059补齐并经增量复核关闭。

## 实际执行

- 批准计划单独保存c57bfcf，原位新分支codex/wb-e0-e7；产品不变。
- 完成execution-baseline消费者/兼容/远端集成/科学缺口及性能协议；纠正architecture与module-map过时状态。
- doctor/smoke-env/启动verify、28项入口/清单测试、20次API新进程导入、policy/diff均0。日志与计时见work/evidence/T-053。
- 独立真实留出未冻结，已记录10670059混合来源不得充当未整理仪器样本；不阻塞E1纯计划。
