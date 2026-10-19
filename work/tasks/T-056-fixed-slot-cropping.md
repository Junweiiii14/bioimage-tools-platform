# T-056：E3固定N几何与原值裁剪

- 状态：implementing；base733ea17，前置E2产品b4b519f/822全门禁与独审通过。
- 授权：连续E0–E7，无阶段重复批准、不设定时任务；仅最新t051树/codex/wb-e0-e7。
- 范围：tools/wb、apps/desktop、tests、tooling/installed_wheels.py、docs、.impeccable、PRODUCT.md、DESIGN.md、AGENT_HANDOFF.md、.agent-handoff、work/tasks/T-056-fixed-slot-cropping.md及work/evidence/T-056。
- 目标：从确认清单显式N建立独立稳定槽位；只读分配原图并复用source_geometry@2定位。完整保存膜/Marker/候选/原坐标/来源/策略和复核状态；无可靠几何不强行均分为成功。不推断跨蛋白样本顺序，不把弱/无信号当未上样或有效零值。
- 实施：先纯类型/用例/原值适配和schema版本，再宿主串行裁剪与候选复核/重试；绑定E2票据与CAS，先结束冻结输入票据再合并执行器产物，旧回复/取消不安装。实际定位在后台，原值TIFF与显示产物分开，无OCR/提前测量。
- 兼容：新字段采用显式项目版本，旧schema1–11读取保留，已有结果不覆写；旧策略不静默迁移。复用既有export_crop的原样本写后核验与无覆盖发布。
- 验收：固定N包含首尾/连续/全空槽，Marker不占槽；弱信号/无Marker/不等距/斜膜/多曝光/同图多区域证据不足保留待复核；同名行/来源修改/取消/旧票据/保存失败/重开；已知坐标像素精确裁剪和位深/元数据原图不变。无独立真实标注，不声明自动接受准确率。
- 版本/阈值：沿用source_geometry@2的已版本化检测，不调其科学阈值；新固定槽位封装独立策略intake_crop@1。候选默认未经人工审核；只在明确复核后允许本行crop done。
- 验证：相关性质/数值/真实存储和Qt回归，schema变更完整门禁及隔离wheel；最终提交非作者独审与界面适用证据。旧Qt purecall来源UNKNOWN，若再现停止本阶段门禁并诊断，E6另处理已观测旧fixture残留。
- 未完成：全部实现/验证/独审；E4完整Fig拼图后定量及E5填表/总输出不在本阶段伪造。
