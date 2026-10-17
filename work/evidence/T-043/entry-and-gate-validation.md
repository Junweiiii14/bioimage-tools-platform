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

尚待最终类型、完整check、独审及同提交确认；没有将离屏配置修复称为已证明某个原生锁死根因。
