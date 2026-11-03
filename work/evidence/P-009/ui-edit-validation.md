# P009 完整界面链路与首轮有效视觉采集

本阶段基于f4c8ac1，仍in_progress，未独立审查或合入main。本轮不改科学公式或运行/测试预算。

## 已验证的实际操作

`uv run --locked --no-sync python -m pytest tests/test_workflow_authoring_web.py -q` 最新日志`.local/p009-web-edit-connected-flows.log`，退出0，**5passed39.93秒**。用真实QtWebEngine/WebChannel、同一worker和持久化成果覆盖：

1. 标题/ROI表单保存保持输入DOM及焦点，原始样例实际出4000.0/报告，再绑定第二批实际出40.0。
2. 新增节点、缺输入解释、错误类型端口点击连线/中文解释、正确重连、替换模块、删除、原边保留、打开原目录恢复已保存修订。
3. 布尔false能保存；删除全部泳道形成不完整草稿，随后从目录默认项恢复；模拟composition事件期间保存被阻止，结束后中文标识实际保存。模拟事件不证明物理输入法验收。
4. 移动节点保存实验室模板，GUI从该模板和另一张真实TIFF新建、保留布局、一键实际出40.0；同一新封装模板经独立CLI进程运行完成。
5. GUI连续运行的真实worker数/复用节点分别为(3,0)、移动后(0,3)、改报告样式后(1,2)、改分析极性后(2,1)。运行中编辑的新标题、dirty状态及焦点在结果回执后保留，再实际保存。

相应实现修正：模板新建不传无关的空泳道数；布尔控件不错误设置required；空数组可从目录已有明确参数复制新项；高级JSON可显式应用回表单；输入法开始即标记草稿，结束提交文本；窄窗参数页可切换当前步骤；桥接连接前禁用文件操作。

## 失败和真实限制

首个图编辑测试误读不存在的bridge.workspace_path属性，退出1/2.74秒；改读实际UI路径后同流程3.16秒过。未为测试添加产品属性。

第一次五流程联合运行4passed/1setup error50.41秒，初始化20秒超时，伴随D3D/Skia/mailbox日志。测试等待脚本对象存在并不证明WebChannel已连接，因此增加连接就绪状态/按钮加载态/相应等待条件；新联合运行通过。原失败的确切原因仍UNKNOWN，不由新通过倒推出GPU或启动竞态统一根因。日志`.local/p009-web-edit-flows.log`保留。

Pyright初次因fixture重构后缺少投影类型断言报5个OptionalMemberAccess；仅在用例入口断言真实投影已创建，未增加ignore。最终`.local/p009-ui-edit-final-types.log`退出0，0 errors/warnings；目标Ruff与`.local/p009-ui-edit-final-web-static.log`的web格式/lint/既有checkJs均退出0。

## 视觉采集：有效性先于验收

实际脚本`work/evidence/P-009/ui_surface_probe.py`，首次离屏QWidget抓图返回成功但图像纯色，**不构成视觉通过**。Windows软件合成初轮图片有上一主题/视图帧滞后；只等DOM RAF不足以证明原生compositor readback完成。静态捕获一轮又在RAF等待10秒超时，退出1/18.41秒，GLES/shared-context日志保留，不改测试超时掩盖。

最终进程环境仅对该命令设置QT_QPA_PLATFORM=windows、QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu、P009_CAPTURE_OUTPUT=.local/p009-ui-main-windows-active。原生窗口激活后采集，截图专用样式关闭transition/animation，等待两次RAF及500ms compositor交付；**500ms不进入产品交互性能成绩**。增加非纯色和当前按钮计算背景与实际像素一致校验。`.local/p009-ui-windows-active-capture.log`退出0，1passed15.42秒。没有修改生产GPU配置，也不宣称全部GPU/目标机故障修复。

有效12图：四主题1440×940画布，四主题960×640参数，forest640×720画布/参数/成果，forest1440×940成果。CSS视口/文档无横溢及来源记录于本地captures.json；原图和最终有效副本位于`.local/p009-ui-main-windows-active/`与`.impeccable/review/`。父线程已查看整批contact sheet及代表原图，文件内容与视图/主题一致。尚未独立视觉判定；原失败工件不覆盖。

本轮仅一次`impeccable detect --json`扫描四个新增/修改工作流JS/CSS目标，退出0：0主要项，1个advisory（backdrop字面颜色）；原始`.local/p009-ui-detect.json`交视觉审查，不重复detector，不借此修改全局主题。

## 剩余

集中独立视觉审查/必要修正及最多一次有效确认，P006口径的真实节点/预览/暂停与取消性能观测、完整隔离wheel、准确提交独立代码审查、PR/必需CI和正常合并。中文操作单docs/runbooks/workflow-authoring.md及版本/旧数据兼容说明docs/contracts/workflow-authoring-v1.md已写。科学/目标环境与真实用户体验待办保留；不能标P009或总目标完成。
