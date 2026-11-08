# P027 最终交付

普通文件夹中的单张原名 TIFF 可以从首页 WB 卡片导入。配置一组 Fig/GAPDH 并勾选原图后，泳道数 N 缺失时可以保存、重开草稿，自动处理禁用。独立灰度入口可打开同一图并等待框选。来源识别后误报草稿冲突已修复；完整走查、方法与证据边界见[实际记录](README.md)。已安装版本和 P023 冻结候选未更新。

[PR79](https://github.com/Junweiiii14/bioimage-tools-platform/pull/79) 正常 squash 合入 main 3103063d1abf116ef1d98694b9cc57f4dc70ae22。git fetch 后受审 05d04b2e942078cc1f5b988af135aaedde2d695b 与 origin/main 完整树 diff exit 0。初始产品候选 4168f9c 的本机锁定环境仪器桌面模块 37 passed（85.03 秒）。[首审](independent/independent-review-4168f9c.md)复核普通单图、N 留空保存与重开、真实编辑冲突及参考组保护，仅任务卡元数据 R01 待改；[最终独审](independent/independent-review-05d04b2.md)确认关闭。独审报告里以 .local 为根的观察和摘要归档在 independent 下。全局计划校验仍先报历史 P010 缺 reviewed commit，未修改历史卡。

准确最终头四项必需检查通过。[规则](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/42512044682)和[质量检查](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/42512044704)。Linux 首轮 1774 passed、4 skipped、12 warnings；desktop-environment 通过，native-case 条件跳过。较早产品头的双平台作业因任务卡提交被取消。

Windows [首轮日志](windows-attempt1.log.gz)记录桌面回归在 12% 通过，随后套件持续前进，到 97% 的 test_real_worker_cancellation[False] 通过后约 1.4 秒因作业 30 分钟上限被取消。未见失败断言或 60 秒挂起栈；总耗时波动的原因未确认。保留原尝试，只重跑同 SHA 的 Windows 作业一次，未放宽门禁。[第二轮](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/42512044704/job/128835120710) 1778 passed、12 warnings，pytest 1157.64 秒，作业 22 分 10 秒。

一次本地收尾随下一正常 PR 带入。下一窗口从任务卡恢复，生成下一项规则回执时纳入本次收尾回执。真人、科学方法验收及干净 Windows 缺项保留。
