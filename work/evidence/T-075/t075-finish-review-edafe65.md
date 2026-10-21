## verdict

- resolved — 直接回归：新 .local/t075-final-source/960-crop.png 中，“裁图就绪”完整显示，泳道编号 1–6 均完整可读，ROI 四角和上下边界没有被视口裁切，底部缩放控件与预览保留区不重叠。
- resolved — 标准窗口对照：新 1440-crop.png 中状态标签、泳道编号、ROI 边界和右侧角度字段正常；本次适配修正未见直接可见回归。
- 初轮四项保持上一轮 resolved 结论；本轮按要求不扩张复查。

## remaining

clear。核对 HEAD edafe65e1451ecf2e5cb695f9f6b33ddfda2e49e，工作树干净；本轮直接查看上述两张同名新截图，报告记录 Windows / Chromium 140 / DPR1.5 / pending=0 / console=[]，两张截图均有效。

本次 ship 仅覆盖已评分修正，不覆盖整个界面。不声明安装、CI、科学验收或完整硬件验收完成；未运行浏览器、服务器或重新捕获，也未改产品文件。

disposition: ship
