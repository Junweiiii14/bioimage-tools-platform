---
name: WB 自动化桌面工具
description: 以原图证据和明确工作阶段组织的 Qt 实验工作台
colors:
  primary: "#126878"
  rail: "#172126"
  rail-ink: "#c9d5db"
  rail-muted: "#acbdc6"
  current-step: "#d2e9bd"
  current-step-ink: "#213322"
  caption-ink: "#536771"
  welcome-panel: "#e8eef1"
  window: "#f4f7f9"
  surface: "#ffffff"
  alternate-base: "#eef3f5"
  palette-button: "#f7fafb"
  ink: "#20323d"
  secondary-ink: "#405660"
  header-ink: "#344c59"
  disabled-ink: "#697a84"
  chrome: "#eaf0f3"
  border: "#b7c6cf"
  divider: "#c8d4dc"
  splitter: "#d3dde2"
  grid: "#dce4e9"
  hover: "#e7f1f4"
  disabled-surface: "#edf1f3"
  inactive-tab: "#edf2f5"
  table-selection: "#d3e9ed"
  table-selection-ink: "#173e49"
typography:
  brand:
    fontFamily: "Microsoft YaHei UI"
    fontSize: "28px"
    fontWeight: 600
  project-name:
    fontFamily: "Microsoft YaHei UI"
    fontSize: "14px"
    fontWeight: 600
  caption:
    fontFamily: "Microsoft YaHei UI"
    fontSize: "11px"
  welcome:
    fontFamily: "Microsoft YaHei UI"
    fontSize: "24px"
    fontWeight: 600
  title:
    fontFamily: "Microsoft YaHei UI"
    fontSize: "19px"
    fontWeight: 600
  section:
    fontFamily: "Microsoft YaHei UI"
    fontSize: "17px"
    fontWeight: 600
  body:
    fontFamily: "Microsoft YaHei UI"
    fontSize: "10pt"
rounded:
  control: "5px"
  rail: "6px"
  navigation: "4px"
  field: "3px"
spacing:
  compact: "4px"
  inset: "6px"
  toolbar-gap: "8px"
  toolbar-inset: "7px"
  section-gap: "16px"
  workspace-gap: "16px"
  content-gap: "5px"
  navigation-gap: "3px"
components:
  button:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "5px 9px"
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.surface}"
    rounded: "{rounded.control}"
    padding: "5px 9px"
  button-hover:
    backgroundColor: "{colors.hover}"
  button-disabled:
    backgroundColor: "{colors.disabled-surface}"
    textColor: "{colors.disabled-ink}"
  field:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.field}"
    padding: "4px"
  navigation-item:
    textColor: "{colors.rail-ink}"
    padding: "12px 7px"
  navigation-selected:
    backgroundColor: "{colors.current-step}"
    textColor: "{colors.current-step-ink}"
    rounded: "{rounded.navigation}"
  tab:
    backgroundColor: "{colors.inactive-tab}"
    textColor: "{colors.secondary-ink}"
    padding: "7px 12px"
  tab-selected:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.surface}"
---

# Design System: WB 自动化桌面工具

## Overview

**Creative North Star: "实验工作台"**

石墨导航、浅 lime 当前步骤、冷白证据区域和青蓝主要操作构成 Windows 原生 Qt 工作台。紧凑项目栏与层级明确的控件为原图、曲线和拼图让出空间；产品自身的真实证据成为视觉主体。

此记录来自 T-022 第二轮 Taste / Impeccable 原生适配后的实际代码：桌面 `figure_window.py` 的 `_apply_theme`，WB 的 `figure_view.py`、`crop_suggestions.py`、`project_analysis.py`、`project_ocr.py`，以及 `canvas.py` 和 `view.py` 的绘制实现。它描述当前实现，不证明科学准确率、物理 DPI 或安装包验收。用户确认仅借鉴旧 WBQuant 的浅色参数区、深色图像舞台和紧凑工具栏布局；当前 Qt 工作流及科学语义保持独立。

**Key Characteristics:**

- 原生控件与统一中文系统字体。
- 石墨导航和浅 lime 当前步骤，配合紧凑项目栏。
- 图像与曲线拥有独立的证据绘制色。

## Colors

青蓝动作色与浅 lime 阶段定位分工；石墨导航衬托冷白证据工作面，表格选中保持较浅的底色以便阅读。

### Primary

- `primary` 用于主要按钮、页签选中、菜单选中及控件焦点边框；选中文字使用 `surface`。
- `hover` 用于普通按钮悬停。主要按钮保留其更具体的对象选择器底色，不额外规定独立悬停色。

### Secondary

- `current-step` / `current-step-ink` 只用于步骤列表当前项，区别于青蓝操作按钮和页签。

### Neutral

- `rail` 是石墨步骤栏背景，`rail-ink` / `rail-muted` 用于导航和辅助文字；品牌使用 `window` 浅色字。`caption-ink` 用于当前项目标签，`welcome-panel` 用于欢迎流程说明面。
- `window` 是窗口背景；`surface` 是编辑区、表格、滚动区与菜单背景。`alternate-base` 和 `palette-button` 是 Qt palette 角色；按钮的 QSS 背景实际采用 `surface`。
- `ink`、`secondary-ink`、`header-ink` 分别承担正文、辅助说明及表头/导航文字。
- `chrome` 用于工具栏、表头；`border`、`divider`、`splitter`、`grid` 保留控件边界、页签边框、分隔柄和表格网格的区别。
- 表格选中使用 `table-selection` / `table-selection-ink`。禁用按钮使用 `disabled-surface` / `disabled-ink`；部分原生控件仍由 Qt 处理禁用状态，不能推导为所有控件共有的完整禁用规范。

**The Evidence Canvas Rule.** 原图与剖面画布固定绘制色只属于证据视图，不进入通用壳主题，也不改变定量像素。

原图画布在 `canvas.py` 固定绘制深色背景、浅色空态文字、暖色区域框与绿色泳道框。`view.py` 的剖面图固定绘制浅色背景、蓝色曲线与红色边界/基线；这些是各自局部的可视化编码，具体值保留在源码，不能当作新的主要操作色。

## Typography

字体由 `QFont("Microsoft YaHei UI", 10)` 继承；Qt 在字体缺失时选择系统替代，代码没有显式 fallback 栈。标题、品牌和项目名称使用 QSS 像素字号与半粗权重；正文保持 Qt 点字号。没有独立展示字体、等宽字体、固定行高或字距规范。

- `brand`：导航栏 WB 标识。
- `project-name`：紧凑顶部项目名输入。
- `caption`：当前项目标签与导航辅助文字。
- `welcome`：项目欢迎标题。
- `title`：当前工作步骤标题。
- `section`：导出用途分组标题与裁剪候选面板标题。
- `body`：表格、按钮、字段、标签和说明。

输出拼图的字体导入和“输出像素”标签字号属于作品模板设置，不属于应用 UI 字体层级。

## Layout

当前窗口初始尺寸为 1440 × 960；项目列表最小宽度 240、最大宽度 340。工作区石墨侧栏固定宽度 168，与内容区相隔 `workspace-gap`；侧栏包含 WB 标识、说明和步骤列表。步骤项目间隔为 `navigation-gap`。根布局边距为左右 12、上下 10，内容布局间距为 `content-gap`。这些是 Qt 布局尺寸，不是 CSS 断点。

主体是四步骤 `QStackedWidget`，步骤内继续用页签组织相关操作。当前步骤用可调整内容的滚动区域承载；小窗口通过滚动保留可访问性，没有实现移动端折叠导航或响应式断点。原图表与下方图像工作区使用纵向 splitter；下方左侧是固定宽度 254 的浅色可滚参数面板，右侧是弹性主宽度的深色原图画布，通过水平布局并排，间距 8、边距 4。排版设置与预览、定量边界表与曲线使用横向 splitter，均不允许子项完全折叠。原图表高度限制为 110–170，精确坐标列默认隐藏；检测参数通过“高级检测设置”按需纵向展开。OCR / 结果表位于定量步骤，和定量曲线、样本对应页签并列；拼图步骤保留排版与预览。定量左右证据区高度限制为 180–240，结果表位于其下方。

候选裁剪面板采用两列动作网格，候选选择和高级设置开关跨两列，面板边距 10、布局间距 8；应用候选使用主要按钮样式。定量和 OCR 动作采用三列网格。导出用途组间距采用 `section-gap`，导出按钮最大宽度 360。其余未显式设置的间距沿用 Qt 布局默认值，不将其虚构为统一倍数网格。

## Elevation & Depth

当前壳主题通过背景层次、细边框、表格网格与 splitter 表达分区；没有定义自绘阴影或装饰动画。系统菜单等原生表面可能受平台样式影响，因此这不构成对操作系统阴影的全局禁令。

## Shapes

按钮与工具按钮使用 `control` 圆角，单行字段、整数输入和组合框使用 `field` 圆角。双精度输入框只显式设置边框和内边距，没有定义统一圆角。侧栏使用 `rail` 圆角，当前步骤使用 `navigation` 圆角。表格和页签容器保持原生几何，不包装成额外卡片。

## Components

### Buttons

普通按钮为浅底细边框，悬停改变背景与边框；键盘焦点使用主要色 2px 边框。主要按钮以对象名 `primaryAction` 标识，使用青蓝底白字。禁用按钮降低文字和背景对比；禁用主要按钮仍保留其对象规则的边框，未另设独立边框 token。

### Inputs / Fields

单行文本、整数输入和组合框使用白底细边框，焦点变为主要色边框。双精度输入是单独 QSS 规则；多行文本只显式规定前景和背景。不存在可复用的统一错误边框或动画规范。

### Navigation

步骤栏是石墨背景内的原生列表，选中项浅 lime 底深色字；页签和菜单仍使用青蓝底白字。步骤数字是操作顺序，不是完成勾选。底部上一步/下一步与直接选步骤并存，切换保留来源上下文。

顶部项目名是透明、无边框的编辑字段，聚焦时恢复白底主要色边框；它保持可编辑性，同时减少常态界面重量。

### Tables and Evidence Views

表头用冷灰底与底部分隔线，表格单元格白底、浅网格，选中用浅青底深字。证据画布独立绘制；OCR 的图像与原始文本以页签切换。空态给出真实下一步操作，不伪造已经计算或审核的状态。拼图预览提供“适应窗口”和“100%”：前者按显示区域缩放，后者保留实际像素尺寸；完整未缩放渲染仍被保留，这个显示选项不改变输出图或定量数据。

## Do's and Don'ts

### Do:

- **Do** 从实际 Qt palette 与 QSS 延续控件角色和状态。
- **Do** 保留当前来源、未保存标注与步骤位置之间的连续性。
- **Do** 将缺失、失败与真实零值分别呈现。

### Don't:

- **Don't** 将画布绘制色或输出拼图字体提升为通用壳主题。
- **Don't** 用导航选中态表示计算完成或科学审核通过。
- **Don't** 宣称尚未实现的断点、动画、网页组件或统一错误状态。
