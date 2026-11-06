---
version: 1
slug: "nuclei-research"
primary_target: "apps/desktop/src/bioimage_app/web_ui/nuclei.js"
related_targets: ["apps/desktop/src/bioimage_app/web_ui/nuclei.css"]
---

# P016 单图核分割

Mode: Operate · existing Windows QtWebEngine workbench extension · code-led.

继承当前四主题、字体、按钮、原生文件选择及工作流对话框身份，不改全站视觉。首页首屏紧凑研究工具入口，进入后选择原图/运行/原图与轮廓/核数/导出/保存路径。首次依赖选择放运行设置，普通分析不要求命令；真实运行仅既有WorkflowSession。视图保护核分割操作焦点，与旧WB项目分开。

数值只显示提交后核数，未知和失败不显示0；轮廓/缩放仅显示，标签原坐标不变。原图浏览采用简单img适应/固定倍率，既有WB canvas含裁图编辑语义，不跨工具导入。已实际运行公开样例，未完成最终小窗口/主题及独审验收。
