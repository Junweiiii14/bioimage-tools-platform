# T-077：工具入口文件夹拖入及可见结果导出

- 状态：两项整改已完成本地与绑定独立验证；本任务在最终 HEAD 四项必需 CI 全成功后结束，并创建指定视频调研聊天。实时CI结果保存在 `.local/T077-final-ci.json`，不为重复状态文案再制造提交。
- base commit：6b6afd5c71cc20e20fa2dff8717938707bc6bf63（T076 四必要 CI success）
- 当前分支：codex/t077-folder-drop-visible-export
- 授权：2026-10-23 一次性 wb 自动化，完成两项整改且验证后才创建指定视频调研独立聊天。

## 目标与范围

1. 核对当前工具平台真实入口，为已安装 WB 接通 Windows 文件管理器文件夹拖入及既有目录输入流程；处理非法路径、多项、无效目录、忙碌/草稿和可见反馈，不扩展其他工具。
2. 最终结果表未审核时也能导出可见内容、顺序及格式可表达的样式，不要求未审核标记；缺失/失败不得转有效零。

保留 ResearchVault 旧 dirty 树和全部原图/历史输出。不改变科学算法、schema、依赖或门禁。最新活动树为 wb-ui-system；当前源与安装候选971d860差异仅既有测试/证据。

## 必读与修改范围

AGENTS、AGENT_HANDOFF 与相关交接、docs/module-map、architecture、coding-standards、规则回执流程；apps/desktop 与 tools/wb README、相关公开契约。范围 apps/desktop、tools/wb、tests、docs/contracts、work/tasks/T-077*、work/evidence/T-077、.agent-handoff。

## 验收

真实 WebEngine 拖入事件→宿主既有目录流程；单目录、多目录、普通文件/远端URL/无效目录、已有草稿/忙碌保护。未审核非空表的 Excel/CSV 与可见行列值相符，合法数值保留、缺失/失败为空或原有说明；XLSX 样式核验。绑定提交独审及必需 CI。所有命令和未覆盖项如实记录。

## 验证与独立审查

已完成12项新增/端到端回归、实际XLSX/CSV逐格比对和4张静态Qt截图。扩展回归首轮94过1夹具失败及修复、历史失败与限制见 work/evidence/T-077/validation.md。绑定提交独审与最终必需CI待执行。

## 视频任务

两项均完成验证前不创建；通过后按用户全文任务创建本项目本地新聊天，gpt-6-astra/ultra，先 create_goal、不设预算，传递真实提交、审查与安全合成素材。

## 最终实现与独立结论

- 最终产品 `c32ad11106d0f49d1d7babc91d2f987bb2d3e12e`；草稿PR38，base T076 `6b6afd5`。只读旧ResearchVault树/历史/971d860安装均保留，修正版由本活动树Start-BioImage.ps1启动。
- 本机作者最终输出22项/11.67s/exit0；此前95扩展/97.01s/0、20拖入/两出口/格式13.87s/0。测试时序、舍入、XLSX格式及审计路径调整理由和原失败均在validation，未改容差/skip/锁文件/门禁。
- 非作者产品独审Accepted，base6b6afd5..c32ad11，最终24项/12.16s/0；39成员摘要及严格旧ZIP恢复相等。报告 work/evidence/T-077/independent-review-c32ad11.md。ddc阶段报告标Superseded。独立设计记录绑定c32ad11，静态5图ship，不外推物理输入/硬件验收。
- 自动结果目录和直接导出均使用可见原始积分宽表；新目录旧审计另存measurement-audit.*，index.table_policy显式版本化，旧目录/ZIP内部表不迁移。
- 全合成演示素材 `.local/deliveries/WB-T077-safe-demo-c32ad11`，108文件/5,432,183字节逐项SHA核验；两个300×700 uint16源、两Fig×5泳道、AKT标签仅作演示。旧演示副本保留。

## 完结谓词与后续聊天

1. 最终HEAD与远端相同，产品文件与c32ad11所审相同；rules-context、desktop-environment、foundation Windows/Linux四项均SUCCESS。native-case可按工作流正常skip，不冒充运行。
2. 未满足1，不启动视频调研，不将goal完成；如失败，读取真实日志处理，不能改门禁/成功状态。
3. 满足1后只创建一次本项目本地独立视频聊天，model=gpt-6-astra、thinking=ultra，第一步create_goal且无token_budget；全文授权/目标及真实证据/安全素材传入，wait_threads有界确认启动。创建状态写本地 `.local/T077-video-start.json` 与自动化memory；不为副本创建新功能聊天或周期任务。
4. 不合并/发布，不重建原安装，不覆盖原图或历史；物理Explorer/OLE、干净Win10、DPI、科学留出、外部Excel/WPS/LibreOffice和历史native UNKNOWN另记。
