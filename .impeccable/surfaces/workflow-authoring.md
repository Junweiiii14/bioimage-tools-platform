---
version: 1
slug: "workflow-authoring"
primary_target: "apps/desktop/src/bioimage_app/web_ui/workflow_authoring.js"
related_targets: ["apps/desktop/src/bioimage_app/web_ui/workflow_graph.js", "apps/desktop/src/bioimage_app/web_ui/workflow_graph.css"]
---

# P009 工作流编排

Mode: Operate · existing Windows QtWebEngine workbench extension · code-led.

沿已授权T075四主题、本地Noto Sans SC和40px控件。模块目录、步骤画布及参数/连接检查分区；主操作为保存/运行，运行状态与草稿分开。选择节点及文本焦点不随后台回执重建。画布只承载真实保存图的几何，键盘和端口按钮均可编辑，不用动画代替运行。

先用有限节点实测原生DOM/SVG连线、键盘和布局，不新增画布依赖；探针不是M2交付。最终完整WebEngine流程、1440×940/960×640/适用窄窗四主题有界检查、独立视觉审查和代码审查另记录。当前未验收。
