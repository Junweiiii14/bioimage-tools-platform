# P016 完成条件审计

审计源码：16d32b12f3980cf2dcaeb3ec9d145488378c6dcd，base a7612843e5216f0471b51be93bd3687f0b8dbc82。当前结论：以下工程范围全部满足；最终CI/主线树一致性/正式上游回传已核验。科学与外部验收边界保持。

| 原始要求 | 当前证据与判断 |
| --- | --- |
| 正式登记、依赖、范围、任务/context；保护P015及原树 | P016任务卡、registry及rules/integration-context已提交；从2b1447a继续，当前树bioimage-plan-sync。没有在原dirty树、旧GUI、安装或原始输入上执行修改。通过。 |
| 当前工作台可发现入口，保持视觉，不全站重做 | index.html首屏单图核分割入口；nuclei对话框继承现有module组件/tokens；Impeccable context和一次detector，截图1440/960与独审。通过限定桌面窗口观察，非四主题/DPI普查。 |
| 环境准备后选择、运行、原图/轮廓/计数、导出、退出重开 | first-gui-run.json记录实际Computer Use原生选择和模型调用，46核；运行进程72364/44488均exit0。已提交Workspace只有同一run，导出一致。通过。 |
| 复用P015公共API与WorkflowSession/Workspace | nuclei_bridge调用nuclei_tool.api、prepare和WorkflowSession；nuclei_results仅读已提交资产；无新算法/执行或存储引擎。独审源码核对通过。 |
| 一句研究状态，缺依赖的设置与说明，保存路径，无安装下载 | index.html与nuclei.js的运行设置入口、自动展开缺设置提示；QSettings保存worker/model，默认轻量依赖不含模型运行栈；test_nuclei_web缺设置/入口验证。普通分析只按钮操作。环境维护按工具README准备，首次指南未内嵌是后续改进，不宣称学生验证。通过当前准备后范围。 |
| 固定unsigned uint8、单页单通道BlackIsZero/TopLeft，不猜测转码 | read_nuclei_input核验L/n_frames及258/339/277/274/262标签，明确拒绝；GUI16bit回归，P015既有准入测试。原图只读导入并核对SHA，无输入模式转换。通过。 |
| 显示与定量隔离，原坐标轮廓、切换/缩放，无调参编辑 | presentation只在原坐标uint32标签上构造RGB显示；request和provenance/hash/形状核验。prepare从原文件重新读入并导入真实资产，预览SHA变更即拒绝。工具零/非零显示测试及WebChannel缩放测试通过，截图可见原图/轮廓和缩放。通过。 |
| 最小计数来源表、可视化、保留整数标签，不覆盖 | export_result唯一UUID暂存目录完整写完才rename；CSV含计数/sourceSHA/execution/run/method，labels.npy/provenance原字节保留，README标明显示PNG。真实导出和独审逐字节检查、项目内导出拒绝通过。 |
| 重开持久化结果，不重新推理或覆盖历史 | read_result核验journal/run/manifest/request/资产再显示，没有模型调用；首次新进程重开同run且仍仅一次run，P014标签逐像素相同。通过。 |
| 正式完成后显示、旧回复不污染新输入、失败不变0 | session完成并关闭后读取已提交结果；busy拒绝切换、close忽略迟到预览；源变化拒绝；控制器6项覆盖，真实zero=0、missing=null、cancel=null、旧zero run保留。显示旧图明确为已保存核数。通过。 |
| 取消/失败/重试/返回，GUI不阻塞 | gui-regression观察真实worker PID后取消，没有正式结果；后台QThread/WorkflowSession及idle等待，336次20ms心跳最大间隔约63ms。损坏/缺失SQLite错误回归可恢复，关闭等待源读取测试，真实正常退出重开通过。性能结论限本机该例，独审未独立再跑完整运行中关闭。通过所需风险范围。 |
| 先一条真实样例，再风险回归；不以开发者代学生/科学 | first-gui-run与gui-regression明确区分真实点击和原生选择器替换；公开已见图训练重叠/患者独立性仍未知，8bit/Windows真实模型为边界，Linux CI不代表模型或科学。通过。 |
| 短导航与最小练习 | docs/runbooks/nuclei-single-image.md包括设置、5步流程、保存位置与重开、失败旧图含义、46核公开练习及非科学验证说明。通过。 |
| 准确提交独审及必需CI/正常PR/main，不削弱门禁 | 独审绑定16d32b1，P2关闭，无其他阻断；详见review-and-validation.md。c08979d本地1735+wheel通过；16d32b1增量8项独立通过。PR67 quality42157212799双平台完整门禁/wheel成功，Windows1737/Linux1733+4既有skip，规则和环境通过；main6bd4680与准确候选tree相同。通过。 |
| 正式回传上游入口/截图/证据/PRmain/限制及下一建议，自动接续 | 2026-11-06合入后已成功发送正式验收，包含入口/两张截图路径/真实GUI及模型证据/CI独审/PRmain/科学与环境边界及下一最小建议，上游工具回执isError=false。通过。 |

没有安装器发布、私有原图上传、外部付费或新数据用途。GitHub代码PR和上游消息属于已有明确授权。所有科学/真实学生/独立目标机缺项保留，不能由以上工程证据关闭。

## 集成与回传收据

最终验收：PR67已合入main 6bd4680530dc4697f8d394a96fd288723222ddb8，与候选16d32b12f3980cf2dcaeb3ec9d145488378c6dcd文件树diff退出0。quality42157212799成功：Windows1737 passed/10 warnings/1410.11s；Linux1733 passed/4既有Windows专用skip/10 warnings/951.94s；两平台随后wheel/check --all完整通过。rules42157213226、desktop-environment通过。只读独审绑定候选通过。2026-11-06已成功向上游01a19bfd-f3ab-7502-86da-9f61953d1c8a(local)发送正式入口/截图/证据/CI/独审/PRmain/边界和下一建议，要求自动接续。观察进程87597已exit0。
