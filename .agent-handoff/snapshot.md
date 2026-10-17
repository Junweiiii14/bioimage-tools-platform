# Handoff Snapshot

- 更新2026-10-17；任务唯一来源work/tasks/T-043-gate-repair-and-staged-sync.md；T-003科学与发布验收仍未完成。
- 当前活动树C:/Users/70236/.codex/worktrees/t021-coordination/bioimage-tools-platform，codex/t043-gate-and-staged-sync。原ResearchVault主目录是dirty历史检出，保留全部原改动，不能用于当前产品启动。
- 正常入口：桌面“BioImage WB 工作台（当前开发）”→活动树Start-BioImage.ps1→绿色WebWorkbenchWindow。无参及历史--figure-project/--platform统一当前工作台；旧Qt窗仅显式legacy诊断。不要用历史树或兼容测试窗演示当前产品。原生CUA按用户停止决定不重启。
- T043产品2e5021d修复默认入口、失败弹旧宿主及测试可见旧窗；网页HTML/CSS未改。14新增测试/绑定独审通过；完整check真实exit0，642项/361.62s及隔离wheel完成。
- 原生交互式间歇挂起仍UNKNOWN。原628全check停止exit1、后续分跑、未改生命周期时628完整exit0及压力诊断均保留；不能据离屏成功宣称已定位原生锁根因。
- 治理前置0b786cb/草稿PR7：显式历史清单，当前scope/base/rules仍完整检查。独立44项完整check/165.88s/exit0，独审6拒绝路径exit0；首次缺venv失败保留，原锁环境安装后通过。远端4项CI成功。
- 八产品阶段整理完成且独审通过；产品快照一致，8份清单均exit0。T007/T026真实重载且保留旧blob。阶段表.local/t043/stages-built-v2.json；远端阶段PR与最新状态见T043任务/管理记录。
- 合并治理后的最终开发树完整check真实exit0：657passed/427.30s，全部隔离wheel完成；日志.local/t043/check-final-integrated.log。后续仅文档/回执整理，产品代码未变。
- main仍221a2df，禁止一次合入累计历史；开发分支已推送f9ef161。现有PR3保持草稿，机器人PR4/5不动。没有合main或发布动作。
- 仓库外bundle及19树补丁/未跟踪tar已验证；34个原有未提交文件哈希保持；6个干净无.local历史树原位锁定分类，未删/移目录。dirty和结果树保持原位。私有路径仅.local，管理记录work/evidence/T-043/repository-management.md。
- T042 source_geometry@2/background_support@1接现有工作台；8原图推理、参考只评分，旧1/8→新8/8，非留出。8原图/12参考/旧成果SHA保持。48槽7valid/41quality_review，没有积分真值。网页导出/保存重开/48DOM结果exit0；详见T042证据，不重复注入本地结果。
- 开发日志Issue6已发布并回读；待补入口/门禁/阶段PR结果。下一步：完整门禁→最终文档/清单→阶段草稿PR/CI→二次refs备份和交接容量检查。
