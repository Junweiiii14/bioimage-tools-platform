# P023 本机独立目录候选交付

2026-11-06，PR [75](https://github.com/Junweiiii14/bioimage-tools-platform/pull/75) 经指定独审与准确提交必需检查后正常 squash 合并。受审候选 `5dbfb394763227cb9a0befc1e28fd5a5c11a3334`，base `b13e71aa5aaebe91edecde44f386fc20ef693b19`，main `d3733a7e1edae6e195d129c751a707e62b7fedea`；main 与受审提交完整树 diff exit 0。

## 启动与实际范围

入口：`C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-plan-sync/.local/releases/runtime-5dbfb3947632-acceptance-p023-local/app/BioImageWB-Acceptance.exe`。目录内 `安装与使用说明.txt` 提供首次准备、输入限制、保存重开与设置重启说明。保留整个 app 目录，直接运行，无需开发环境。应用 0.14.0，通道 `wb-acceptance-p023-local`，独立设置 `Acceptance-p023-local`；旧实验室版未替换。

WB、单图核分割、BCA 与现有固定工作流/模板可用。核环境仍外置：`C:/Users/70236/ResearchVault/Codex-Workbench/p015-research/worker-env/Scripts/python.exe`，模型 `C:/Users/70236/ResearchVault/Codex-Workbench/p014-research/models/2D_versatile_fluo`。已通过实际候选设置保存；移动机器后这些本机路径不会自动具备，不能称完全自包含核分割安装包。

## 证据边界

三工具实际 worker、正式结果、冷重开、模板新数据、设置跨重启在 `969347929eefabe1d23009f653846d58ef899a05` 工件完成，详 README/native-evidence。最终六 wheel 与该基线逐字节一致，限定沿用功能证据；不把旧执行改称最终 SHA 独立运行。

最终准确工件由作者及独审分别通过真实 EXE 从仓库外启动、正确版本/三个入口、正常 Alt+F4/exit 0。作者最终启动不启调试端口；用户 Escape 中断后明确恢复操作，再完成关闭。独审设置前后摘要一致。最终 7900 payload 精确文件、506 archive、308安装源码/资源核验通过；独审额外双向集合509项无未知源码/缺失。见 [独审](independent-review-5dbfb39.md)、independent-evidence.json.gz 与 p023-final-{directory-audit,native}.json.gz。

冻结文件 SHA256：

- build-manifest.json：`af8dc3fb8868a3a57528e3417d56a50d673b804e6663f4e0b86243a7920877fb`
- payload-files.json：`ac0f02e299d7b9e3cd53868c92de6f7ea7e0b90bb9d2c03304bfea60306a5ab6`
- EXE：`b112d76395588e438e09bfff5408359d2e7d45e520ceb35880e6fa0ad81a4a30`
- source-code.zip：`abb62ddccc8065cf0ea10d16cfba14eb67c86ba91917bf4f85f9dbc819dd4274`

最终审计时目录逻辑大小1,131,109,416字节，运行后可增加Python缓存；外置worker 2,028,900,854字节/模型5,772,540字节。峰值内存、冷缓存启动时延未测。

## 检查与集成

[quality 42233985746](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/42233985746) 首轮成功：Windows 1778 passed/12 warnings/1568.37s，Linux 1774 passed/4既有skip/12 warnings/840.75s；两平台后续wheel与安装工作流检查成功。日志 p023-ci-{windows,linux}.log.gz。desktop-environment 与 [rules-context](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/42233985802) 成功；native-case为既有条件未触发，未称运行。准确head四项必需检查全绿、CLEAN后按上游条件授权合并，无绕过规则、重跑或超时放宽。

本机相关检查与失败已在README/build-notes记录，独审49项38.65s通过。一次本地收尾只写任务、交接和证据，沿用下一正常任务提交，不推纯收据触发CI。

## 保留项与交接

独审N01为既有来源核验器单向集合遗漏，实际最终包经独立双向核对无未知文件，因此非阻断；随下一直接相关来源核验任务用已有反例最小改进，不在本轮加循环。Linux历史收尾挂起根因UNKNOWN保留，当前首轮通过不表示根因修复。

干净Windows、真人、物理DPI/GPU、科学/化学准确性、用户安装升级/签名/发布未验或未执行；卡片堆叠预览未实现。原图、旧结果、旧dirty树、在用安装未覆盖。

本窗口完成P023后释放bioimage-plan-sync，后续由上游新窗口派发，不续开任务。主计划下一最小建议：围绕此候选的首次使用与输入准备做有界走查，集中处理实际阻断并形成真人试用反馈入口；已有本机候选和固定样例满足工程准备，真人/科学材料依赖由用户协调，不自行外联。N01仅随直接相关来源核验工作处理。
