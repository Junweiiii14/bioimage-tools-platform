# R00 基线与交付事实（2026-10-28）

本记录为事实校准，未重跑 T081 安装验收。当前任务唯一来源为 `work/tasks/T-082-reliability-remediation.md`。

| 对象 | 已核验事实 |
| --- | --- |
| 本轮源码起点 | fetch 后 origin/main `18b5cf6de0c83b8c67f26433a6059d8dabf1f381`，与附件基线相同 |
| 本轮隔离树 | `wb-reliability-remediation/bioimage-tools-platform`，`codex/t082-reliability-remediation`；创建时 clean |
| 原目录 | ResearchVault 的 `feat/T-021-laboratory-figure-layout` / `bb5601a` 有既存 dirty 内容，全部保持，不能当最新源码 |
| 最近交付产品源码 | `f1e6142ab41e16c66cfeb3d33958ab3a364581b1`，T081 R2 实际构建来源 |
| T081 最终文档提交 | `6d02b82ecb5472ac78416e31e54707bf1b810736` |
| 主线集成 | PR43 合入 `18b5cf6`；Git 合并提交和旧活动树真实 `final-closeout.json` 一致，收据记合并时刻 2026-10-23T19:34:01Z |
| 实际安装器 | `BioImage-WB-Lab-Windows-x64-f1e6142ab41e-Setup.exe`；SHA256 `d4ff255ad422cc183b98c46dc39b6486035b9b79b4b438803d9baa46429c2d36`，383952574 bytes，来源 T081 交付证据 |
| 完整交付 ZIP | SHA256 `8581bc080464a8300aeba1eaca8e7c270840d42ba4110c1ee09be295a28705db`；旧 closeout 与 tracked 交付记录一致 |
| 验收边界 | T081 本机 Win11、37 安装态用例、7793 载荷/209 源码/163 模块核验是历史证据；本轮未重跑，不等于干净 Win10、全部物理 DPI/GPU或独立科学留出通过 |

T081 原本地 closeout 位于 `wb-lab-installer/bioimage-tools-platform/.local/T081/package/r2/final-closeout.json`，本轮已只读取得；它包含 final 文档四项 SUCCESS 链接及真实验收摘要，不能把旧 snapshot 的“下一步合 PR43”继续作为当前任务。原记录保持；旧故障、失败和 UNKNOWN 不销账。

## 范围与验证

R00 只修正 AGENTS 稳定规则中的过期任务号、README/发布入口、handoff 当前指针和本轮台账；没有产品/算法/锁/门禁代码变更。保留原 snapshot 到 archive。旧 T081 任务为历史闭合谓词，原文不改写成新的验证。

- Windows / PowerShell，uv 0.13.0、CPython 3.12.14；`git status/log/remote/worktree`、`git fetch origin main` exit0。
- `uv sync --locked --all-groups` exit0；仅本隔离树创建环境，83 个解析包/82 个安装包，锁文件无变更。
- `dev.py context --task T-082 --scope . --record` exit0；加载已有七份核心规则、恢复文档、任务。规则修改后重新加载。
- 产品测试尚未运行；下一项 R01 建立受控事件取消/异常行为回归。
