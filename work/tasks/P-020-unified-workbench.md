# P020 统一工作台与 BCA 桌面 MVP

<!-- PROGRAM_TASK_META {"id": "P-020", "status": "in_progress", "work_package": "W05", "depends_on": ["P-009", "P-016", "P-019"], "execution_root": "C:\\Users\\70236\\ResearchVault\\Codex-Workbench\\bioimage-plan-sync", "owner": "chat-01a1b02f-dc63-7573-94bb-014c0cb2aadc", "base_commit": "1c819aeaae9813fdc29606cbad463b08a191fbab", "head_commit": null} -->

状态：实现与定向自验完成，PR72首轮独审R01/R02修复后准备增量复审；本机全量中断，待必需CI。2026-11-06，上游授权独占 bioimage-plan-sync；基线 main 1c819aeaae9813fdc29606cbad463b08a191fbab，起点 6c06283190c044491c862d5961f9e3b9f6b800e9（P019 本地收尾保留）。分支 codex/p020-unified-workbench。

## 范围与退出条件

- 复用既有 DESIGN/token，WB、核分割、BCA 同骨架工具卡、准备状态和保留会话的导航；更新 PRODUCT 真实能力。
- BCA 选择 CSV、填写/加载必要板记录，真实 WorkflowSession worker→完整核验提交→逐孔/样本结果、原因、导出及新进程重开。固定 0.1.1 方法，无科学默认确认。
- 基本状态/来源/主操作一致；核分割实际准备帮助可打开，专业结果能力保留。
- 首页“工作流编排”进入 P009 真实画布，明确当前受支持节点；不承诺 BCA/核分割节点注册、完整可插拔或 Agent。
- 当前桌面源码入口真实回归，1440/960 及既有主题一次批量视觉检查、集中修正后最多一次确认；必要失败/取消/损坏/partial、焦点与中文输入回归。
- 冻结 base/head、自验/导航/截图和 PR，回传上游待独审候选；由指定独审窗口审查，上游安排正常集成，不自行另派重复审查或合并。

## 保护与未验

不改第三方算法、模型、冻结参考、方法语义、旧安装、原图、历史及旧 dirty 树；不新增依赖/门禁或后端功能。公开/合成操作不代表科学或真人验收；物理 DPI、目标机、安装未验保留。

## 验证记录

已完成真实 BCA worker/提交/导出/新进程重开/取消/损坏拒绝与导航回归；定向22+10测试通过，WB3测试通过，真实核分割46核及新进程重开通过。16张双尺寸/主题截图全部核对。全量check仍运行，初次格式失败及GPU中断不计通过。详 work/evidence/P-020/README.md；独审、CI、集成尚未完成。

## 首轮独审修复

3056334候选由上游派指定独审，回传R01身份误翻译、R02帮助链接空白，连同占用提示集中修复。定向17通过/15.36s，类型/格式/Web通过；旧单卡数量测试明确改为授权三卡，其他断言保留。完整本机check中断不计通过，CI与增量复审尚待；详work/evidence/P-020/review-fixes.md。
