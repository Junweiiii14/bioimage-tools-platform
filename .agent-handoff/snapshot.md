# Handoff Snapshot

- 更新2026-10-17；当前T-040真实多蛋白Fig验收，唯一状态work/tasks/T-040-real-fig-validation.md。总体T003/WB未科学验收完成。
- 活动树C:/Users/70236/.codex/worktrees/t021-coordination/bioimage-tools-platform；codex/t040-real-fig-validation；产品f7a6651。旧主目录dirty及.impeccable/questions保留。
- 用户授权只处理8张(1).tiff，4Fig各2蛋白(N8/4/8/4)，标准960×1200N TIFF按蛋白名放原目录，原像素定量，命名冲突不覆盖。验证目录只读评分。
- 首轮纯自动冻结并独审：1/8=12.5%，7fail。N/Marker/倾斜截断问题尚未由本任务解决；不可用后续参考辅助纠正8/8冒充自动成功。
- 参考辅助注册8/8视觉通过，NCC0.99786..0.99977；原图/参考hash不变。标准显示文件8/16位保持且禁止quant导入，native crop切片逐像素一致。
- 实际桌面4Fig+48值+Excel/CSV+4高res标注图+ZIP已跑通。独审发现17/48旧自动bounds/baseline切穿主峰，另存明确整窗监督修正版，48与独立原像素整窗公式一致。33quality_review/15valid，全部actin有0平台，曝光线性未知，不做默认归一化。
- T041显式standard_lane_ratio@1与DisplayFrame仅显示、source_to_output回源，native默认/冻结manifest保留。P1分段复用整行frame已限制仅整行可用；88专项及31后续通过，独审至f7a6651无未解发现。
- .local/t040含首轮冻结、audit、诊断、delivery-report.json(最终workspace/output/supervised_output)、验证JSON及真实截图；用户可见输出在WB资料中新结果目录，原目录仅新增8标准裁图。脚本finish/supervise均exit0；Excel48单元格及ZIP8frame复读通过。
- T040实际执行已交付，桌面PID32064可见8原图/4Fig；.local/t040/opened-desktop.png已目视核验。全check虽600passed但exit1，原因UNKNOWN，不宣称全门禁通过；独立wheel另记。下一步排查测试退出异常并修科学自动化。未来优先修原图膜/倾斜/周期泳道与自动bounds，不能继续以UI或合成数据替代科学验证。PR/main/干净Windows未做。

- 用户要求原因推理与尝试方案，已核对原图诊断/首轮审计/48profile及源代码；归因与分阶段消融方案补T040末节，本轮未改算法。膜阈值、倾斜和边界选择问题有证据；最近原始profile局部极小值及向内收紧已由17/17重放定位；零平台来源及退出异常仍未知。

- 深度报告work/evidence/T-040/deep-technical-limitations.md（17节/逐层代码索引）已三路复核；新probes均exit0。明确最终参考辅助/监督脚本尚未产品化、默认先量后拼、CSV2位舍入、像素/厘米DPI区别、高res临时内嵌参数超限；>2048缩略manifest风险本次未触发。本轮无产品修复。
