# T-043 入口与门禁验证

基线b4e85ea；Windows、Python3.12.14、锁定PySide6 6.12.0。产品/依赖锁未升级。

## 未修改生命周期时的调查

- 原顺序完整pytest：628passed/395.93s/exit0（.local/t043/full-baseline.log）。仅为一次通过，不证明旧间歇挂起修复。
- 600次独立窗口关闭/回收：30passed/81.07s/exit0。
- GC阈值50/5/5的600次窗口关闭：30passed/79.85s/exit0。
- 后台关闭与QTimer信号连接交错2000次：exit0。
- 后续100批低阈值/高切换频率压力运行到第58批，被用户报告旧窗口后停止；不能记完成。
- 正式check重复运行到约17%时，同样因测试弹出旧窗口而停止，实际exit1；不是已复现原挂起。
- StackWalk64诊断能采集自有测试进程原生栈，活跃样本为正常Qt事件循环，尚未取得挂起样本；只读诊断未找到确定性线程缺陷。原Qt原生交互式间歇挂起根因仍UNKNOWN。
- 首次诊断脚本错误复用pytest节点造成29个qtbot KeyError，已改为独立节点；这是诊断脚本错误，非产品失败或有效压力结果。

## 反复出现旧界面的已确认原因

1. __main__默认PlatformWindow，其WB注册直接构造旧FigureProjectWindow；--figure-project也直接打开旧窗口。上次仅修正验证脚本，未统一真实入口。
2. WebWorkbenchWindow关闭失败会自动host.show，把后台兼容窗口弹到前台。
3. 本地pytest未默认offscreen，兼容回归测试show()会将旧界面展示到用户桌面；CI原已使用offscreen。

修复：日常命令和常用历史参数统一当前绿色WebWorkbenchWindow；明确--legacy-*兼容参数并标记窗口标题；关闭失败保持当前工作台；固定目录启动器；check子进程强制离屏，直接pytest默认离屏。保留全部兼容测试、worker路由和旧数据，无HTML/CSS变更。

初轮入口10项exit0；入口/网页/平台21项exit0/24.61s。初轮Ruff长行由format修复；初轮Pyright两项测试直接访问protected成员已改为通过正常close路径观察，未加ignore或降低门禁。

最终产品提交2e5021d：只读独审无确定阻断问题，独立新增14项exit0。正式uv run --locked --no-sync python dev.py check --all实际exit0：642passed/361.62s，Ruff/format/Pyright/import及隔离wheel全部完成。日志.local/t043/check-entry-fix.log。未把离屏配置修复称为已证明某个原生锁死根因；原生Windows显示/交互和旧间歇挂起仍独立保留。

桌面新建“BioImage WB 工作台（当前开发）”快捷方式，固定当前检出目录的Start-BioImage.ps1；原有快捷方式/旧结果启动文件未覆盖。入口+网页+平台21项exit0，最终入口/环境/同步异步关闭拒绝14项exit0。


治理合入开发树e0be945后再次正式完整check，实际exit0：657passed/427.30s，全部独立wheel及真实OCR验证完成。日志.local/t043/check-final-integrated.log；只读原生快照显示正常Git子进程管道ReadFile等待，没有复现挂起。8原图/12参考SHA再验相等，34个原有未提交文件SHA相等。


CI001之后最终产品树fa9c5f2正式完整check实际exit0：657passed/451.28s，全部隔离wheel含真实OCR完成。日志.local/t043/check-final-ci001.log；文档后继与此产品内容相同。
远端Linux首次暴露close中的Windows句柄类型分支，2b9f643最小guard修复并独审。旧阶段自身锁定环境8真实进程测试/10.89s退出0；模块Linux/Windows目标0错误。Windows Qt存根不含Unix接口，整个项目在Windows强制Linux目标的8个Qt存根错误不是有效Linux CI证据，前置尝试exit1且当时未执行完整check；真实Linux检查以GitHub runner为准。
从原ResearchVault历史目录运行活动Start-BioImage.ps1 --help退出0，得到当前工作台及显式legacy参数。8原图/12参考与旧first-automatic.json SHA保持，34原有未提交文件保持。


CI004产品68c3265正式完整check --all实际exit0：659passed/509.86秒，静态/架构/政策检查和全部隔离wheel、真实OCR/worker均通过；日志.local/t043/check-ci004-final.log，退出码记录.local/t043/ci004-final-gate.json。没有修改时限、预期、skip或依赖；通过不证明偶发超时根因。


CI006产品a811ccfd正式完整check --all实际exit0：668passed/508.54秒；Ruff/format/Pyright/import/policy及全部隔离wheel、真实桌面异步关闭/OCR/worker均完成。日志.local/t043/check-ci006-final.log，退出回执.local/t043/ci006-final-gate.json。保留原测试/时限/依赖，之前79f9070失败不抹去。


CI009产品57fd7ea正式check --all实际exit0：669passed/497.77秒，Observed child exit0/u32=0；Ruff/format/Pyright/import/policy及全部隔离wheel、真实桌面异步关闭/OCR/worker均完成。日志.local/t043/check-ci009-final.log，回执.local/t043/ci009-final-gate.json。原5秒等待/15分钟/全部断言/依赖不变。此前Windows与旧退出失败仍保留。
