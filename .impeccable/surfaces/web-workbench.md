# 同源网页工作台

## T045 手动泳道与整图Fig定量

延续本页Operate方向与三栏视觉体系。用户已经明确要求旧WBQuant手动操作回归，
并批准自动Fig切分后直接定量、按需手动修改。左侧同处提供框选/复制/删除/清空/重选、
分组切换和自动处理；中央始终显示原图或源图Fig区域，右侧为参数/结果；不另开旧工具。
普通完整泳道多峰与UB整段模式共用曲线/封底编辑，自动OCR歧义可见，旧组结果保持。
当前新增能力为既有视觉体系扩展，未批准或执行整体重设计；已有sidecar漂移不在本次修复。

Target: apps/desktop/src/bioimage_app/web_ui/index.html
Mode: Operate; Web + QtWebEngine; code-led. 用户要求先网页、再完全同源还原，沿用已确认三栏与product-performs方向，不重新投票。

## Direction contract
THESIS: 从原图进入证据复核，当前来源、图像与质量原因始终可同时辨认；视觉精度服务图上操作。
OWN-WORLD: 正常照明的实验室，矿物白工作面、深松绿色窄平台栏、翡翠色选中状态，琥珀仅用于质量警告；系统中文UI字体、紧凑标签与舒展图像。
STORY: 平台选原图，自动处理完成后直接进入拼图，正常裁图无需逐张确认；点击拼图图像返回对应原图调整，再按 Fig 进入灰度监督与结果。导航依次为裁图→拼图→灰度→结果。网页预览明确只读记录/交互草稿，桌面连接真实后端，均不伪造有效信号。
FIRST VIEWPORT: 72px平台栏；66px项目顶栏，51px模式导航；244px来源区、弹性中央图像、296px复核区。图像复核右侧主要动作为返回拼图；底部轻量状态。390px转单列与抽屉，不压缩三栏。
FORM: 延续已选product-performs、固定三栏用户约束；本次不是新的概念投票。signature为来源缩略图选择与中央原图/边界/右侧证据同步，非图像控件使用短过渡，图像证据与像素数值不插值。
FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Runtime and capability boundary
网页与 QtWebEngine 直接使用同一 `web_ui/index.html`、`styles.css` 和 `app.js`。网页只展示历史记录、维护交互草稿，不执行重算；桌面 bridge 连接真实 backend。T-037 的曲线、泳道范围、积分边界和直线封底监督直接在同源界面内操作，桌面修改后自动重算，不跳旧定量窗口。OCR、模板、实验信息和归一化仍在原生窗口操作。默认启动仍为原生平台，`--web-workbench` 显式进入同源桌面。

## Motion and responsive contract
模式指示线和抽屉入场 260ms，抽屉离场 150ms；按钮反馈 140ms、阴影 180ms。动效限于非图像控件，不对图像证据或定量数字插值。系统 prefers-reduced-motion 与应用减少动效选项将动画/过渡缩至 1ms。CSS 适配点为 1600/1180/900/620px；窄屏辅助栏移入抽屉，背景 inert、关闭恢复焦点。

## Evidence and limits
T-037 本次对照 `fa5e5e3` 基线及当前工作树核对实现；门禁与提交绑定独审仍由主任务跟进，未宣称全产品通过。下面的截图是历史静态证据，不覆盖新增灰度监督。

当前本地静态证据：`.local/t033/desktop.png`、`home.png`、`mobile.png`。截图不证明真实 backend 流程、动画体验、科学准确率或完整移动端可用性；T-033 主任务记录与提交绑定独审决定完成状态。网页与桌面同源不代表高级能力已全部网页化。

## Final implementation details
既有 T-033 视觉记录：网页辅助文字 `#58675f`，原 8/9/10px 标签统一提高为 11px；图像 opacity/transform 过渡已移除。T-035 基于 `96366e9` 核对交互：裁剪宽高比为 1.25 × 泳道数 n，四角点拖动与方向键等比调整（默认高度步进 1 原像素，Shift 10，宽度按比例取整），框体方向键平移；无 ROI 时在图上拖画比例范围，宽高至少各 4 原像素才提交。修改 n 保持裁剪高度，仅调宽；超出原图则提示先缩小框。原图不缩放改写，显示变换不进入定量。拼图命中区来自实际渲染图像边界及来源 ID，支持点击与键盘回原图。裁图状态 cropStatus 与定量质量独立；就绪不代表信号有效或人工审核。浏览器编辑仍为草稿，不产生新的科学结果，历史拼图不冒充草稿结果。T-035 验收以主任务证据为准，以上为代码核对记录。


T-037 灰度页按 Fig 使用真实 montage，泳道框依据渲染区域的 sourceRoi 与 sourceLaneRange 映射各自原图。每张原图对应一段曲线，间隔、文字和拼图边框不参与积分。组内泳道不一致或缺少裁剪时明确阻止组映射并显示原因，保留原图独立监督入口。右侧组内结果逐积分区间呈现数值、质量状态与可展开原因。点击条带、曲线段或结果表数值回到相应原图、泳道和积分区间；桌面调整范围、边界或封底自动重算，浏览器只展示历史曲线。灰度表及分组导出采用两位小数，缺失值保空，计算记录保留完整精度。

本次为已确认视觉体系内的普通能力扩展；DESIGN.md frontmatter 和 design.json 的视觉 token 无需更新。既有 sidecar 中三模式及高级曲线仍为原生的能力描述已过时，本次按限定写入范围保留，不将其作为 T-037 能力依据；能力边界以 PRODUCT.md 和本 surface 记录为准。


T-045（普通扩展）恢复独立完整泳道的复制/删除/清空/重选、共享原图新组和修改/拆并分组；曲线补峰/排除及32步会话撤销重做不恢复历史run。UB整段模式在几何调整和重开后保留，独立泳道/规则网格显式切换。显示描边按实际缩放保持1.5px；手形、Space或中键平移，取消不改泳道。手动工具默认折叠、最多占侧栏40%，Fig列表至少160px。产品3f4c593；本地私图截图.impeccable/review/desktop.png、manual-desktop.png、desktop-960.png、ub-profiles.png不提交。截图只证明静态布局，实际worker/指针/保存重开证据见T-045验证。shipped documenter只读核对原配色/字体/组件/布局，无token变更；预存默认原生入口/曲线仍原生的说明漂移保留，不在本轮改造DESIGN或sidecar。
