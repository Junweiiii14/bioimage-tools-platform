disposition: ship

本轮为已批准 T075 世界内的 Operate 扩展；没有新的 approved comp、comp diff、concept seed 或 QUALITY BAR 卡，未将其缺席视为漏做新视觉世界流程。

## persistence

pass — 全新独立静态视觉审查，基线 `7fcb8192ada7acf5695e74f23cbe010ffd862966`，产品截图绑定 `e7eb3a2851efa8b43bbefb34b5b56ce8738a39fc`，分支 `codex/t076-platform-home-scroll`。读取 T076 任务与 `work/evidence/T-076/rules-context.json`（scope `.`）、PRODUCT.md、DESIGN.md、sidecar、T076 设计记录、继承的 T075 surface brief 与 craft floor；抽查共享 HTML、平台 CSS/JS、矩阵与编辑渲染。未修改产品、测试或规则回执，未运行 detector、浏览器或新截图。

已逐一打开 `.local/t076-visual-settled/` 下全部 12 张要求截图：`1440-platform.png`、`960-platform.png`、`1440-wb-home.png`、`960-wb-home.png`、`1440-matrix-last.png`、`960-matrix-last.png`、`1440-matrix-editor.png`、`960-matrix-editor.png`、`theme-forest.png`、`theme-ember.png`、`theme-iris.png`、`theme-neutral.png`。图像非空、无黑块、内容与名称一致；1440 图为 1440×900，960 图为 960×640，主题图为 1440×900。editor 图明确是滚到底查看操作区，不是编辑初始定位或完整曲线截图；局部滚动导致上部内容离开视口不构成坏截图。

`report.json` 记录 Windows Qt offscreen、Chromium 140.0.7339.225、`--disable-gpu`、DPR 1、本地 Noto Sans SC 已加载、pending 0 和空 console。主题图尺寸与 ground/rail 颜色另用 Pillow 只读采样核对。未以作者的 51 项及追加 5 项通过替代本轮视觉判断；也未重用 T075 验收覆盖本次矩阵反馈。

范围：本结论覆盖这些稳定状态的可见布局、层级、类型、颜色及显示内容。没有直接观察指针跟随、WB 成图动效、滚轮/键盘操作、编辑初始 reveal、关闭恢复位置/焦点、迟到状态与保存事务；这些须由本轮行为与代码证据支持。物理 DPI、硬件动效、安装版和科学结果正确性未验证。审查期间作者开始修改会话/编辑 reveal 逻辑，未将这些未提交改动绑定为本次已审产品；后续提交须按实际差异核查证据适用性。

提交适用性追加（2026-10-22）：已直接检查 `e7eb3a2851efa8b43bbefb34b5b56ce8738a39fc..d3aff15d53bf04c822976af0dd6b261f2b4dd6a1` 的文件清单和四个产品文件完整 diff。`desktop_session.js` 与 `preview_adapter.js` 仅更改 WB 首页新建命令路由；`web_window.py` 增加对应的原生选图/文件夹与新项目命令处理；`intake_quant.js` 只将编辑 reveal 的身份校验和当前 DOM 查询放入 rAF，并调整 pending 消费时机。其余两文件为行为测试。HTML、CSS、字体、图标、渲染模板、合成展示数据及主题 token 均未改动，已有 12 图所评估的相同稳定状态没有静态呈现变化。因此原 `ship` 静态结论继续适用于当前产品提交 `d3aff15d53bf04c822976af0dd6b261f2b4dd6a1`。截图的真实采集提交仍为 `e7eb3a2`；本次是基于源码差异核查的适用性确认，没有生成新版截图。编辑初始定位/连续快照、动效、新建事务及会话保护的正确性仍由当前提交的代码和行为独审负责，本追加不予代验。核查命令退出码 0；工作区仅见作者保留的 PRODUCT.md 与 docs/design 文档改动，未改产品或测试。

## fidelity

| 元素 / 承诺 | 状态 | 可见证据与依据 |
|---|---|---|
| THESIS：工具入口优先，当前对象可辨认 | match | 两张 platform 图中 WB 是唯一大面积主入口，最近项目位于辅助列；没有 IF/IHC 等未实现工具。符合 T076 用户批准范围与 PRODUCT.md。 |
| STORY：平台 → WB → 当前项目 | adaptation | 平台和 WB 各有明确首页标题，项目页面包屑继续保留 WB 与项目名；主题图中“当前打开 · WB”和“继续工作”作为会话状态信息。T076 明确授权在原 WB 首页前增加平台层级。 |
| FIRST VIEWPORT：1440×900 与 960×640 | match | 两个尺寸的主入口、顶栏与工作模式均无横向溢出；960 矩阵将测量详情收为入口以保留工作区。≤800px 单栏未在本批静态截图中覆盖，不外推为已目视通过。 |
| WB 首页原有内容与成图纸面 | match | 两张 wb-home 图保留仪器文件夹、独立灰度与裁图、已有项目以及 Fig 版式示意；960 下方内容通过外层滚动继续。没有把原首页替换为平台卡片。 |
| 整 Fig 最末行、最末列 | match | 两张 matrix-last 都显示 Protein 10 与泳道 18；纵向滚动和矩阵横向滚动均有可见滚动条。960 左边的局部列受滚动裁切，末列完整且蛋白标识仍固定。 |
| Fig 标题、蛋白列和曲线身份 | match | 滚到底后 Fig 1、10 蛋白、18 泳道的标题仍可见；Protein 9/10 固定在左，曲线格显示泳道号与 y 像素单位。未用缩小到不可读的全矩阵代替滚动。 |
| 编辑对象和保存区 | match | editor 图固定标题明确写 Fig 1 / Protein 10 / 泳道 18，收起调整与底部保存并重算区域可见；无草稿时操作禁用并有“已提交曲线”说明。960 曲线在上方滚动区，当前截图不声称曲线与保存区同时可见。 |
| 原图预览可收起 | match | 提供的矩阵状态已为曲线释放空间；源码有显式收起/展开按钮与 `aria-expanded`，仅改变显示。截图未直接证明该按钮点击行为。 |
| TYPE | adaptation | 中文本地 Noto 与继承的 WB Sans 保持一致，标题、工具名、正文和单位层级清晰。平台 32/26px 标题、26px 工具名、15px 分组题及 18px WB 标记属于局部页面层级，依据 T076 设计记录和既有 Operate 世界；没有改变系统字体或公共 token。 |
| MATERIAL | match | 平台的条带是明确几何装饰，WB 纸面是已批准且标为“版式示意”的几何 Fig；没有伪装真实原图的 CSS 材质、伪物理装饰或缺失新 raster。曲线保持科学示意而非装饰图。 |
| GROUND / OWN-WORLD | match | 对四主题图分别采样 (20,100) ground 与 (200,400) rail：forest `#f1f3e9/#103c32`、ember `#f4eee6/#302d2a`、iris `#eff1f8/#202c56`、neutral `#f3f4f3/#e9ece9`，与 DESIGN.md 完全相同；无未经授权的暖色/冷色漂移。 |
| 演示真实性与科研提示 | match | 页脚标为设计预览/演示数据；矩阵底部保留“所有数值仅用于界面体验”和“显示缩放不影响原像素计算”。右侧“测量记录”是全 Fig 按蛋白分组的独立列表，并非冒充当前 Protein 10 的记录。 |
| FORM 的静止表现 | match | 工具卡条带、箭头、原 WB 纸面和稳定命中区的视觉结构在场；只确认静止结构，4px 指针跟随、可中断转场和减少动态效果不由这些 PNG 得出通过。 |

现有 detector 为 6 项 advisory：32px、15px、26px、18px 字号与 2px 条带端头圆角（26px 有两处）。独立查看后，它们是局部层级与几何端头，不是字体替换、卡片层级失控或全局 token 漂移；没有 material finding。未发现 kicker、装饰侧条、硬偏移影、渐变字、系统展示字体或 Unicode 图标替代一致图标体系。WB 小标记、工具分组题和“当前打开”状态分别承担身份、分组与会话信息，不作为营销 eyebrow 判定。

## ceiling

reached — 在本轮 Operate 静态范围内，继承的明亮画布、墨绿/酸橙主次关系、本地字形、留白、可滚动科学矩阵和固定对象标识已经服务任务。没有需要新增材质、raster、装饰密度或视觉世界的缺口。动态品质未纳入此 ceiling 结论。

## material_fixes

无；本轮矩阵没有 missing 或 contradicted 的静态可见项。

## keep

保持平台工具入口优先、原 WB 首页、四主题与本地 Noto、可达的矩阵末行末列、固定 Fig/蛋白/泳道身份及清楚的演示边界；不要用装饰修改稀释这些已批准关系。
