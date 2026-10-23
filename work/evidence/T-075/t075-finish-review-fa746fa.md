disposition: fix

输入边界：本轮为用户批准的 code-led 替换，无获批 raster comp 或 QUALITY BAR 卡；以方向契约和 docs/t075-design-research.md 为依据。26 张必需 PNG 均已查看；动态仅抽看 4 帧及动作/动效源码，未逐帧复核，components.html 仅源码抽查。

## persistence

pass — 初始核对分支 codex/t075-ui-system、HEAD fa746fa953eedc4b491091876dfe1d6830373a15，工作树干净；PRODUCT.md、DESIGN.md、.impeccable/design.json 和 T075 方向契约存在并描述当前四主题、本地字体与高级抽屉。FORM 记录用户固定方向，按本轮明确授权不要求随机概念或生成 comp。26 张必需截图内容、视口与命名相符，未见空白或黑块；报告记录 Windows Qt WebEngine / Chromium 140、DPR 1.5、Noto Sans SC 和静态截图 pending=0。此审查不声明安装、CI、科学验收或完整硬件验收完成。审查末尾出现的并行 Python 修改不在本次提交范围。

## fidelity

| 元素 / 承诺 | 判定 | 证据 |
|---|---|---|
| TYPE | match | 本地 Noto Sans SC、标题/正文/辅助层级与实际字体报告一致。 |
| MATERIAL | match | 首页使用已批准的几何成图示意与轻纸张层次，科学图像保持中性；不存在未交付 raster plate 义务。 |
| GROUND / OWN-WORLD | match | forest 墨绿顶栏、酸橙主操作、浅绿工作面，以及 ember/iris/neutral 四张主题图保持同一结构。 |
| STORY | match | 准备页上方 Fig/N/蛋白配置、下方同组三图；裁剪区域、整 Fig 蛋白×泳道矩阵与四类高级网页工具保留。 |
| THESIS：对象与操作可辨认 | contradicted | 1440-layout.png 左侧蛋白链接无分隔连成 p-AKTAKTGAPDH；960-crop/layout.png 的详情文字紧邻下一工具图标。 |
| FIRST VIEWPORT：稳定主操作与统一控件 | contradicted | 960-home/settings.png 的固定预览浮条覆盖内容；1440-crop.png 角度输入仍是尺寸较小的浏览器默认字段。 |
| FORM | match | 首页焦点抬升、页面切换及抽屉反向转换在抽样帧与可取消动效源码中存在；来源预览有 focus/click 对应入口，未见数字滚动或 ROI 装饰运动。 |
| Truth | match | 截图明确标注演示项目/数据，归一化空态没有填零；不由演示完成标签推导真实事务成功。 |

## ceiling

未达：参考产品所强调的对象分组、稳定操作间距与统一字段完成度，在拼图导航、窄窗工具条和裁图角度输入处尚未贯通。无需增加装饰、资产或扩大动效。检测器的三项无 src 图片在运行截图中均已填充；未复跑检测器，旧静态 radius/font/marquee 告警不直接替代实际画面判断。

## material_fixes

1. THESIS / 对象身份：修复 1440-layout.png 左侧 p-AKTAKTGAPDH 与 p-ERKERKGAPDH 连写；intake_grid.js:15 输出相邻 .text-button.full，但只有 .button.full 获得满宽规则。让每个蛋白成为独立且有间距的定位行，保留 Fig 层级与独立命中区。
2. FIRST VIEWPORT / 预览一致性：960-home.png 底部浮条盖住“打开已有项目”按钮的左上部分，960-settings.png 覆盖信息密度区域；components.css:93 的 fixed/z-index:100 没有占位。将演示标识和切换控制放入保留空间或可收起的预览区域，抽屉打开时不能悬在其表单/操作之上。
3. THESIS / 操作辨认：960-crop.png 与 960-layout.png 顶部“裁图详情”末字几乎贴上后一枚 sliders 图标；1440 下收起工具区与项目工具又使用相同 sliders 图标相邻。统一 .mode-actions 为有明确 gap 的布局，并区分收起区与项目工具图形，确保 960 宽下文字和各自命中区不拥挤。
4. FIRST VIEWPORT / 控件体系：1440-crop.png 右侧“角度（度）0.00”保留约 26px 高的默认白色输入框，明显脱离其余 40px 主题字段；intake.js:225 的裸 input 未命中共享 field 规则。接入同一字段高度、内边距、边框、主题与焦点样式，同时保留数值、单位和现有编辑语义。

## keep

保留墨绿酸橙及三可选主题、本地字体、准备上表下三图、裁剪结构、整 Fig 矩阵、高级抽屉底部主操作、演示标记和科学内容的稳定呈现。
