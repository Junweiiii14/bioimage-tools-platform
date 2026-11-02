# 当前恢复指针

目标仍active、无预算：在bioimage-v0完成4.0 M1通用执行与M2真实可视编排，不缩成仅CLI或账本。分支codex/p005-workflow-executor，main基线006e9f143c830f5e13be2932e8ac37a9f3a05ed1；核对实际HEAD/dirty后接续。

用户最新要求优先：入口一次校验、内部信任不变量，删重复判空/验证，不滥用try/except，不为单次逻辑抽象，不写低概率防御。社区karpathy-guidelines已验证后项目配置，固定2c606141936f1eeef17fa3043a72095b4765b9c2，原文SHA一致、仅MD无hook、非作者独立核验/policy通过；配置提交bab41e0。技能不是自动修复保证。普通已授权操作连续做，独审集中可运行最终候选，不再逐个小提交循环审批。

## 当前任务

权威卡work/tasks/P-005-workflow-execution-slice.md保持in_progress，当前scope . 的新规则回执已实际加载，AGENTS/coding-standards为新简洁规则。P002/P003/P006/P007已分别通过既有PR集成done，不重做；P004仍单独planned，P008/P009待依赖。

- 账本/存储组件准确3215..418已独审/隔离wheels通过；证据journal-review-r1/r2/r3与journal-wheels，旧失败保留。
- 三固定WB节点及请求确认：823d首审发现NaN/负数可误发布valid；b80b900已复用旧ResultFrame完整校验并获89ba603..b80b900 Accepted，独立13pass22.86s，worker-review-r1保留Request changes。不要把该接受扩大到后继调度代码。
- 新WorkflowSession已实际自动派发verify/analyze/publish，后台可信注册/当前环境核验，PID账本确认后再发送请求，正式提交后更新账本。原来测试父循环已由生产控制器取代。单图与节点边界暂停/继续测试2pass；相关RunSession/模块共23pass36.34s。新增核验调用次数/线程断言后2pass10.86s：开始仅核验一次，明确resume重新核验一次，全部在后台。
- 新--workflow CLI实际执行triangle_u16三真实run、journal revision21/succeeded、表4000.0/text:valid，退出0；关闭后重开比对当前runtime源码指纹相同。work/evidence/P-005/auto-session.json记录实际源码SHA、日志、run IDs。Ruff/Pyright/policy/九import边界通过。新代码尚未最终独审/完整门禁/新wheels/CI，不是整卡或M1完成。

## 下一步：直接推进MVP

1. 控制器取消/关闭重开/存储故障/缓存矩阵19项已通过；桌面入口--workflow-ui复用同一执行器，后台输入准备、开始/暂停/继续/取消/重开/应用参数或样式新修订均已接通，5项真实界面测试通过。输入准备失败的重入关闭竞态已实际复现并修为只退休一次；旧失败证据保留。runtime-gui-recovery.json记录原生截图/真实4000三run与准确源码。
2. 当前冻结可运行候选，集中独审和完整dev.py check --all、四wheel最终重验与正常PR/四必需CI。此前四wheel/23联合/5界面通过不覆盖随后最后样式修补，不提前认整卡完成。主线base仍006e9f1，规则scope .有效。
3. P008复用同一账本/cache/recovery扩有限批量完整M1，随后P009真实增删/连接/替换/参数/保存重开/模板第二批M2；不重建第二执行器，不以静态图或JSON预检收尾。

## 当前代码与运行入口

apps/desktop/src/bioimage_app/workflow_session.py、workflow_preparation.py、wb_workflow_host.py、workflow_cli.py与RunSession是下一修改范围；tests/test_workflow_session.py实际控制器测试。CLI：uv run --locked --no-sync python -m bioimage_app --workflow --workspace <全新目录> --validation triangle_u16；原图/参数用--source和--parameters，恢复用--resume <execution_id>。不要覆盖已存在示例工作区。

本轮实际案例.local/p005-auto-mvp-20261102-verified-r2与日志.local/p005-auto-mvp-cli-r2.log保留，都是自有合成数据。旧snapshot完整归档archive/2026-11-02-before-auto-session-snapshot.md。PR52候选5814已推送，独审首轮P2非WB rerun无回执/关闭等待，作者正在入口修正并补真实回归，准确复审与新CI待做。旧local check session19645因修正主动中止exit1（约13%有F与GPU日志，原因未定位）；PID29552已查不存在。原日志保留，不能写通过；新全量使用CI同款--disable-gpu。实际HEAD/dirty必须核对。

## 保留边界

科学留出/负责人容差/S1、用户体验与干净Windows/物理DPI/GPU/T002-P0及旧native UNKNOWN仍见risks/backlog；这些不冻结无依赖工程。原图/历史/旧dirty树/在用安装不覆盖；不扩到新校正、其他实验全套、Agent、正式安装器发布/替换、外联、花费或数据上传。
