---
name: BioImage WB · T075
description: 墨绿酸橙、明亮科学画布与稳定操作位置的 Windows 实验工作台。
colors:
  ink: '#203b2e'
  muted: '#52634c'
  subtle: '#52634c'
  accent: '#24745a'
  accent-hover: '#185e47'
  accent-light: '#e6efcf'
  paper: '#fefff9'
  ground: '#f1f3e9'
  line: '#dce3d4'
  rail: '#103c32'
  shell-ink: '#eff3dc'
  shell-muted: '#b4c9bc'
  primary: '#d7ed82'
  primary-ink: '#183d2c'
  field: '#f7f9f0'
  soft-header: '#e9efde'
  warning: '#875719'
  warning-bg: '#fbf1dd'
  danger: '#a6372d'
  danger-bg: '#fff0eb'
  canvas: '#e8e9e7'
  ember-ink: '#3d2d25'
  ember-muted: '#765d50'
  ember-subtle: '#765d50'
  ember-accent: '#a94227'
  ember-accent-hover: '#90351e'
  ember-accent-light: '#f6ded0'
  ember-paper: '#fffaf4'
  ember-ground: '#f4eee6'
  ember-line: '#e6d9ca'
  ember-rail: '#302d2a'
  ember-shell-ink: '#f8ece0'
  ember-shell-muted: '#cbb6a5'
  ember-primary: '#ff926b'
  ember-primary-ink: '#3b2119'
  ember-field: '#fcf4eb'
  ember-soft-header: '#eee1d3'
  iris-ink: '#293455'
  iris-muted: '#5d6684'
  iris-subtle: '#5d6684'
  iris-accent: '#435cbe'
  iris-accent-hover: '#32489f'
  iris-accent-light: '#e2e8ff'
  iris-paper: '#fcfdff'
  iris-ground: '#eff1f8'
  iris-line: '#dce0f0'
  iris-rail: '#202c56'
  iris-shell-ink: '#f0f2ff'
  iris-shell-muted: '#c0c8e8'
  iris-primary: '#b7cbff'
  iris-primary-ink: '#202f59'
  iris-field: '#f4f6fe'
  iris-soft-header: '#e8ecf8'
  neutral-ink: '#303332'
  neutral-muted: '#616663'
  neutral-subtle: '#616663'
  neutral-accent: '#424845'
  neutral-accent-hover: '#262b28'
  neutral-accent-light: '#e8ebe8'
  neutral-paper: '#fff'
  neutral-ground: '#f3f4f3'
  neutral-line: '#dce0dd'
  neutral-rail: '#e9ece9'
  neutral-shell-ink: '#303632'
  neutral-shell-muted: '#57625b'
  neutral-primary: '#343c36'
  neutral-primary-ink: '#fff'
  neutral-field: '#f7f8f7'
  neutral-soft-header: '#edf0ed'
typography:
  home-title:
    fontFamily: '"WB Sans", sans-serif'
    fontSize: 36px
    fontWeight: 550
    lineHeight: 1.5
    letterSpacing: -.025em
  home-title-small:
    fontFamily: '"WB Sans", sans-serif'
    fontSize: 28px
    fontWeight: 550
    lineHeight: 1.5
    letterSpacing: -.025em
  canvas-title:
    fontFamily: '"WB Sans", sans-serif'
    fontSize: 20px
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: normal
  drawer-title:
    fontFamily: '"WB Sans", sans-serif'
    fontSize: 22px
    fontWeight: 550
    lineHeight: 1.5
    letterSpacing: normal
  section-title:
    fontFamily: '"WB Sans", sans-serif'
    fontSize: 16px
    fontWeight: 550
    lineHeight: 1.5
    letterSpacing: normal
  body:
    fontFamily: '"WB Sans", sans-serif'
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: normal
  button:
    fontFamily: '"WB Sans", sans-serif'
    fontSize: 14px
    fontWeight: 550
    lineHeight: 1.5
    letterSpacing: normal
  field:
    fontFamily: '"WB Sans", sans-serif'
    fontSize: 13px
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: normal
  auxiliary:
    fontFamily: '"WB Sans", sans-serif'
    fontSize: 12px
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: normal
rounded:
  field-advanced: 6px
  control: 8px
  detail: 10px
  panel: 12px
  home-card: 16px
  paper: 3px
spacing:
  page: 32px
  group: 24px
  inner: 16px
  related: 8px
  control: 40px
  row: 16px
  compact-page: 24px
  compact-group: 16px
  compact-inner: 12px
  compact-related: 6px
  compact-control: 32px
  compact-row: 10px
components:
  button-primary:
    backgroundColor: '{colors.primary}'
    textColor: '{colors.primary-ink}'
    typography: '{typography.button}'
    rounded: '{rounded.control}'
    padding: 4px 16px
    height: '{spacing.control}'
  button-subtle:
    backgroundColor: '{colors.paper}'
    textColor: '{colors.ink}'
    typography: '{typography.button}'
    rounded: '{rounded.control}'
    padding: 4px 16px
    height: '{spacing.control}'
  button-text:
    textColor: '{colors.accent}'
    typography: '{typography.field}'
    padding: 6px 0
  field:
    backgroundColor: '{colors.field}'
    textColor: '{colors.ink}'
    typography: '{typography.body}'
    rounded: '{rounded.control}'
    padding: 8px 10px
  field-advanced:
    backgroundColor: '{colors.field}'
    textColor: '{colors.ink}'
    typography: '{typography.field}'
    rounded: '{rounded.field-advanced}'
    padding: 8px 10px
  mode-tab:
    textColor: '{colors.muted}'
    typography: '{typography.body}'
    height: 62px
    padding: 0 6px
  token-chip:
    textColor: '{colors.ink}'
    typography: '{typography.field}'
    rounded: '{rounded.field-advanced}'
    padding: 6px 10px
  preview-panel:
    backgroundColor: '{colors.soft-header}'
    rounded: '{rounded.panel}'
    padding: 24px
  quick-preview:
    backgroundColor: '{colors.paper}'
    textColor: '{colors.ink}'
    typography: '{typography.auxiliary}'
    rounded: '{rounded.detail}'
    padding: 14px 16px
---

# BioImage WB 设计系统

## Overview

**Creative North Star: "舒展的实验工作台"**

以稳定的操作位置和明亮的科学画布组织复杂实验流程。墨绿外壳负责项目身份，酸橙标出当前主要动作；留白让来源、Fig、蛋白和泳道的关系更容易辨认。界面可以有温度与动感，原图、坐标、曲线和数值必须保持严谨。

这是一份从 T075 当前工作树提取的实现规范，基于最新 T074 `0376f23`，不是完成验收声明。正式入口为 `WebWorkbenchWindow`；HTML 预览与桌面加载同一套 `apps/desktop/src/bioimage_app/web_ui` 资源，通过不同数据适配器运行。不能另写安装版样式来掩盖差异。

**Key Characteristics:**

- 默认 forest / comfortable / expressive；四主题共用结构与业务语义。
- 主操作稳定可见，低频细节原位展开，辅助信息在悬停、聚焦和点击时同样可达。
- 准备页上方 Fig 配置、下方同组三图；定量保留整 Fig 的蛋白 × 泳道矩阵。
- 连续反馈可以中断，提交不等待动画；科学证据不做装饰运动。

当前来源为 `design_tokens.css`、`components.css`、`advanced.css`、`motion.js`、`appearance.js` 与 `interactions.js`，同时核对基础样式的继承。规范描述已落地的公共体系；旧页面残留规则、实际尺寸和完整动态效果仍须在集中验收中核实。任务状态只见 `work/tasks/T-075-ui-system.md`。

## Colors

前置 token 是实际 CSS 值：不带主题前缀的键属于默认 forest；`ember-`、`iris-`、`neutral-` 为各主题覆盖。`warning`、`warning-bg`、`danger`、`danger-bg` 和 `canvas` 由四主题共享。`primary` 用于主要按钮，`accent` 用于选中、焦点和定位，二者不可混为一个颜色。

| 配置 | 外壳 `rail` | 主操作 `primary` | 工作面 `paper` | 内容底 `ground` |
|---|---|---|---|---|
| forest · 墨绿 × 酸橙 | `#103c32` | `#d7ed82` | `#fefff9` | `#f1f3e9` |
| ember · 炭黑 × 朱砂 | `#302d2a` | `#ff926b` | `#fffaf4` | `#f4eee6` |
| iris · 深靛 × 冰蓝 | `#202c56` | `#b7cbff` | `#fcfdff` | `#eff1f8` |
| neutral · 白灰 | `#e9ece9` | `#343c36` | `#fff` | `#f3f4f3` |

`ink` 是正文，`muted` / `subtle` 是辅助文字，`shell-ink` / `shell-muted` 是顶栏文字。`field` 承接可编辑区，`soft-header` 承接表头与分组，`line` 仅表达必要边界。主按钮悬停为 `color-mix(in srgb, var(--primary), var(--primary-ink) 8%)`，不是额外硬编码色板。

**The Scientific Neutrality Rule.** 界面主题只改变工作台外观。原图、画布中的科学内容、源坐标、计算值和导出图像不继承主题；警告、错误、缺项和未保存状态同时保留文字或图标。

`.impeccable/design.json` 的八阶色带只用于规范面板展示，由实际颜色转换为 OKLCH 后生成；它们没有被应用代码采用，不是新的产品 token。

## Typography

本地文件 `web_ui/fonts/NotoSansSC-VF.ttf` 以 CSS 家族 `WB Sans` 加载，覆盖 100–900 字重，`font-display:block`、`font-synthesis:none`。许可为 OFL-1.1；源仓库 `notofonts/noto-cjk` 固定提交 `f8d157532fbfaeda587e826d4cd5b21a49186f7c`，资源 SHA256 为 `d68bafcb48a2707749396aa12bbbd833cb70401f3a9a689fd2902c7e0d295964`。来源与许可随字体保存在 `web_ui/fonts`。

正文 14px / 1.5；按钮 14px、550 字重；高级表单与表格 13px；辅助文字 12px。首页标题 36px、550 字重、字距 -.025em，小于等于 800px 时 28px。画布标题 20px / 1.4，抽屉标题 22px。表格数值使用 `tabular-nums`。主题缩略卡中的 8–10px 图形文字是 `aria-hidden` 的装饰缩略内容，不承载操作说明。

**The One Font Rule.** 预览和安装版都加载同一 Noto Sans SC 文件及真实字重，禁止通过系统字体回退、合成粗体或安装版独立缩放解释差异。

实验成图的项目字体与界面字体分别管理；本轮固定 UI 字体不能改变模板或科学导出的既有字体选择。科学数值格式遵循原业务契约，显示舍入不能回写计算记录。

## Layout

1440px 内容区是设计基准。默认页面边距 32px、主要分组 24px、组内 16px、关联内容 8px；紧凑 token 分别为 24 / 16 / 12 / 6px。常规控件 token 为 40px、紧凑为 32px，表格行内垂直留白为 16px / 10px。小窗口断点会进一步调整布局；紧凑模式不得删除内容、改变对象顺序或科学坐标。

顶栏和流程导航各 64px。首页在约 1160px 内容宽度内组织左右区域，默认 48px 栏间距，右侧成图装饰独立于稳定命中区。准备页保留上方 Fig / N / 蛋白配置、下方同组三张原图；裁剪维持来源、画布和工具区；定量优先呈现整个 Fig 的蛋白 × 泳道矩阵，并在矩阵后展开当前格的编辑区。结果按稳定身份局部更新。

标准抽屉宽度 `min(520px, 100vw)`；模板、实验信息、OCR 和归一化采用 `min(1120px, calc(100vw - 32px))`，内容双栏比 1.2 : 1、间距 32px。标题与底部主操作保持独立，内容区滚动；高级表格表头吸顶并局部滚动，不能让保存按钮随长表消失。

| 已实现条件 | 行为 |
|---|---|
| 宽度 ≤ 1100px | 压缩顶栏次要身份文字、导航间距；首页双栏间距 24px。 |
| 宽度 ≤ 850px | 高级抽屉铺满内容宽度；高级内容改为单栏、间距 24px。 |
| 宽度 ≤ 800px | 首页单栏；页面边距 token 20px、分组 16px；准备页三图通过局部水平滚动保留并排。 |
| 高度 ≤ 720px | 收紧定量图像与标题高度，曲线卡图高由 64px 调为 56px。 |

这些是新增公共层的断点，不表示旧科学工作区的所有局部断点已经移除。小窗口可达性与高缩放必须单独检查，不据此承诺完整移动科学工作流。

**The Stable Position Rule.** 后台进度、保存回执和迟到请求不能抢走当前对象、草稿、输入焦点、滚动或选择。工具区只由用户主动收起，记住其选择。

## Elevation & Depth

常驻面板用留白、底色和必要边界分组。阴影仅用于可悬停的来源图、首页成图、菜单、快速预览和浮层：来源图悬停 `0 6px 18px #14251c14`；快速预览 `0 10px 28px #14251c20`；抽屉 `-12px 0 48px #14251c18`。抽屉遮罩为 `#15251e30`，模糊 2px。

首页成图默认旋转 -2°；悬停回正并抬高 4px。丰富动效的鼠标跟随只作用于内部纸面，通过 requestAnimationFrame 合并指针更新，横移约 ±2px、上移 2–4px、倾斜约 ±2°。文字、容器和点击区域不随其移动。减少动态效果时移除纸面变换。

**The Evidence Stays Still Rule.** 阴影和轻抬只帮助辨认可操作层。ROI、积分边界、曲线采样、原图像素和科学数值不使用弹跳、倾斜或数值滚动。

## Shapes

常规按钮、输入与列表项圆角 8px；主面板、画布与主题卡 12px；来源图、工具入口与快速预览 10px；高级表单及 token 标签 6px；首页继续项目卡 16px。纸面预览保留 3px 小圆角以贴近成图对象。不要把全部区域套成重复卡片。

选中通过边框、底色、勾选或短标签共同表达。公共键盘焦点为 `2px solid var(--accent)`，偏移 3px；科学画布内的句柄继续使用其专有描边反馈，不能改变数据几何来制造聚焦效果。

## Components

公共组件及可直接渲染的缩小示例见 `.impeccable/design.json`。示例继承产品 CSS token，并保留悬停、聚焦、按压状态；它们展示实际公共样式，不执行真实业务或替代整页验收。

| 组件 / 场景 | 使用规则与当前实现 |
|---|---|
| 主要 / 次要按钮 | 同区域一个突出动作；主要按钮用 `primary`，次要用 `paper` 与边框。按压调低亮度，不移动命中区。禁用保留短说明与业务原因。 |
| 输入与表格 | 字段正文 13–14px，辅助 12px；中文组合输入和草稿不被后台快照覆盖。高级表格固定表头；冲突让用户明确选择保留的值。 |
| 流程导航 | 2px 选中线连续移动；切换保留对应来源、Fig、矩阵位置和局部滚动，不能为播放动画延迟命令。 |
| 选择来源 | 原图区域悬停显示轻微阴影；选择同时更新边框、勾选和业务状态。图像本身无 opacity / transform 过渡。 |
| 原位展开 | details 展开从当前高度继续，反向动作取消旧动画；退出更快，旧回调不能关闭新打开的面板。 |
| 快速预览 | 已接入来源与 Fig 信息按钮；指针停留 350ms 显示，键盘聚焦立即显示，点击固定到详情抽屉。不要据此声称所有项目对象都已接入。 |
| 拼图与矩阵 | 排序显示当前拖动对象与落点；矩阵行列悬停帮助定位，选中格与下方编辑区相连。排序的完整让位动画仍以动态验收为准。 |
| 外观设置 | 四张真实 token 缩略卡；选择立即预览，`appearance@1` 回执确认 QSettings 保存，跨发行通道隔离。失败恢复上次有效配置，可重试；不写入科研项目。 |
| 保存 / 高级工具 | 模板、实验信息、OCR、归一化通过宿主命令复用业务用例。长内容与固定底部主操作分离；业务执行、修订校验、取消与真实保存不能被演示状态替代。 |

**The Real Receipt Rule.** 点击立即反馈，但只有收到对应请求的真实保存成功回执才显示完成。失败留在相关操作附近，恢复上次有效状态并提供重试。

动效公共曲线为 `cubic-bezier(.2,.8,.2,1)`。即时反馈 120ms、普通选择及原位展开 220ms、主要进入和导航 320ms、抽屉退出 180ms。轻柔模式 CSS 普通/主要时长为 180ms，Web Animations API 时长上限 180ms；减少动态效果使用 CSS 60 / 80 / 80ms、API 上限 80ms，并关闭进入与抽屉的空间位移。系统 `prefers-reduced-motion` 优先于应用选项。

每个节点只保留一个当前 Web Animation；取消、完成、页面退出清理资源，反向抽屉从当前 computed style 接续。静止界面不运行持续装饰动画；后台活动提示仍应表达真实工作状态。

当前源码确认记录位于 `.local/t075-visual-confirm/report.json`：Qt 6.12 / Chromium 140.0.7339.225，offscreen、`--disable-gpu`、DPR 1；覆盖 1440 × 900 与 960 × 640 的 22 个页面状态，记录的实际字体均为本地 Noto Sans SC（custom font），控制台无记录。该目录还包含通过真实主题按钮生成的四张 `theme-*.png`，以及 `frames.json` 对应的 69 帧交互记录。它们是源码确认材料，不能推导硬件 60fps、物理 DPI 或安装版一致性。

首次 QWidget 抓图存在状态滞后，旧 `.local/t075-visual-valid/theme*` 图片还曾被会话覆盖，这两类材料不能作为四主题验收依据；新的 `t075-visual-confirm/theme*` 不在此排除范围。硬件渲染、高缩放、绑定最终资源的动态对照、源码到 wheel / 安装目录核对和提交绑定独审仍由 T075 执行。动态手感和 M6 尚未验收完成，不得降级定稿效果来通过验收。

## Do's and Don'ts

**Do**

- 以当前 T074 业务结构和 T075 同源资源为准，保留来源、单位、缺项、质量和未保存状态。
- 使用同一 DOM、字体、SVG 与动效代码交付预览和安装版，并冻结数据、视口、DPR 与资源摘要。
- 让主要动作、键盘焦点和当前对象可见；让辅助入口同时支持悬停、聚焦和点击。
- 把保存中、已保存、失败、部分完成和人工审核分开表达。
- 在真实 WebEngine 中核对快速切换、反向展开、中文输入、返回焦点与保存回执。

**Don't**

- 不要用旧预览或旧 Qt Widgets 界面替代最新正式工作台的视觉验收。
- 不要用隐藏来源、单位或错误来降低信息密度，也不要把缺失、失败或未检测显示成零。
- 不要让主题、密度或动效进入科研项目文件、原图或导出内容。
- 不要给科学 ROI、积分边界、曲线和数值添加装饰动画，或让提交等待动画。
- 不要将静态截图、软件渲染测试或资源相同等同于动态体验、硬件渲染或安装版验收通过。
