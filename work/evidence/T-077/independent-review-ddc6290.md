> Superseded：本阶段报告绑定ddc6290；最终完整产品审查已由[c32ad11独立报告](C:/Users/70236/.codex/worktrees/wb-ui-system/bioimage-tools-platform/work/evidence/T-077/independent-review-c32ad11.md)替代。保留原阶段证据，不用于代替最终writer覆盖结论。

# T077 独立审查：目录拖入与可见结果导出

- 结论：**Accepted**，无未解决的产品阻断发现。有限静态视觉结论为 **disposition: ship**。
- 审查者为非作者独立子代理；未修改产品、既有测试、分支、HEAD或门禁，只新增本报告。作者在审查期间按发现提交修正；下述最终结论绑定修正后的完整产品差异。
- base：`6b6afd5c71cc20e20fa2dff8717938707bc6bf63`
- head：`ddc6290f303ba8160326fcd29eb5423c4a67adad`
- 分支：`codex/t077-folder-drop-visible-export`
- 树：`C:/Users/70236/.codex/worktrees/wb-ui-system/bioimage-tools-platform`
- 收尾时间：2026-10-23 02:49 Asia/Shanghai（2026-10-22 18:49 UTC）；审查期间各阶段检查分别记录。
- 环境：Windows 11 10.0.26200；Python 3.12.14；PySide6 6.12.0；Chromium 140.0.7339.225。独立 GUI 测试使用 `QT_QPA_PLATFORM=offscreen`、`QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu`。

## 代码审查依据与结果

已读根规则、恢复指针与风险/待办、T077、module-map、architecture、coding-standards、research-protocol、rule-enforcement、桌面/WB README，以及可见结果表 v1、清单输出 v1、采集组 v1、项目归档 v2 公开契约。两个模块没有自己的 AGENTS.md。检查了 base..head 全部产品差异及新增测试；没有按作者的成功说明直接判定通过。

- 拖入：原生 URL MIME 始终 CopyAction；URI/相对路径/控制字符/数量在无文件 I/O 的边界拒绝，目录状态及 TIFF 遍历复用后台 ProjectSelectionJob。WebEngine 命中仅在平台 WB 卡、无弹窗时接受；后到回调另核宿主/epoch。进入既有新建/切换会话流程，忙态拒绝、草稿返回保护和失败反馈未绕过。
- 可见值：页面和导出共用 proteins 稳定顺序、最大 N 宽表投影；raw_integral 与有效信号分开。坏证据、缺失和失败仍无值，真实 0 保留；有原始积分的质量警告保留星号。未改算法、schema 或历史归档表。
- 导出链：最终保存后重建结果展示；后续导出重新收集并在后台核验请求/run/资产，未直接信任页面缓存。已有取消、generation、发布前检查和无覆盖写出保持。新 adapter 不在 GUI 线程读写文件；桌面外部入口仍使用 wb_tool.api。
- 大表：原逐蛋白统计及逐格 tooltip 的重复扫描已在 fe25fc1 改为单次字典/Map 索引；终态输出及 DOM 结构未变。该审查不是 512×96 实机交互延迟基准。
- 测试/门禁：没有更改容差、skip/xfail、类型忽略、锁文件或门禁。后续 XLSX 测试修正为读取实际 styles/numFmtId 再按其显式位数比对；这比旧的手工两位格式化能多检出整数格式错误。

### 审查中发现并复核关闭的项

1. **CSV 舍入不一致（原 ce73bd2/fe25fc1）**：UI 的 Intl 最多两位显示 1.005→1.01、2.675→2.68、1.125→1.13；Python `.2f` 原为 1、2.67、1.12。4ca8f50 改为 Decimal(str(value)) + ROUND_HALF_UP，4ef1115 只将辅助函数重命名为 display_intake_number。独立实际 Node Intl 对照 10,011 个边界/相邻浮点/固定种子值，无差异；原 double 未改。
2. **XLSX 可选小数格式风险（原至 4ca8f50）**：`#,##0.##` 中的小数点与可选数字占位不同，不能用 XML 值的 Python 重格式化证明整数显示一致。微软的[格式规则](https://support.microsoft.com/en-us/excel/review-guidelines-for-customizing-a-number-format)明确区分小数点与可省略零的 #；本机没有 Excel、WPS 或 LibreOffice，未声称在这些软件实际重现。1e639ba 改为按可见 0/1/2 位选择明确格式及质量版本，4ef1115 保持。独立注入合法 ProjectTableCell 的 adapter 边界实验核验：400.004 / 400.104 / 1.125 的 raw 单元格不变，格式为 `#,##0"*"` / `#,##0.0"*"` / `#,##0.00"*"`，CSV 为 400* / 400.1* / 1.13*，缺项仍“—”。关闭该源格式风险，仍不冒充外部表格软件兼容验收。

3. **末轮hover与就绪等待复核（ddc6290）**：去掉拖入激活态浅底覆写，仅保留虚线，恢复既有深底/浅字配对；重新打开新增hover与四张重捕获，未见修正引入的静态回归。作者报告过一次19过1败的保存间隙取值时序失败；独立此前20过不否认该失败。最终测试仅新增 !state.busy 与10个已提交rawIntegral就绪前提，原逐格/质量断言、超时、skip均未削弱；最终独立20项通过。4ef1115的独立20项/12.00s/exit0作为阶段记录保留，不替代最终结果。

### 独立执行记录

所有 pytest 命令的前置环境均为上述 offscreen / disable-gpu；未设置 T077_EVIDENCE，因此没有重拍或覆盖作者截图。

| 修订/阶段 | 命令或实验 | 实际结果 |
|---|---|---|
| 最终 ddc6290（运行前后 HEAD 相同；产品/测试无dirty，仅两份未跟踪审查文档） | `uv run --locked --no-sync pytest -q tests/test_folder_drop.py tests/test_visible_export_desktop.py tools/wb/tests/test_intake_visible_export.py` | **exit 0；20 passed / 11.78s**；10 条 QDragEnterEvent 旧构造函数弃用警告 |
| 4ca8f50 阶段，相关代码后有作者修正 | `uv run --locked --no-sync pytest -q tests/test_folder_drop.py tests/test_visible_export_desktop.py tools/wb/tests/test_intake_visible_export.py tests/test_project_start.py tests/test_project_entry.py tests/test_project_navigation_session.py` | exit 0；41 passed / 22.20s；同类10警告。后续导出/CSS变化已由最终20项复验 |
| 早期 fe25fc1 阶段，作者随后改动 | 三个新功能测试文件同最终命令 | exit 0；12 passed / 11.69s；该结果仅保留阶段证据，不替代最终20项 |
| 4ca8f50 阶段命令错误 | 上述新功能文件加 tests/test_project_start.py 与不存在的 tools/wb/tests/test_csv_export.py | **exit 1；no tests ran / 0.23s**；纠正为真实文件后得到41项结果，未删除此失败 |
| CSV 原反例 | `node -e` 实际调用 toLocaleString('en-US',{maximumFractionDigits:2})，与 `uv run --locked --no-sync python -c` 的原 `.2f` 对比 | 两命令 exit 0；观测到上述 1.005 / 2.675 / 1.125 差异 |
| 4ca8f50/1e639ba 的同一舍入实现，最后仅改名 | stdin Python 构造 -1500..1500 的百位小数中点及 math.nextafter 两邻值，加固定种子7701的1000个值与零/负零等8值；subprocess 调用实际 Node Intl 并逐值比对 | exit 0；**10,011 values，0 mismatches** |
| 1e639ba，最终仅改名 | stdin Python 在 adapter 填表边界注入上述三项 raw/quality 及缺项，读取实际 CSV、sheet1.xml、styles.xml | exit 0；raw 精度、0/1/2位/星号样式及缺项符合预期 |
| 文件拖入代码未再变化 | stdin Python 调用实际 FolderDropView._target，使用显式排队回调的假页面端口 | exit 0；更换 host/epoch 后旧 True 回复拒绝；False 拒绝；同 context True 才接收；zoom=1.5 的60/90坐标映射40/60。此为回调边界实验，不是物理 Explorer 操作 |
| 补充销毁探索 | stdin Python 创建未加载页面的 FolderDropView，发起 _target 后 shiboken6.delete(page) | exit 0，但未观测到目标回调，不作页面销毁竞态通过证据；stderr 有软件图形 GLES fallback/context 诊断 |
| 规则读取 | 按当时已有 receipt 的 task/base/scopes 实际执行 `uv run --locked --no-sync python dev.py context ... --record` | exit 0；相关规则另经逐文件阅读。作者随后重生最终 base6b6afd5 回执；最终报告前只读核对，未再次改写 |

独立未运行完整 check --all、wheel 安装、doctor/audit 或远端必需 CI；这些结果必须由作者的独立证据与当前 PR HEAD 核对。物理 Explorer 鼠标、硬件 GPU、目标机 DPI、干净 Windows、科学留出以及历史 native UNKNOWN 不因本次通过而解除。

## 有限静态视觉 finish review

disposition: ship

专用 finish-reviewer agent_type 未提供，使用独立通用子代理按 degraded/finish-reviewer.md 检查契约执行；并非作者内联自验。未提供新的 approved comp、QUALITY BAR card、comp-diff 或概念 seed：本次为用户已固定 T075/T076 方向的 Operate 窄扩展，不重新投概念或设计全局外观。结论仅覆盖四张指定静态视口、新增1440拖入hover视口与本次扩展。

### persistence

pass：PRODUCT.md、既有 DESIGN.md、.impeccable/design.json 与 t075-ui-system.md 均存在，方向与构建世界一致。已重新实际打开检查四张指定 PNG，加看新增 platform-hover-1440.png，均非空、没有黑块，平台页和结果页内容与文件名相符，文档顶端可见。尺寸分别为1440×940、960×640；960结果页为有滚动的视口截图，不冒充全页。

作者在最后一轮有效流程重捕获四张指定截图及新增hover截图；本审查重新打开了这五个确切路径，并重新核对摘要。ddc6290的hover浅背景覆写已移除，实际hover截图保留原墨绿底与浅字，并显示卡片外虚线；其余布局和表格值无新增回归。没有用前轮结果截图替代本轮重捕获，也不把截图当作动态硬件证据。未重跑 detector，使用父代理已给的旧动态 img/src、圆角/字阶 advisory；本轮新增提示/outline无新机械 warning 的陈述只作为该机械记录。

| 捕获 | SHA256 |
|---|---|
| platform-1440.png | 72b012459d1748103dadd7e0bb9f8c7ab97b19b02d8560623a4a38e5b7ce51f7 |
| platform-960.png | bf97bb05b9010b1442c2c84c0ae4379511f5fa83f80fd8854f67ebdf7588f53f |
| platform-hover-1440.png | 361909d394dbb3fa49e34f8b3346d435f54bb50938ed495c2e06c70e58d5c80d |
| results-1440.png | f1e543a3ad75a5a2e0d02a1a7c494f3f884426a15c15b948fa6f44ebd2eb9f93 |
| results-960.png | b450be75e2da47b9ca4a91e191ec45d65d0e13ade54c81b2c7548ced692a758a |

### fidelity

| 元素 | 状态 | 可见证据/契约依据 |
|---|---|---|
| TYPE | match | 延续本地 WB Sans/Noto Sans SC 的既有层级；中文、表头、辅助提示及数据可读，没有新显示字体或装饰数字 |
| MATERIAL | match | CSS平面工作面、真实表格和已有一致SVG几何；没有伪造物理材质或新增未交付栅格义务 |
| GROUND | match | 平台空白像素为RGB241/243/233，符合ground #f1f3e9；结果页浅色工作面和墨绿外壳延续既有体系 |
| 工具入口与拖入提示 | adaptation | 原WB卡下增加一行明确的本机目录拖入说明，用户授权的入口能力可在数秒内找到；1440与960均完整可读 |
| 结果表与导出操作 | match | 两行同名AKT仍按Fig分开；泳道1..5、千分位、小数、质量星号、状态和“—”说明可见；960下五列与状态完整呈现 |
| 阅读顺序与小窗口 | match | 保留顶栏、阶段导航、结果标题、导出按钮、主表和详情入口；未见新增遮挡/横向溢出。更大N仍按现有局部滚动契约，不由本截图证明 |

### ceiling

reached within scope：现有工作台的墨绿、酸橙主操作、明亮数据面、稳定控件位置与层级已延续；没有本次静态证据能支持的新增材质/字号/装饰缺口。没有QUALITY BAR card，因此不宣称对未给定世界卡、动态效果或整个产品达到新的设计上限。

### material_fixes

无未解决静态视觉 material fix。已复核hover浅底修正：虚线可见，原卡片文字/深底对比保持，没有新增遮挡。截图不验证完整焦点/disabled/错误态、物理拖拽激活、动画、物理鼠标、DPI或GPU；相关行为由代码与上述测试在其各自边界内支持。

### keep

保留稳定的主操作、蛋白/Fig身份、原始积分/有效信号分离、缺项和质量文字；不要用隐藏警告或改变数值来换取更整齐的表格。

