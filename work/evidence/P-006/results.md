# P006 原生基线：测量完成，多项超线

冻结测量源码 **a9bda31365ac892719d5bdeae4f58f8051504863**，产品基线main839fa52。六例均真实exit0，每段5预热+30正式；四主题交互仅rows-normal，取消仅neutral。源、输入、预算与分母在采样期间未改，没有并行本地测试/构建。首轮f3e50fe失败保留，不算成功样本；第二轮完整结果不替换失败历史。

原始JSON/log/exit/environment按生产字节保存在[frozen-runs](frozen-runs/native-a9bda31-complete/)。[native-results.json](native-results.json)列全部SHA、原路径、统计复算及六fixture核对；[process-closure.json](process-closure.json)记录六host/renderer共12个PID在结束后均不存活，未杀进程。这不是任意进程树缺失证明。报告前由工具正常关闭/排空/deleteLater。

## 环境与边界

Win11 26200、Core Ultra7 255HX 20核/20逻辑、16GB、Python3.12.14、Qt6.12.0、Windows QPA；屏幕1707×1067/DPR1.5/DPI96、viewport1440×940。Performance电源，--disable-gpu，QT_OPENGL/QT_QUICK_BACKEND未设；开始CPU2%/空闲3367856KiB是单点观察。日志仍有GLES/shared-context错误，未确定其根因。

**前台状态UNKNOWN**：未逐样本记录OS前台PID、Qt active-window、document.visibilityState/hasFocus。DOM焦点正确不证明窗口处于前台。以下rAF延迟是本次未记录前台状态条件下的观测，保留超线，不能直接认证活跃用户延迟或断言后台节流/GPU/产品代码是原因。两次rAF仅绘制机会，不是物理显示。用户体验、目标机、真实原图、算法性能和科学适用性均未验。

## 六负载原值

每项p95为nearest-rank第29/30项，p50/max/原始数组/预热均在JSON。旧预算：快照+JSON50ms、刷新200ms、idle1ms、payload16MiB、host+renderer private2GiB。内存是末次两个进程采样点，非全树或全程峰值；normal行式在交互后取值，与其他例的生命周期不同。

| case | 冷/热快照+JSON p95 ms | 刷新 p95 ms | payload B | 末次private B |
| --- | ---: | ---: | ---: | ---: |
| rows-small | 0.304 / 0.145 | **236.7** | 10591 | 1755181056 |
| rows-normal | 1.244 / 1.162 | 73.9 | 135061 | **2343129088** |
| rows-limit | **147.248 / 142.974** | **489.1** | 15190523 | **2269450240** |
| intake-small | 1.929 / 0.571 | **245.3** | 102546 | 1793982464 |
| intake-normal | 14.208 / 3.632 | 153.0 | 866608 | 1901957120 |
| intake-limit | **374.457 / 211.186** | **1184.9** | **27149399** | **2550824960** |

六例idle p95为0.0082–0.0094ms，快照重建/发射均0。两上界冷/热快照均超50ms，四例刷新超200ms，仪器上界载荷超16MiB，三例内存点超2GiB；不能把exit0写成预算全部通过。

旧T082 R09 e6b78b4同四fixture、预算与环境记录保留，可比较载荷相同及量级；本轮没有产品性能优化，不从一次p95波动宣布改善/退化，也不将旧摘要当当前原始数据。

## 四主题与取消

四主题各30可信原生settings事件，项目/修订/选择保持；焦点进入抽屉和关闭后恢复均30/30。feedback是click至DOM状态+两次rAF；settled再等动画，不能互换预算。

| theme | feedback p95 ms（预算100） | settled p95 ms |
| --- | ---: | ---: |
| forest | **974.7** | 3978.6 |
| ember | **960.1** | 3926.4 |
| iris | **1134.0** | 3911.2 |
| neutral | **944.6** | 3925.3 |

neutral取消30/30均在**preparing**，final_run=null、无PID，不是已启动worker/长算法中断验收。源码在采集前实际检查最终UI状态cancelled，并等ComparisonBridge.idle服务关闭；原始报告保留空RunRecord，不补造进程。DOM反馈p95 **85.2ms**、宿主cancelling确认p95 **28.070ms**、请求至服务关闭p95 **6396.539ms**。前两项本次低于200ms初始预算，最后一项单列，三者不可相加。正式RunRecord持久取消/正在计算的安全点需P005另验。

## 后续小修顺序与复测

1. 先补观测条件：逐样本记录浏览器visibility/focus、Qt active及OS前台归属；前台补测另立批次，保留本批，不删条件不符的样本。未定因前不改节流flag求过线。
2. 上界全量payload/JSON成本有直接数值证据：拆分资产引用/分页投影，保持身份、全部导出、缺失与有效零及草稿。新任务用同六fixture、预算、5+30复测，测真实场景再决定优化。
3. 准备取消的服务关闭单独定位I/O/生命周期耗时；P005在真实worker运行/提交边界另测暂停取消，P009验运行导航/焦点与新编辑器。当前node/pause和无对齐host-ready时间戳预览明确未测。

本卡交付可复现基线与定位入口，不要求一次修完所有性能；不修改现有产品、算法、预算、锁文件、skip/xfail或检查成功标准。
