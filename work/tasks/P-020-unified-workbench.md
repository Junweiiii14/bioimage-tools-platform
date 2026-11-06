# P020 统一工作台与 BCA 桌面 MVP

<!-- PROGRAM_TASK_META {"id": "P-020", "status": "done", "work_package": "W05", "depends_on": ["P-009", "P-016", "P-019"], "execution_root": "C:\\Users\\70236\\ResearchVault\\Codex-Workbench\\bioimage-plan-sync", "owner": "chat-01a1b02f-dc63-7573-94bb-014c0cb2aadc", "base_commit": "1c819aeaae9813fdc29606cbad463b08a191fbab", "head_commit": "0d83f4dc75804e90291d408302027fe590286fdf"} -->

状态：工程范围完成。PR72已合入main aa3302ad2980dfeec1ac6f7776fec6176f18fcda，与最终已审0d83f4dc75804e90291d408302027fe590286fdf树一致；最终独审及全部必需CI通过。

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

## CI 重开等待修正

c9a4d42指定增量独审pass；Windows CI唯一旧重开测试在空宿主idle窗口提前返回，Linux完整通过。已用250ms延迟探针实证原条件失败/界面未宣告成功，只增加目标workspace身份等待，保留20秒及业务断言。定向15通过；详work/evidence/P-020/ci-reopen-wait.md。新测试候选待准确增量复审/必需CI，不合入未通过提交。

## 最终验收

详work/evidence/P-020/final-delivery.md。Windows1767pass、Linux1763pass/4既有skip及两平台wheel/check --all成功，rules/desktop通过。指定三份独审原报告保留，R01/R02与等待条件增量闭环。一次本地收尾随下一任务带入，树释放；下一任务上游新窗口。科学/真人/IME/DPI/目标机/安装未验，用户旧安装未替换。
