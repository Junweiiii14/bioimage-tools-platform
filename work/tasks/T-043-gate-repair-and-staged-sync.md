# T-043：全量门禁挂起修复与分阶段远端同步

- 状态：in_progress。
- 基线：b4e85ea，当前分支codex/t043-gate-and-staged-sync；先在现有活动树调查，保留旧主目录与其他工作树。
- 用户授权：查清并修复全量门禁挂起，完整检查通过后安全同步本地开发成果到GitHub，按阶段整理PR和历史工作树；保留所有未提交改动和旧结果，不一次合并累计128提交。
- 顺序：复现/线程证据→最小修复及回归→提交绑定只读独审→完整check真实exit0→本地可恢复备份/私有内容审计→推送阶段分支及依赖PR→验证未提交内容/旧结果保留并归档可安全归档的历史工作树。
- 不以分跑、跳过用例、改成功状态或放宽测试预期代替全量检查；不强推、不擅自合main、不上传私有图/模型/凭据/安装包。
- 继续沿用已授权的只读独立审查代理；代码由主代理修改。
- 证据目录：work/evidence/T-043；原生诊断/备份位于.local/t043或仓库外专用备份目录，不提交私有内容。

## 验证与进度

产品2e5021d已提交并独审；正式完整check exit0，642测试/361.62s及隔离wheel完成。证据work/evidence/T-043/entry-and-gate-validation.md。原生交互式间歇挂起根因仍UNKNOWN，不将离屏配置与正常入口修复夸大为已证明某个原生锁缺陷。前任务exit1记录保留。

## 用户追加：反复出现旧界面

已查明两个入口问题：默认命令经PlatformWindow的注册表进入旧FigureProjectWindow，历史--figure-project也直接打开旧窗口；工作台关闭失败还自动host.show。另，本地pytest未默认offscreen，会显示遗留兼容测试窗口。修复正常入口统一现有绿色工作台、兼容入口显式标记、关闭失败留在工作台、测试默认离屏；保留兼容测试与worker，不修改网页样式和原图/旧结果。

完整门禁通过后已建立仓库外all-refs.bundle并verify、19个工作树的index/unstaged binary patch与未跟踪文件tar/摘要；私有忽略结果仍在原路径保留，未将其当Git备份。备份位置仅记.local/t043/backup-location.json。下一步创建依赖阶段草稿PR并分类归档。


合并独立治理实现0b786cb后的开发树e0be945完整check也实际退出0：657passed/427.30s，Ruff/format/Pyright/import/policy及全部隔离wheel完成。后续仅文档、规则回执和阶段历史整理，产品代码不变。34个原有未提交文件SHA保持，8原图/12参考SHA再验一致；6干净历史树原位锁定，所有文件保留。八阶段整理独审完成，治理PR7四项CI通过，阶段草稿PR同步中。原生交互式间歇挂起仍UNKNOWN。


## 本轮交付记录

CI001之后最终产品树fa9c5f2正式完整check实际exit0：657passed/451.28s，全部隔离wheel含真实OCR完成。日志.local/t043/check-final-ci001.log；文档后继与此产品内容相同。
治理前置PR7与8阶段PR3、8–14均已创建草稿。CI001处理Linux类型分支，同步前再次完成全门禁与独审；按精确基线链更新后原子推送，非强推，main不变。当前远端CI结论以各PR实时记录及Issue6开发日志为准，不将历史阶段单独产品审查视为完成。原生Windows交互式间歇挂起根因仍UNKNOWN、后续科学/发布验收未完成；因此总体T043/T003不作完成宣告。


## 入口复发与远端超时追踪

已再次核对专用快捷方式固定活动树；当前AGENT_HANDOFF索引也纠正旧目录指针，原dirty历史树未变。CI003确定隐藏host未随owner销毁，最小Qt所有权修复b4bc8ba/独审3项通过；完整check实际exit0，658passed/497.50s及全部wheel/真实OCR。8原图正常宿主路径新目录验证exit0，原图SHA/保存重开相等/参考未读；离屏截图空白不当作视觉通过。

阶段7原SHA Windows重跑已成功，但初次失败保留。阶段8bcf15分钟取消；CI002诊断5de Windows1failed/656passed/426.36s，首次AsyncStorage create10秒超时且finally关闭完成。不能宣告已定位永久锁；CI00468c3265按请求阶段补无载荷DEBUG日志，独审2项通过，最终全门禁另跑。保持原15分钟/10秒/断言/skip/依赖。


CI004产品68c3265正式完整check --all实际exit0：659passed/509.86秒，静态/架构/政策检查和全部隔离wheel、真实OCR/worker均通过；日志.local/t043/check-ci004-final.log，退出码记录.local/t043/ci004-final-gate.json。没有修改时限、预期、skip或依赖；通过不证明偶发超时根因。


## CI005真实Windows栈

ea6178e远端Windows15分钟取消，60秒栈锁定test_web_bridge.py:128 finally关闭期间QTimer.timeout.connect；不是随后显式gc.collect位置，2无Python帧线程不能诊断GC。Linux659/184.75秒及wheel0，本机50次关闭26.81秒0。79f9070新增受控owned-tree native栈观察，独审独立8项0，完整664门禁随后真实挂起并保存三线程证据，停止专属pytest后check实际exit1；CI006继续修复，保留旧失败。另修父工作区旧WB路由，原文件外置备份，仅该项目段变化并经只读核验；原34未提交内容不变。


## CI006对象退出修复

a811ccfd将存储/WB后台/解码器/恢复四处worker排空后移回owner，确认原线程结束、queued析构完成后才终态。真实本地原生栈支持Qt对象锁/GIL反转，其他超时不一概归因。独审独立18项/4.17秒/exit0，作者组合36项0；668完整check随后实际exit0，见文末结果。8原图再次经现有工作台正常host→真实worker→新输出→保存重开，8run成功、N8/8/4/4/8/8/4/4、原图SHA保持、参考未读、最终关闭退出0；不是注入识别结果或视觉验收。日志.local/t043/workbench-ci006.log。


CI006产品a811ccfd正式完整check --all实际exit0：668passed/508.54秒；Ruff/format/Pyright/import/policy及全部隔离wheel、真实桌面异步关闭/OCR/worker均完成。日志.local/t043/check-ci006-final.log，退出回执.local/t043/ci006-final-gate.json。保留原测试/时限/依赖，之前79f9070失败不抹去。


CI007：bbf3cc5远端Linux真实4项Pyright失败位于诊断辅助函数，pytest未跑；1021662仅补平台guard、绑定独审两平台类型0、作者相关8项0，未变产品或门禁。准备精确清单后继，等待bbf Windows结束再正常推送，保留原作业证据。最新远端状态始终看Issue6/PR14，main未变。


CI008：bbf3cc5 Windows最终668passed/508.43秒但外层exit1/wheel未跑，未定位退出根因，不当全量成功。f5b1fe4/f2a61b3补真实子码和pytest后faulthandler保留，绑定独审、11项0。当前新候选合CI007最小guard及CI008诊断，待正常推送重跑真实远端；main不变。


用户追加：完成后用简单专业语言汇报维护设定、后续维护和快速修bug流程。已更新docs/maintenance-plan.md的现状/入口/分阶段保护/定向→完整检查→独审流程；最终报告须如实区分已建机制和未完成科学/发布/稳定性验收。CI00957fd7ea全量669进行中，8原图功能链已exit0且8几何/48槽输出保持。


CI009产品57fd7ea正式check --all实际exit0：669passed/497.77秒，Observed child exit0/u32=0；Ruff/format/Pyright/import/policy及全部隔离wheel、真实桌面异步关闭/OCR/worker均完成。日志.local/t043/check-ci009-final.log，回执.local/t043/ci009-final-gate.json。原5秒等待/15分钟/全部断言/依赖不变。此前Windows与旧退出失败仍保留。
