# P-019 固定BCA单板CSV研究适配

<!-- PROGRAM_TASK_META {"id":"P-019","status":"in_progress","work_package":"W07","depends_on":["P-018"],"execution_root":"C:\\Users\\70236\\ResearchVault\\Codex-Workbench\\bioimage-plan-sync","owner":"Codex BCA adapter","base_commit":"3947261244143e3414b9bbf151bbe77c6edb5991"} -->

## 范围与验收

2026-11-06按上游持续授权新窗推进，已建无预算goal。保留2bfd40c收尾。实现P018 pierce25-point-v0-research的严格单板UTF8长CSV及必要板记录、逐孔扣空白/NumPy interp/预稀释/技术均值SD；独立bca_tool公开API，沿用WorkflowSession/Workspace真实worker、提交和重开。原文件/历史不覆盖；低高范围和partial留空。研究方法和科学限制保持，不扩GUI/通用孔板/拟合框架/依赖/安装发布。

透明合成输入经真实CSV/API/worker/提交/重开，独立核算P018关键数值及来源摘要。必要反例覆盖身份、非有限、非法曲线、范围、partial、历史保护、失败与取消不提交。补新包import-linter/独立wheel，已有必需检查不削弱。冻结准确候选/PR回传上游指定独审；修复留本窗，上游安排集成，不自行合并。完成后一次必要收尾、释放树、关闭goal。

## 当前状态

实现与36项定向测试、独立BCA wheel、真实CSV执行/重开已完成；作者自验见work/evidence/P-019/README.md。本机全量1757通过、2个既有旋转canvas超时，CI环境定向3通过、所有wheel通过，原失败保留，不称首次全量通过。待冻结准确候选/PR与上游指定独审，尚未集成/释放。B021四份完成收据已按白名单带入；原P018研究与2bfd40c收尾保留。
