# 同源网页工作台

Target: apps/desktop/src/bioimage_app/web_ui/index.html
Mode: Operate; Web + QtWebEngine; code-led. 用户要求先网页、再完全同源还原，沿用已确认三栏与product-performs方向，不重新投票。

## Direction contract
THESIS: 从原图进入证据复核，当前来源、图像与质量原因始终可同时辨认；视觉精度服务图上操作。
OWN-WORLD: 正常照明的实验室，矿物白工作面、深松绿色窄平台栏、翡翠色选中状态，琥珀仅用于质量警告；系统中文UI字体、紧凑标签与舒展图像。
STORY: 平台选原图，自动处理，再在三栏里复核、排版、查看输出。网页预览明确只读记录/交互草稿，桌面连接真实后端，均不伪造有效信号。
FIRST VIEWPORT: 72px平台栏；66px项目顶栏，51px模式导航；244px来源区、弹性中央图像、296px复核区。右侧唯一确认动作；底部轻量状态。390px转单列与抽屉，不压缩三栏。
FORM: 延续已选product-performs、固定三栏用户约束；本次不是新的概念投票。signature为来源缩略图选择与中央原图/边界/右侧证据同步，非图像控件使用短过渡，图像证据与像素数值不插值。
FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Runtime and capability boundary
网页与 QtWebEngine 直接使用同一 `web_ui/index.html`、`styles.css` 和 `app.js`。网页只展示历史记录、维护交互草稿，不执行重算；桌面 bridge 连接真实 backend。高级曲线/积分边界、OCR、模板、实验信息和归一化仍在原生窗口操作。默认启动仍为原生平台，`--web-workbench` 显式进入同源桌面。

## Motion and responsive contract
模式指示线和抽屉入场 260ms，抽屉离场 150ms；按钮反馈 140ms、阴影 180ms。动效限于非图像控件，不对图像证据或定量数字插值。系统 prefers-reduced-motion 与应用减少动效选项将动画/过渡缩至 1ms。CSS 适配点为 1600/1180/900/620px；窄屏辅助栏移入抽屉，背景 inert、关闭恢复焦点。

## Evidence and limits
当前本地静态证据：`.local/t033/desktop.png`、`home.png`、`mobile.png`。截图不证明真实 backend 流程、动画体验、科学准确率或完整移动端可用性；T-033 主任务记录与提交绑定独审决定完成状态。网页与桌面同源不代表高级能力已全部网页化。

## Final implementation details
基于 `a68000e`：网页辅助文字 `#58675f`，原 8/9/10px 标签统一提高为 11px；图像 opacity/transform 过渡已移除。四角点方向键调整对应边界（默认 1 原像素，Shift 10），框体方向键平移；无 ROI 时在图上拖画，至少 4×4 原像素才提交。浏览器编辑仍为草稿，不产生新的科学结果。
