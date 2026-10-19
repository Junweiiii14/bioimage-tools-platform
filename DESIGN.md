---
name: BioImage 工具平台与 WB 证据工作台
description: 可见工具平台与左右工作区、中间图像的原生 Qt 自动化实验工具
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
  source-selected: "#e1f2ee"
typography:
  platform-page:
    fontFamily: "Microsoft YaHei UI"
    fontSize: "26px"
    fontWeight: 600
  platform-brand:
    fontFamily: "Microsoft YaHei UI"
    fontSize: "23px"
    fontWeight: 600
  platform-tool:
    fontFamily: "Microsoft YaHei UI"
    fontSize: "22px"
    fontWeight: 600
  platform-section:
    fontFamily: "Microsoft YaHei UI"
    fontSize: "15px"
    fontWeight: 600
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
  platform-control: "6px"
  platform-tool: "12px"
  control: "5px"
  field: "3px"
spacing:
  field-inset: "4px"
  content-gap: "5px"
  header-inset: "6px"
  parameter-gap: "8px"
  column-gap: "10px"
  export-gap: "16px"
  source-column-gap: "12px"
  source-control-inset: "14px 12px"
  platform-action-inset: "10px 14px"
  platform-content-inset: "30px 34px 28px"
components:
  analysis-review-panel:
    backgroundColor: "{colors.surface}"
    width: "292px"
  platform-button:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.platform-control}"
    padding: "10px 14px"
  platform-tool:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.platform-tool}"
    padding: "24px"
  source-list-selected:
    backgroundColor: "{colors.source-selected}"
    textColor: "{colors.selected-ink}"
    rounded: "{rounded.control}"
    padding: "9px 6px"
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

# Design System: BioImage 工具平台与 WB 证据工作台

## Overview

**Creative North Star: "证据工作台"**

冷白平台入口与白色工作区承载项目、工具和结果，深色画布承载原始图像。青绿用于主要动作和当前选择，系统中文字体保证长时间操作的清晰度。沿用用户选择的 A「证据工作台」，将相同的视觉语言扩展到可见工具平台和原图三栏工作区。

本次增量来源为平台 `f32ebbb` 的 `platform_window.py`、原图工作区与画布 `e2d78e6`，并核对 T-024 协调工作树的最终改动：定量复核栏扩为 292px、摘要格式与状态换行、拼图来源序号。其余定量、OCR、拼图和导出视觉规则沿用 T-023 `0d9aad94`。原图页 1440×900 与 1100×780 的实际 Qt 合成截图已检查；平台最终集成截图和真实资源完整运行由主任务补充，不能从这些设计记录推断科学准确率。

这是 Windows 自定义 Qt Widgets 设计语言。Impeccable 当前没有相应 Platform 枚举，按原生界面手工提取尺寸、QSS 和绘制行为；不把桌面控件伪报成网页组件或移动端组件。

**Key Characteristics:**

- 可见工具平台：工具入口、项目动作和最近项目。
- WB 顶部横向阶段导航，来源与操作在左、图像居中、结果复核在右。
- 自动化为主要操作；精确坐标与批量元数据保留在高级入口。
- 机器建议、人工复核和过期状态有各自含义，颜色不代替状态文字。
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

- `platform-page`、`platform-brand`、`platform-tool`、`platform-section`：平台主标题、品牌、工具名与分区标题。
- `welcome`：WB 欢迎标题；`title`：步骤标题。
- `section`：导出用途组和裁剪候选标题；`brand`：工具栏产品名。
- `evidence-heading`：来源、当前结果与复核标题；`project-name`：可编辑项目名。
- `caption`：当前项目标签；`body`：常规控件和数据。

剖面图绘制文字局部设为 9pt；拼图导入字体及输出像素字号属于作品模板，不是应用 UI 字体。定量页隐藏重复的步骤标题与说明，让页签和三栏标题承担定位。

## Layout

平台初始尺寸 1380 × 880，最小 1000 × 680；左导航宽 216、右项目说明宽 270，中间工具与最近项目弹性扩展。顶部边距为左右 28、上下 20，中间内容左右 34、上 30、下 28。平台当前只有一个 WB 工具面板，后续工具不画成已可用入口。

WB 窗口初始尺寸 1440 × 900。根布局左右边距 12、上下 10，内容间距 5。四阶段以 `QListWidget` 横向、不换行排列，单元格 220 × 44，列表固定高度 48；没有旧侧栏，也没有实现移动端折叠或自动换行断点。

定量页内的证据工作台采用三栏：左侧参数滚动区固定宽 220，右侧复核滚动区固定宽 292，中央证据区弹性扩展，栏间距 10。中央原图与曲线使用不可折叠的纵向 splitter，初始分配 340 / 210；原图画布最小 280 × 190，剖面图最小高度 150。右侧当前摘要表高 130–180，四列为泳道、有效信号、状态、原始积分（待复核）。来源列表高 82，当前泳道字段与完整参数表共享编辑状态。

OCR、归一化与定量为同级页签；证据工作台、全部泳道参数、完整项目结果为定量内部页签。完整结果没有被固定塞入工作台底部。

原图工作区采用左 224 / 中间弹性 / 右 272 的三栏，栏间距 12。左右白色区域内边距左右 12、上下 14；中央画布最小 280 × 240。左侧原图列表显示名称、缩略图与状态，自动处理和结果导出在列表下方；右侧放当前来源、Fig/蛋白/泳道数/排除泳道与确认动作，候选及高级检测按需展开。顶部宽表移到“高级数据表”页签，精确坐标仍默认隐藏。长文件名使用可压缩标题与完整 tooltip。

拼图阶段以水平 splitter 连接设置与预览，设置最小宽 450、预览最小宽 250，初始分配 460 / 400。导出用途组间距 16，按钮最大宽 360。小窗口依靠实际滚动容器与弹性中央区域；已检查原图页 1100×780 无横向截断关键操作，不宣称移动端或任意窗口尺寸适配。

## Elevation & Depth

通过背景明暗、细边框、表格线和分隔柄组织工作区；没有定义自绘投影或装饰动画。操作系统原生菜单等表面可能有平台阴影，不能据此制定全局无阴影禁令。

## Shapes

平台工具面板为 12px 圆角、平台按钮及最近项目项为 6px；WB 按钮与工具按钮使用 5px 圆角；单行输入、整数输入和组合框使用 3px 圆角。双精度输入仅显式规定边框和内边距。导航和页签使用底部指示线，三栏保持平直原生容器，不包装成额外卡片。

## Components

### Buttons

平台按钮使用较宽的 10px/14px 内边距，WB 内部沿用紧凑控件尺寸。原图主要自动处理按钮最小高 38px。普通按钮白底细边框，悬停变浅青背景与主要色边框，焦点边框为主要色 2px。`primaryAction` 是青绿底白字，用于导入、确认、计算、预览等明确动作。禁用样式降低文字/背景对比；主要按钮更具体的对象规则保留其边框，不虚构独立禁用边框 token。

### Inputs / Fields

单行文本、整数输入和组合框使用白底细边框，焦点变为主要色。透明、无边框的顶部项目名在聚焦时恢复白底边框。双精度与多行输入有自己的 QSS 范围，不推广为完整统一错误状态规范。

### Navigation

当前阶段以浅青背景、深青文字和 3px 青绿底线表示；页签底线为 2px。阶段数字表示操作顺序，不表示完成进度。来源列表以浅青选中背景关联当前原图与测量证据；原图列表使用 `source-selected`，定量列表继续使用既有 hover 面。平台左侧显示项目与工具入口，WB 工具栏提供返回平台动作。

### Source Canvas

裁剪框内部拖动移动原图 ROI，边角拖动调整大小；绿色框和白色角点表达可编辑范围，内部泳道随拖动实时显示。鼠标释放后才提交半开原像素坐标，单击未移动不使结果过期。裁剪编辑限制在原图范围内，焦点视图和缩放不改变坐标含义。

滚轮缩放以指针位置为中心，范围 1–12 倍；中键拖动平移，双击恢复缩放，“适应窗口”回到全图。操作提示常驻画布下方。定量页原图仍只读，不能把这次裁剪交互扩展解释为已经实现拖动曲线基线。

### Platform and Result States

平台最近项目列表保留最多 8 个文件夹路径，选中后展示保存位置，空态给出新建项目动作。只有真实可用的工具可以进入工具列表。

自动化结果的视觉状态不能等同于人工确认。schema8 的机器建议保持 `human_reviewed=false`；只有与当前原图、几何、泳道数、排除和分析请求匹配的建议可继续处理。当前原图右栏显示人工已确认、裁剪已就绪但待复核或等待识别，并追加来源备注；过期和失败的完整含义还在定量结果与处理报告中保留。不能将裁剪框存在等同于机器证据当前有效，不用已勾选状态或成功色掩盖未完成复核。

### Tables and Evidence Views

表格白底、冷浅灰表头、浅网格；选中保持深字。右侧摘要同时显示有效信号、状态与待复核原始积分，未检测和排除不填为零。摘要数值用 4 位有效数字以适应窄栏，完整项目结果表和数据导出保留既有精度；这只是显示格式，不改变定量值。状态开启换行、禁止省略号，并根据内容调整行高。原始积分待复核时不等同于有效信号，也不用于归一化。

定量中央原图只读；裁剪编辑仍属于原图阶段。曲线只显示已核验结果，修改参数需重新计算。纵轴为定量极性下的原始灰度单位信号均值，横轴为裁剪内 0 起算行号；实际刻度来自数据范围。L/R 虚线附边界行号，基线连接所用端点值；没有拖曲线或拖基线交互。

拼图版式表的来源列采用“当前项目三位序号 · 蛋白名”，相同蛋白的不同原图仍可区分；同一来源的多个显示段保持同一编号。完整文件名和稳定 row_id 保留在 tooltip，行号只作当前项目内的显示标识。

拼图预览提供适应窗口与 100%，保留完整未缩放渲染；缩放仅影响显示。空态提示下一步真实操作，不伪造成功。

## Do's and Don'ts

### Do:

- **Do** 从实际 Qt palette、QSS 和绘制实现延续角色。
- **Do** 同步当前来源、泳道参数、图像、曲线与核验结果。
- **Do** 将自动识别和图上修正作为默认操作，精确坐标作为高级补充。
- **Do** 保留机器建议、人工复核、过期和失败的独立文字状态。
- **Do** 显示真实坐标单位、边界含义、缺失与排除状态。

### Don't:

- **Don't** 恢复已被替换的石墨侧栏或 lime 导航规则。
- **Don't** 将显示映射、预览缩放或导航选中当作定量与完成证据。
- **Don't** 虚构网页组件、断点、旧版拖基线功能或统一错误样式。
