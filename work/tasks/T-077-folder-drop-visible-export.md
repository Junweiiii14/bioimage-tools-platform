# T-077：工具入口文件夹拖入及可见结果导出

- 状态：implementing
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
