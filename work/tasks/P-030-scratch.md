# P030 划痕闭合需求与可行性

<!-- PROGRAM_TASK_META {"id":"P-030","status":"in_review","head_commit":"03a02057da3813fc9005333e0a5f96d0212b187c","work_package":"W14","depends_on":["P-013"],"execution_root":"C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-plan-sync","owner":"chat-01a1bce6-570e-7002-b569-b896b6f72f5d","base_commit":"0b0c4c532add70dfb1f3a36cd8cc8a53e9f84a77"} -->

核验一条公开序列、许可和参考，原样调用上游分割，逐帧比较并界定学生操作、重复单位、MVP及排期。不扩产品或依赖。携带 P029 一次收尾。指定独审、CI 和集成待办。

[研究与复验](../../docs/research/2026-11-09-scratch-closure.md)。独立新目录回放四帧与首次运行相同，退出 0。实际宏四帧均输出 ROI，12 h 和 24 h 闭合方向与多边形参考相反，暂缓自动 MVP。

作者检查：Windows，研究提交 03a0205；固定源重放、policy、handoff 容量、ruff 及提交钩子通过。首次直接 git commit 未激活环境，未提交；改用 uv run 原钩子通过。计划检查 exit 1 仍为 P010 历史 head 缺项。首次回放脚本未兼容 ZIP stored 成员，修正后新目录完整回放 exit 0。独审/CI/合并待回执。
