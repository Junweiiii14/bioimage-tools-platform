# Handoff Snapshot

- 当前任务唯一状态：[T072](../work/tasks/T-072-automatic-flow-repair.md)。用户2026-10-21批准六项试用反馈修复，完整方案已登记活动目标，持续到独审、PR/main与新离线测试版。
- 新树 C:/Users/70236/.codex/worktrees/wb-auto-flow-repair/bioimage-tools-platform，分支codex/t072-automatic-flow-repair，基线main975942de。旧主目录27份dirty、旧grouped树10份dirty、T071树clean的HEAD/status/SHA清单在新树.local/t072/preserved-worktrees.json；未改旧树、原图/历史/安装。
- 当前已实现草稿：intake_crop@2自动采纳和人工review分离；已有倾角接入显示框；手动显示角度/恢复；独立有界只读Fig预览，灰度页图片与原坐标区域映射；结果页显式全宽表格/导出入口，收拢常驻说明。未提交/未最终独审/未全门禁/未打包。
- 已验：新增12核心反例0；真实两Fig自动链不需手动确认、10表格记录、灰度图片/5区域、Excel及原图保持；加原暂停链/修正提示共3项17.66s0。首扩展回归72passed/2failed保留（修正提示缩短、序列现场）；后继三项通过不覆盖早期GPU context lost日志。新测试初次误放参数装饰器导致collection1已修正。Pyright曾0，最终改动后须重跑。
- 最新：原信号无膜轮廓19组源图单独0/19；新增instrument_guided_geometry@1初稿13/19但独审发现方向、多膜、近邻双排和标准高度吞目标四问题；已修复，13专用用例及独立扩展反例通过，保守4/19自动其余暂停。原图不变；13旧结果不可当有效能力。导向源码隔离自检9槽/两Fig/图表/退出0。
- 下一步：完成预览异步/视觉验证、更新证据，最终提交独审→完整门禁/四CI→新独立离线包。targeted-v4出现GPU context lost/停滞，核对PID后仅终止本轮pytest；v5改软件渲染运行，未削弱断言。不得将合成通过称科学留出；不操作用户正在使用的旧安装窗口。

## 上次交付（历史指针）

- 当前状态唯一来源：[T071](../work/tasks/T-071-fig-sequence-automation.md)。用户批准完整T070方案与持续实施；完整方案已登记目标，没有待答数据问题。
- 活动树C:/Users/70236/.codex/worktrees/wb-fig-sequence/bioimage-tools-platform，文档收尾codex/fig-sequence-delivery。产品PR30精确head5f2090a四必需检查后正常合main710bb85；二进制冻结该main，收尾不改产物来源。
- 新桌面目录BioImage-WB-Fig顺序自动化测试版-T071已生成，当前用户独立安装/新快捷方式已建立，三流程实际OS0、PS5.1随包三自检0、7,751载荷文件摘要一致。最终非作者交付审计Accepted；本次文档PR仅整理已完成事实，四检查集成后完成目标，无后续获批产品实施待办。交付摘要与证据见[记录](../docs/wb-fig-sequence-delivery.md)。
- 旧wb-grouped-intake/codex/fig-sequence-plan的10份dirty文件SHA、HEAD/status与旧T069三关键文件SHA不变；原图/历史结果和其他树保持。T069仍冻结6080867，不自动删除/升级旧安装。
- 当前85TIFF/19执行组＋28参考组、74槽是已见参照辅助回归，不是科学留出。旧native/手动坐标UNKNOWN、干净Win10、物理按钮/DPI和独立科学真值继续保留；无正式Release/依赖升级/新工具扩展。原失败与源码/包态界限见T071 evidence，勿据后继成功销账。
