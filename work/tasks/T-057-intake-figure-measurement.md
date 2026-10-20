# T-057：E4完整Fig持久化后原像素定量

- 状态：done；base1719a2d，E3产品32da9f4已获绑定独审/832全门禁及隔离wheel与真实OCR通过。
- 授权：按docs/wb-execution-plan.md连续E0–E7，不设定时、不重复索批；仅最新t051树/codex/wb-e0-e7。
- 范围：tools/wb、apps/desktop、tests、tooling/installed_wheels.py、docs、.impeccable、PRODUCT.md、DESIGN.md、AGENT_HANDOFF.md、.agent-handoff、work/tasks/T-057-intake-figure-measurement.md及work/evidence/T-057。
- 目标：按manifest稳定Fig/行/槽位成图，不因无图或失败挤位。每Fig全部已审核原值裁剪后可成图，持久化真实成图后才发起所属原像素worker；其他Fig异常不阻塞就绪Fig。
- 实施：版本化schema13的Fig成图依据与请求身份映射；复用现有渲染、明确原图坐标/锚定背景策略、ProjectMeasurementSession和RunSession，不增加第二成功收据。活动票据输入不可被逐行run安装改变，终态票据校验后统一合并已核验运行。先持久化claim再执行，取消/CAS/旧回复沿用E3保护。
- 兼容：旧schema1–12读取与旧结果不重写。新策略只用于新请求，不改数值公式/检测阈值，不猜跨蛋白样本对应；显示映射/重采样/缩放/旋转不进入定量。独立灰度/OCR继续正式保留。
- 验收：双Fig一坏一好；同名蛋白不同身份/槽位不串；真实原图SHA/ROI/参数与RunRecord对应，display参数变化原ROI不变定量不变；取消/旧票据/未提交成功/存储失败/源变/重开；成图点击回正确原行；全部门禁/隔离wheel与最终提交独审。
- 未通过边界：独立科学真值/仪器留出、干净Win10/物理DPI仍缺；不宣称科学准确率或完整产品/发布完成。旧Qt purecall来源UNKNOWN保留，E6精确所属fixture收尾。
- 进展：首批schema13完整Fig依据/原图请求/原子终态合并、显示成图适配、保存读取与资产恢复；17项核心2.85s、全仓Pyright0。当前宿主仍E3裁剪路径，未切换到E4。
- 进展：宿主已接真实完整Fig→CAS→RunSession与延迟合并、取消/失败/旧回复、重开核验；成图回源与只读结果UI接通。核心+桌面+前端31/33.68s，末桌面/前端27/32.89s，静态0。
- 最终产品候选df98166：宿主/核心独审及UI两P2修正复审通过，documenter No changes。相关代码审查/验证边界见work/evidence/T-057；最终完整门禁与隔离wheel进行中，未完成前仍implementing。

- 完成：最终产品ff898670bedcf1d7fe39b395a388595a8493450d；全量check实际0，843 passed/579.73s、原child0/u32=0、9契约/全部隔离wheel/真实离线OCR0。非作者代码审查绑定ff，UI两项resolved/ship与documenter No changes适用于未变UI。完整失败与限制保留在T057证据；下一阶段E5/T058，无需重新批准。
