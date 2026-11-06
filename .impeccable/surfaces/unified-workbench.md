---
version: 1
slug: "unified-workbench"
primary_target: "apps/desktop/src/bioimage_app/web_ui/index.html"
related_targets: ["apps/desktop/src/bioimage_app/web_ui/research_tools.css", "apps/desktop/src/bioimage_app/web_ui/bca.js"]
---

# P020 统一工作台

Mode: Operate；沿用既有 Windows QtWebEngine 界面，code-led 扩展，用户已明确不重做品牌。

## Direction contract

THESIS：从同一工作台找到三个真实工具，研究状态、环境准备与已保存结果可辨认。

OWN-WORLD：继承 DESIGN.md 与 design_tokens.css 四主题、Noto Sans SC、现有按钮/焦点/密度；不引入组件库或全局 token。

STORY：选择工具→准备输入→运行→核验保存→结果/导出/重开；返回只浏览，不关闭已有项目。普通用户不必理解工作流节点。

FIRST VIEWPORT：三个同骨架工具卡，标题/用途/准备状态/入口顺序一致；最近 WB 项目沿用现有侧栏，编排入口接现有画布。BCA 表单/表格与核分割原图/轮廓保持专业差异。

FORM：既有操作工作台增量，不启动品牌选型。seed: none (incumbent user-pinned)。

FINISH：按用户指定有界视觉检查及上游固定独审窗口收尾；不另派重复审查。设计文档核对由作者完成，独审状态以 P020 任务为准。DESIGN.md 与 sidecar 未改，未生成装饰性位图。
