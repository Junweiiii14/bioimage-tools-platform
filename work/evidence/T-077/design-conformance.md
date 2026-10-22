# T077 独立设计一致性记录

- 记录时间：2026-10-23 02:52 +08:00；初审 02:45，悬停修复复核 02:47，输出契约增量核对 02:51。
- 审阅树：`C:/Users/70236/.codex/worktrees/wb-ui-system/bioimage-tools-platform`。
- 分支：`codex/t077-folder-drop-visible-export`。
- 绑定产品 HEAD：`c32ad11106d0f49d1d7babc91d2f987bb2d3e12e`。
- 视觉复核 HEAD：`ddc6290f303ba8160326fcd29eb5423c4a67adad`；至最终产品 HEAD 界面、视觉资源及证据图未再变化。
- 初审产品 HEAD：`4ef111555dbfbad9b435cb3fdee315fa14f1b871`；修复后只复核该发现、最终截图及文件保持情况。
- 比较基线：`6b6afd5c71cc20e20fa2dff8717938707bc6bf63`。
- 角色：独立 Impeccable documenter；只写本文件，不修改产品、设计系统、测试、规则回执，不提交。

## 范围与结论

本轮是既有 Operate 工作台的窄功能扩展：WB 工具卡本机目录拖入复用仪器导入；未审核的最终可见结果表按同一行列投影导出。没有新视觉世界或设计系统扩展授权。

静态结果页、共享显示投影与导出契约在核对范围内一致；设计文件、字体、主题和公共 token 保持。初审发现的一项新增活动态配色问题已在最终 HEAD 修正并经源码及悬停图复核为 resolved。本轮窄扩展符合所核对的既有设计契约；结论限于下列文件、状态和证据，不替代独立代码审查与必需 CI。

## 核对材料与方法

已读根 AGENTS、模块地图、当前任务、既有规则回执与交接当前指针；已读 `PRODUCT.md`、`DESIGN.md`、`.impeccable/surfaces/t075-ui-system.md`、`docs/contracts/wb-visible-result-table-v1.md`、桌面及 WB README 的相关段落，以及 Impeccable `reference/document.md`、`reference/degraded/documenter.md` 和 `reference/new-work.md` 第 7 节。

已检查 base..HEAD 的四个网页差异：`index.html`、`platform_home.js`、`platform_home.css`、`intake_views.js`；并抽样核对 `web_bridge.py`、`web_intake.py`、`figure_window.py`、`intake_result_table.py`、`intake_table_export.py`、`worksheet_export.py` 和现有 `design_tokens.css`。

最后补充仅阅读 `ddc6290..c32ad11` 的六文件小 diff 及两份完整公开契约 `wb-visible-result-table-v1.md`、`wb-intake-output-v1.md`：范围为自动输出 writer、相关测试/验证记录与契约，不包含界面或设计系统变更。未扩大视觉检查、未重采截图、未运行新增测试；既有悬停 resolved 与五图结论沿相同界面资源保留。

实际执行：Git 分支/HEAD/status、定向 diff、blob 身份/工作文件 hash 核对（相关命令 exit 0）；Impeccable context 与 surface-brief read（exit 0，存在下述既有上下文警告）；初审四张及修复后最终五张 PNG 均通过图像工具实际打开。最终 base..HEAD 设计系统/字体/token diff 仍为空。此角色未运行产品测试、导出程序、机械 detector、物理桌面操作或 CI，未将这些检查写为通过。既有 `rules-context.json` 覆盖 `work/evidence/T-077`，本角色仅核对而未重写回执。

## 保留系统及字节证据

base、HEAD 与当前工作文件的 Git blob 身份分别完全一致：

| 文件 | 三方相同的 blob |
|---|---|
| `DESIGN.md` | `c758a1fef6c541064b1f9b7182f15a8c0a9a38da` |
| `.impeccable/design.json` | `4cdf63c96d1a7cba4b0f45eeb1fc6836379448d2` |

`design_tokens.css`、`fonts/`、`appearance.js`、`components.css` 的 base..HEAD diff 为空。没有把局部目录提示尺寸、XLSX 表头或活动态新增为公共 token。

## 契约与静态证据

- 工具卡：保留既有入口按钮，新增拖入说明、`aria-describedby`、`role="status"`，DOM 命中仅接受工具平台当前的 WB 卡及无打开 dialog 状态；错误消息复用就近说明与 toast。没有显示未实现工具。
- 可见结果：宿主与文件导出共用 `intake_visible_table@1`，按清单蛋白稳定身份和顺序生成 Fig、蛋白、泳道 1..最大 N、状态；显示取原始积分，非 valid 积分保留质量星号，缺项为“—”，真实零保留。蛋白按钮和状态原因继续可达。
- 格式：CSV 适配器按可见数字文字和星号输出并沿用可逆 `text:` 协议；XLSX 保留数值 double、明确的 0/1/2 位格式与星号、表头强调、右对齐、冻结身份列/表头及列宽。它不逐像素复制主题或界面字体；契约明确主题不进入科研数据，CSV 不承诺工作簿样式。这些文档描述与所核对源码一致；实际文件逐格验证来自作者记录，非本角色复跑。
- 自动输出目录（最终增量）：`measurements.csv/xlsx` 现调用相同 `intake_table_bytes`，与直接导出使用同一可见宽表及格式；旧完整审计另存 `measurement-audit.csv/xlsx`。`index.json` 保留 `intake_output@1` 外层并增加 `table_policy=intake_visible_table@1`。两份公开契约明确无该字段的旧目录仍按旧布局解释，`project.zip` 内部旧表与恢复字节核验保持，不迁移/重写历史目录；该叙述与所查 writer diff 一致。新增测试比较 CSV 字节以及 XLSX 主表 XML/styles，旧槽位/来源审计断言改读审计文件，未把容器时间戳或审计修订差异解释为可见表差异；本角色仅读取，未复跑。
- `platform-1440.png`（1440×940）与 `platform-960.png`（960×640）：确为工具平台首页；WB 入口、最近项目区域、目录提示和既有墨绿/酸橙视觉均可见，无空白帧。960 高度有页面滚动，未将下方内容截断解释为缺失。
- `results-1440.png`、`results-960.png`：确为同一两 Fig、五泳道结果页，10 个积分、6 个质量星号及“3 项需查看”状态与 `visible.json` 一致；结果表和导出入口可见。未审核没有被显示为有效归一化值，也没有被要求先审核才显示导出。静态样本无缺项或真零，不能由图片单独推导这两类边界通过。
- `platform-hover-1440.png`：视觉复核 HEAD `ddc6290` 的有效 Qt 静态捕获，WB 卡保留深底及原标题/说明/进入 WB 配色，外侧虚线轮廓可见，新增活动态问题按此有限证据复核 resolved；最终 `c32ad11` 未再修改界面，未宣称此图是在新 HEAD 重新捕获。

## 本轮问题与未覆盖状态

**[P2，resolved] 拖入活动态继承的浅色文字与浅底配对。** 初审 `4ef1115` 的 `platform_home.css:3` 将 `.installed-tool.folder-drop-active` 背景换为 `--accent-light`，但卡标题仍继承 `--shell-ink`，描述/已安装文字为 `--shell-muted`，进入 WB 为 `--primary`；例如 forest 标题 `#eff3dc` 对 `#e6efcf`。这些 token 原为深色 rail 配对，不能把该问题 canonize 为设计规则。实现者在 `ddc6290` 仅移除了活动态背景覆盖，保留 `2px dashed var(--accent)` 外轮廓及原深底/文字配对，未动任何主题 token。本角色已核对该单行 diff，并打开新增悬停图确认标题、说明和操作可读、轮廓可见；此项 resolved。产品修复由实现者完成，本角色仅记录与复核，未实时执行拖入或其他主题动态验收。

作者 `validation.md` 记录了 Windows Qt6.12 软件渲染、合成 URL 拖入事件/焦点子控件、真实后台扫描/存储/worker，以及未审核结果的实际 XLSX/CSV 逐格核对。它同时保留失败与调整记录。上述材料可支持所描述的工程链路，不证明物理 Explorer/OLE 鼠标全过程、硬件 GPU、物理 DPI、干净 Win10、目标机体验或科学留出。现有安装目录未重建；本轮静态截图不替代安装验收。

最终提交后的实现者交接另报告 20 项 / 13.87s / exit 0、实际表格逐格相符、导出后显示保持，并交付本次打开的最终五图。这是实现者的运行证据，本角色未复跑，不能替代相应命令日志和独立产品审查。

## 既有 drift：记录而不维修

`PRODUCT.md` 的 Evidence on Hand 仍指向 T076，`DESIGN.md`/sidecar 保留 T075 的历史候选与验收叙述；它们是既有设计来源，不是 T077 的当前任务状态。Impeccable context 将自由文本 Platform 识别为 web，并且 surface briefs 未提供可唯一匹配的 primaryTarget；surface-brief read 返回候选列表，已直接读取指定 T075 brief。以上均在 base 已存在，本轮未刷新、重写或将其当成 T077 完成证明。

## 五行系统摘要

1. 色板：沿用 forest 默认墨绿/酸橙、ember、iris、neutral 四主题及科学中性画布。
2. 字体：沿用本地 Noto Sans SC / WB Sans，正文 14px、辅助 12px、表格 13px，数值表格字体特性保持。
3. 空间：保留 32/24/16/8 间距及 40/32px 控件体系，长表与窄窗口使用既有局部/页面滚动。
4. 规则：Stable Position 与 Real Receipt 继续要求对象、草稿和保存状态可信；Evidence Stays Still 不允许科学数值装饰运动。
5. 语义：显示舍入不进入定量；缺项、质量、审核、有效信号和保存完成分别表达。

未 canonize 或维修：初审活动态缺陷未升级为系统规则，已由实现者修正且本角色按最终 HEAD 复核 resolved；既有上下文/历史文档 drift 超出窄扩展授权，仅如实记录。
