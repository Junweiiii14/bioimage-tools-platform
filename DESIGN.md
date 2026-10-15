---
name: WB 证据工作台
description: 原图、泳道曲线与核验结果同屏的原生 Qt 实验工作台
colors:
  primary: "#087677"
  selected-ink: "#096568"
  window: "#f3f6f7"
  surface: "#ffffff"
  alternate-base: "#f0f5f5"
  palette-button: "#fafcfc"
  ink: "#24363b"
  secondary-ink: "#405660"
  summary-ink: "#526970"
  header-ink: "#344c59"
  caption-ink: "#536771"
  disabled-ink: "#697a84"
  border: "#cbd8dd"
  divider: "#c8d4dc"
  splitter: "#d3dde2"
  grid: "#dce4e9"
  hover: "#eaf5f3"
  step-selected: "#eff7f6"
  table-selected: "#dff1ed"
  inactive-tab: "#edf2f5"
  disabled-surface: "#edf1f3"
  welcome-panel: "#e8eef1"
typography:
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
  brand:
    fontFamily: "Microsoft YaHei UI"
    fontSize: "16px"
    fontWeight: 600
  evidence-heading:
    fontFamily: "Microsoft YaHei UI"
    fontSize: "14px"
    fontWeight: 600
  project-name:
    fontFamily: "Microsoft YaHei UI"
    fontSize: "14px"
    fontWeight: 600
  caption:
    fontFamily: "Microsoft YaHei UI"
    fontSize: "11px"
  body:
    fontFamily: "Microsoft YaHei UI"
    fontSize: "10pt"
rounded:
  control: "5px"
  field: "3px"
spacing:
  field-inset: "4px"
  content-gap: "5px"
  header-inset: "6px"
  parameter-gap: "8px"
  column-gap: "10px"
  export-gap: "16px"
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
    textColor: "{colors.summary-ink}"
    padding: "10px 20px"
  navigation-selected:
    backgroundColor: "{colors.step-selected}"
    textColor: "{colors.selected-ink}"
  tab:
    backgroundColor: "{colors.inactive-tab}"
    textColor: "{colors.secondary-ink}"
    padding: "7px 12px"
  tab-selected:
    backgroundColor: "{colors.hover}"
    textColor: "{colors.selected-ink}"
  source-selected:
    backgroundColor: "{colors.hover}"
    textColor: "{colors.selected-ink}"
    padding: "5px 7px"
---

# Design System: WB 证据工作台

## Overview

**Creative North Star: "证据工作台"**

白色横向导航与冷白工作区让图像、曲线和结果成为视觉主体。浅色参数区、深色图像画布和克制的青绿操作强调提供熟悉的实验软件布局；系统中文字体保持原生清晰度。

本记录以用户选择的候选 A 最终 Qt 实现为准，替换 T-022 石墨侧栏与 lime 规则。代码基线为 `0d9aad94c8bd7a93f34a24163af4fabe8d017d56`：`apps/desktop/src/bioimage_app/figure_window.py::_apply_theme` 提供壳 token，`tools/wb/src/wb_tool/ui/figure_view.py`、`project_analysis.py`、`view.py` 和 `canvas.py` 提供布局与绘制规则。核对了交付目录中的 `analysis-1440.png` 实际 Qt 截图；截图不证明科学准确率或物理 DPI 验收。

**Key Characteristics:**

- 白色顶部横向阶段导航。
- 来源参数、中央证据、结果复核三栏同屏。
- 原生控件、紧凑中文层级与青绿选择状态。
- 图像显示与定量数据分离。

## Colors

主要操作与信号曲线使用青绿，浅色选中面保持文字可读，深色仅属于图像证据画布。

### Primary

- `primary` 用于主要按钮、控件焦点、导航及页签底部指示线，也与剖面信号线同值。
- `selected-ink` 用于选中步骤、页签、来源和表格文字。步骤底使用 `step-selected`；来源与页签选中底使用 `hover`；表格选中底使用 `table-selected`。

### Neutral

- `window` 承载窗口与中央证据区，`surface` 承载工具栏、横导航、参数区、复核区、编辑器与表格。
- `alternate-base` 用于表头和悬停列表项，也是 Qt AlternateBase；`palette-button` 是 palette 默认按钮角色，实际按钮 QSS 使用 `surface`。
- `ink`、`secondary-ink`、`summary-ink`、`header-ink`、`caption-ink` 分别用于正文、步骤辅助说明、摘要/导航、表头、项目标签。
- `border`、`divider`、`splitter`、`grid` 区分控件边框、页签分隔、分隔柄和表格线；禁用按钮采用 `disabled-surface` / `disabled-ink`。

**The Evidence Canvas Rule.** 画布的固定绘制色只编码证据视图，不改变原始像素、定量结果或输出数据。

图像画布由 `canvas.py` 绘制深底、区域框和泳道框，不从窗口背景反推配色。剖面图由 `view.py` 绘制白底和青绿信号线；灰蓝基线、虚线边界及坐标文字的局部绘制参数记录在 sidecar。它们不是通用错误、成功或壳状态色。

## Typography

基础字体为 `QFont("Microsoft YaHei UI", 10)`，由 Qt 继承；缺失字体时由系统替代，代码没有显式 fallback 栈。标题使用 QSS 像素字号，正文保持点字号；没有固定行高、字距或展示字体规范。

- `welcome`：欢迎标题；`title`：步骤标题。
- `section`：导出用途组和裁剪候选标题；`brand`：工具栏产品名。
- `evidence-heading`：来源、当前结果与复核标题；`project-name`：可编辑项目名。
- `caption`：当前项目标签；`body`：常规控件和数据。

剖面图绘制文字局部设为 9pt；拼图导入字体及输出像素字号属于作品模板，不是应用 UI 字体。定量页隐藏重复的步骤标题与说明，让页签和三栏标题承担定位。

## Layout

窗口初始尺寸 1440 × 900。根布局左右边距 12、上下 10，内容间距 5。四阶段以 `QListWidget` 横向、不换行排列，单元格 220 × 44，列表固定高度 48；没有旧侧栏，也没有实现移动端折叠或自动换行断点。

定量页内的证据工作台采用三栏：左侧参数滚动区固定宽 220，右侧复核滚动区固定宽 250，中央证据区弹性扩展，栏间距 10。中央原图与曲线使用不可折叠的纵向 splitter，初始分配 340 / 210；原图画布最小 280 × 190，剖面图最小高度 150。右侧当前摘要表高 130–180。来源列表高 82，当前泳道字段与完整参数表共享编辑状态。

OCR、归一化与定量为同级页签；证据工作台、全部泳道参数、完整项目结果为定量内部页签。完整结果没有被固定塞入工作台底部。

原图阶段保留顶部来源表和下方左右工作区：浅色可滚裁剪参数宽 254，右侧深色画布扩展。精确坐标和高级检测参数按需展开。拼图阶段以水平 splitter 连接设置与预览，设置最小宽 450、预览最小宽 250，初始分配 460 / 400。导出用途组间距 16，按钮最大宽 360。小窗口依靠实际滚动容器与弹性中央区域，不宣称未实现的通用响应式规则。

## Elevation & Depth

通过背景明暗、细边框、表格线和分隔柄组织工作区；没有定义自绘投影或装饰动画。操作系统原生菜单等表面可能有平台阴影，不能据此制定全局无阴影禁令。

## Shapes

按钮与工具按钮使用 5px 圆角；单行输入、整数输入和组合框使用 3px 圆角。双精度输入仅显式规定边框和内边距。导航和页签使用底部指示线，三栏保持平直原生容器，不包装成额外卡片。

## Components

### Buttons

普通按钮白底细边框，悬停变浅青背景与主要色边框，焦点边框为主要色 2px。`primaryAction` 是青绿底白字，用于导入、确认、计算、预览等明确动作。禁用样式降低文字/背景对比；主要按钮更具体的对象规则保留其边框，不虚构独立禁用边框 token。

### Inputs / Fields

单行文本、整数输入和组合框使用白底细边框，焦点变为主要色。透明、无边框的顶部项目名在聚焦时恢复白底边框。双精度与多行输入有自己的 QSS 范围，不推广为完整统一错误状态规范。

### Navigation

当前阶段以浅青背景、深青文字和 3px 青绿底线表示；页签底线为 2px。阶段数字表示操作顺序，不表示完成进度。来源列表以浅青选中背景关联当前原图与测量证据。

### Tables and Evidence Views

表格白底、冷浅灰表头、浅网格；选中保持深字。右侧摘要同时显示信号与状态，未检测和排除不填为零。

定量中央原图只读；裁剪编辑仍属于原图阶段。曲线只显示已核验结果，修改参数需重新计算。纵轴为定量极性下的原始灰度单位信号均值，横轴为裁剪内 0 起算行号；实际刻度来自数据范围。L/R 虚线附边界行号，基线连接所用端点值；没有拖曲线或拖基线交互。

拼图预览提供适应窗口与 100%，保留完整未缩放渲染；缩放仅影响显示。空态提示下一步真实操作，不伪造成功。

## Do's and Don'ts

### Do:

- **Do** 从实际 Qt palette、QSS 和绘制实现延续角色。
- **Do** 同步当前来源、泳道参数、图像、曲线与核验结果。
- **Do** 显示真实坐标单位、边界含义、缺失与排除状态。

### Don't:

- **Don't** 恢复已被替换的石墨侧栏或 lime 导航规则。
- **Don't** 将显示映射、预览缩放或导航选中当作定量与完成证据。
- **Don't** 虚构网页组件、断点、旧版拖基线功能或统一错误样式。
