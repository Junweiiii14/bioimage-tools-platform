## verdict

- resolved — 蛋白导航：新 1440-layout.png 的 p-AKT、AKT、GAPDH 分别占独立整行，有明确间距与 Fig 层级，不再连写。
- resolved — 预览遮挡：新 960-home.png 与 960-settings.png 的演示栏位于独立底部区域，内容和抽屉在其上方结束，不再浮压于按钮或字段上；内容仍可滚动。
- resolved — 工具入口：新 960-crop.png、960-layout.png 的详情文字与后一工具图标之间已有清晰间距，收起工具区采用独立 sidebar 图标；1440-layout.png 同样可辨认两类入口。
- resolved — 角度字段：新 1440-crop.png 的 0.00 输入采用统一主题背景、圆角、内边距与 40px 控件高度，单位和恢复动作保持可见。

## remaining

- 直接回归 1：新 960-crop.png 相比旧同名截图，“裁图就绪”标签完全消失于图像视口上沿之外，下方泳道编号贴边并被裁切。此次 preview-mode 将 app-shell 缩短 48px 后，画布默认适配未同时给 ROI 外部标注留出空间。请让适配计算包含状态标签和泳道编号的上下余量，并以相同 960×640 状态复验；不改变 ROI 或科学坐标。
- 边界：核对 HEAD 1d872bf2c09c9463b463f18412139da160f0be0d，工作树干净；必需 26 张文件存在，重点复读上述 6 张对应 PNG，报告记录 Windows / Chromium 140 / DPR1.5 / console=[] / settled。此轮只评分原四项及其直接回归，不是整套界面的重新批准，不声明安装、CI、科学验收或完整硬件验收完成；未运行浏览器、服务器或重新捕获。

disposition: fix
