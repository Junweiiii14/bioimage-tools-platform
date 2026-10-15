---
name: BioImage 工具平台与 WB 证据工作台
description: 暖白平面、青绿操作强调、图像中心的 Windows Qt 自动化工作台
colors:
  primary: "#256f82"
  primary-hover: "#205e6e"
  platform-primary-hover: "#1d5868"
  window: "#f6f5f2"
  surface: "#ffffff"
  ink: "#202523"
  platform-ink: "#242723"
  muted: "#626b65"
  disabled-ink: "#6b726d"
  border: "#d9dcd5"
  platform-border: "#d9dcd6"
  hover-border: "#8badb3"
  hover: "#edf3f3"
  pressed: "#dce9eb"
  selected: "#e3eef0"
  selected-ink: "#174f60"
  tab-selected: "#eaf1f2"
  platform-selected: "#e8f0f1"
  disabled-surface: "#eeefeb"
  header: "#f3f4f0"
  header-ink: "#505953"
  grid: "#eaebe6"
  splitter: "#e5e6e0"
  canvas: "#252729"
typography:
  platform-page:
    fontFamily: "Microsoft YaHei UI"
    fontSize: "28px"
    fontWeight: 600
  platform-brand:
    fontFamily: "Microsoft YaHei UI"
    fontSize: "23px"
    fontWeight: 600
  platform-tool:
    fontFamily: "Microsoft YaHei UI"
    fontSize: "22px"
    fontWeight: 600
  section:
    fontFamily: "Microsoft YaHei UI"
    fontSize: "15px"
    fontWeight: 600
  brand:
    fontFamily: "Microsoft YaHei UI"
    fontSize: "16px"
    fontWeight: 600
  project-name:
    fontFamily: "Microsoft YaHei UI"
    fontSize: "17px"
    fontWeight: 600
  body:
    fontFamily: "Microsoft YaHei UI"
    fontSize: "10pt"
rounded:
  control: "6px"
  field: "4px"
  platform-tool: "8px"
spacing:
  field-inset: "5px"
  control-inset: "6px 10px"
  column-gap: "12px"
  rail-inset: "14px 12px"
  platform-action-inset: "10px 14px"
components:
  button:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "{spacing.control-inset}"
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.surface}"
    rounded: "{rounded.control}"
    padding: "{spacing.control-inset}"
  button-disabled:
    backgroundColor: "{colors.disabled-surface}"
    textColor: "{colors.disabled-ink}"
  field:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.field}"
    padding: "{spacing.field-inset}"
  navigation-selected:
    backgroundColor: "{colors.hover}"
    textColor: "{colors.primary-hover}"
    padding: "9px 24px"
  platform-tool:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.platform-tool}"
    padding: "24px"
---

# Design System: BioImage 工具平台与 WB 证据工作台

## Overview

**Creative North Star: "证据工作台"**

暖白工作区与白色控件面形成克制、平直的原生工作台。青绿强调当前选择与主要动作，深灰画布把注意力交给实验图像。沿用已批准 T-028 的 product-performs 方向：产品操作本身构成界面，专业数据和真实状态优先。

本记录从 T-029 实现提交 `0e2c09c` 的 `workbench_style.py`、`workbench_motion.py`、`platform_window.py` 及 WB UI 提取。局部控件保留自己的原生样式，未将所有画布颜色强制统一为壳层强调色。截图证据位于 `.local/deliveries/WB-workbench-20261016-002056/screenshots`；静态视觉审查的 ship 结论仅限静态界面，不代表动效、科学准确率或干净 Windows 验收。

这是 Windows 自定义 Qt Widgets 设计语言。Impeccable 4.5.2 没有对应 Platform 枚举，保留真实平台；sidecar 记录原生 QSS 与行为，不虚构 HTML/CSS 组件、网页断点或移动端适配。

**Key Characteristics:**

- 暖白、平面、系统中文字体，图像占据中央主要空间。
- 图像复核、拼图、结果三种顶层模式；辅助能力通过项目工具和上下文入口到达。
- 机器建议、人工裁剪审核和质量警告分别表达。
- 动效只帮助导航定位与控件显现，图像和定量数值保持稳定。

## Colors

### Primary

`primary` 是主要动作、键盘焦点、导航指示线和任务进度的青绿。`primary-hover` 用于 WB 主按钮悬停和选中导航文字；平台入口保留自己的 `platform-primary-hover`。表格选中使用 `selected` / `selected-ink`，页签使用 `tab-selected`。

### Neutral

`window` 是暖白底，`surface` 是白色操作面；`ink` 与 `muted` 建立正文和说明层级。平台正文与边框的局部差异分别记录为 `platform-ink` / `platform-border`。`header`、`grid` 和 `splitter` 保持数据结构可见。禁用按钮同时改变背景、文字和边框，不能仅靠降低透明度。

**The Evidence Canvas Rule.** 画布配色和显示变换不进入原始像素或定量结果。

画布的裁剪/泳道线为绿色，候选框为琥珀色；它们属于图上编辑语义，不是壳层成功/失败状态。局部绘制值留在 sidecar，不能从配色推断质量合格。

## Typography

使用 `QFont("Microsoft YaHei UI", 10)` 的原生中文正文；Qt 负责缺失字体替代，代码没有显式 web fallback 栈。正文为点字号，标题为 QSS 像素字号，无固定行高或字距 token。平台页面、品牌、工具名形成三级标题；WB 项目名和分区标题维持紧凑阅读层级。模板字体与输出像素字号属于作品内容，不是应用 UI 字体。

## Layout

平台入口左栏宽 190，内容区边距左右 34、上 30、下 28，工具面板内边距 24。选择原图和拖放入口直接启动项目路径；保存位置以说明和可选调整呈现。

WB 三种模式使用横向单层导航，单元格 132×38、列表高度 42。没有移动端断点。图像复核左栏 224、右栏 272，中央弹性扩展，栏间距 12；侧栏内边距左右 12、上下 14。原图画布最小 280×240。来源列表、图像与当前复核状态同步；泳道曲线、实验信息和高级检测按需展开。

拼图使用不可折叠的三栏 splitter，初始分配 200/720/280，左操作栏最大宽 224，右设置栏最小宽 240。结果区左导航宽 136、右摘要宽 260，中间承载结果表。OCR、归一化、批量信息和高级原图数据保留独立上下文页面及返回入口，不再形成第二层顶层阶段。

截图包含 1440 与 1100 窗口的关键页面；实际像素尺寸受 Qt 缩放影响。滚动区和弹性中央区域承担窄窗适配，静态截图不证明所有 DPI 或任意尺寸均已验收。

## Elevation & Depth

界面以平面色块、细边框和分隔柄组织层次，没有自绘装饰阴影。系统菜单保留原生表面行为。控件展开使用短暂透明度反馈，不移动画布或制造浮层深度。

## Shapes

按钮为轻圆角，输入更紧凑，平台工具面板圆角略大；具体值以上方 token 为准。三栏保持平直容器，不套叠装饰卡片。导航采用细线定位，画布框线和角点表达可编辑范围。

## Components

### Buttons and Fields

普通按钮白底细边框，悬停为浅青面及较深边框，按下进一步加深。键盘焦点按钮使用 2px 青绿边框；输入焦点变青绿边框。主要按钮青绿底白字，禁用后恢复灰色背景和文字。平台按钮内边距更宽，WB 保持紧凑。顶部项目名平时透明无边框，聚焦恢复白底描边。

### Navigation and Motion

选中模式使用浅青背景及青绿文字，底部指示线由 `QPropertyAnimation` 在 180ms 内以 `OutCubic` 移动。新打开的指定控件面板在 140ms 内从 0.7 到 1.0 不透明度显现，同样使用 `OutCubic`；这是控件反馈，不是全页面淡入。切换、隐藏或重新显现先停止旧动画并恢复稳定状态。

**The Stable Evidence Rule.** 图像像素、曲线证据和定量数值不做淡入或数值插值。

应用 `QSettings.reduce_motion` 开启，或 Qt 的 `UI_AnimateCombo` 效果被关闭时，立即完成定位/显现。系统支持按 Qt 暴露的效果状态检测，不声称独立读取全部 Windows 动画偏好。按钮状态由 QSS 即时切换，无另造的过渡时长。

### Image Review

左栏显示缩略图、来源和真实处理状态，中间直接拖动裁剪框及角点，右栏显示图像规格、质量说明、逐泳道摘要和确认动作。确认裁剪不会消除质量警告。曲线开关在同一图像复核模式显示曲线；边界与基线编辑后须重新测量，旧结果不能保持为当前有效结果。

裁剪提交保持原像素半开坐标；缩放、平移和适应窗口仅影响显示。精确坐标和批量表是补充入口。自动结果不能自动标记人工审核，未检测、排除、失败和真实零值须可区分。

### Tables, Context Tools and Outputs

表头浅灰、网格轻，选中保持深字。窄摘要使用 4 位有效数字，完整表与导出保留既有精度。原始积分待质量复核时单独呈现，不能等同有效信号或进入归一化。

拼图预览保留适应窗口与 100%；标签、分段、字体及模板设置保持可到达。结果页承载导出动作与输出位置，完整项目 ZIP、拼图 TIFF/PNG、定量表、OCR 表和归一化表保留实际能力。空态与失败文案说明下一步，不伪造完成。

## Do's and Don'ts

### Do:

- **Do** 从实际 Qt palette、QSS 和绘制实现提取角色。
- **Do** 保持原图、来源、曲线、参数和当前结果一致。
- **Do** 用明确文字区分裁剪审核、质量警告、过期和失败。
- **Do** 尊重应用减少动效和 Qt 暴露的系统效果偏好。

### Don't:

- **Don't** 恢复四阶段顶层导航或让高级表格成为默认操作。
- **Don't** 把图像、曲线证据或定量数值加入装饰动画。
- **Don't** 把截图、自动结果或裁剪确认当作科学验收证明。
- **Don't** 虚构网页组件、移动端断点或全平台偏好检测。
