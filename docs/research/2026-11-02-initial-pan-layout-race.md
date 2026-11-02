# 首次平移与延迟布局回调的最小实验

## 问题与判据

P007准确候选23d4056的Windows完整CI在旧手动泳道测试等待imagePan=40/25时超5000ms，其余1599项通过。该候选未改这两份UI源码；原样单独执行通过不能关闭失败。问题限定为真实指针事件与首次fitImage初始化的顺序；原位移、ROI/原像素/历史与数值预期全部保留，不增加超时或skip。

## 来源与环境

Win11、Qt6.12.0/Python3.12.14、offscreen/disable-gpu，与CI类型条件一致但不是CI当时现场。源代码app.js的renderCanvas把fitImage放到requestAnimationFrame；fitImage改变panKey时会重置显示位移。manual_lanes.js在pointerdown捕获旧offset，pointermove后调用fitImage。

核对[Qt6.12官方QTest源](https://raw.githubusercontent.com/qt/qtbase/v6.12.0/src/testlib/qtestmouse.h)及[官方API](https://doc.qt.io/qt-6/qtest.html)：按键已按下时有移动事件分派路径，不能仅因OS光标位于目标位置就断言事件缺失。来源访问2026-11-02；以本机实际trusted事件作为实验依据，不用文档替代WindowsCI现场。

## 有界实验

1. 原样完整用例实际1passed/25.34秒，只是单次观测。
2. 只运行首个平移段的临时探针，把OS光标预置到终点，仍收到trusted pointerdown与40/25移动且通过；不支持光标位置抑制这一候选原因。
3. 同段扣留初始rAF回调：实际trusted pointerdown=(694,416)、move=(734,441)，buttons=1，naturalWidth=100、4个回调待执行，最终imagePan=(0,0)。移入fitImage时才安装新panKey，抹掉刚产生的平移。
4. 正式原用例增加pending_layout分支，原断言/5000ms/后续全部数值不变；产品修复前该分支在同一40/25判据失败，exit1/8.38秒。
5. 产品共享syncImagePanView，在pointerdown抓取offset前初始化当前视图，fitImage沿用同一规则。普通/延迟两个完整用例均通过，2passed/17.20秒；邻近身份/独立灰度WebEngine7passed/12.76秒。新分支在位移断言后恢复全部排队帧，继续原取消、ROI、1000/800、历史保存重开和原图字节不变断言。

## 决定与限制

修复显示状态初始化时机，保留原视图切换的重置语义；不更改坐标算法、ROI或科学数组。没有增加等待或删除不良样本；新增延迟布局分支使原覆盖更严格。网页质量/类型和机械检测通过；无CSS/布局/主题变化，不触碰既有设计侧车漂移或技能升级。

这证明受控pending-layout路径的因果关系，不证明历史CI当时必然发生同一时序；旧GPU/mailbox/native UNKNOWN和目标设备限制保留。原CI完整日志与本机探针/前后回归原件路径及SHA见P007/ci-failure-r1.json、pan-race-regression.json。后继新准确提交须独审与双平台必需CI，旧Accepted不覆盖该UI增量。
