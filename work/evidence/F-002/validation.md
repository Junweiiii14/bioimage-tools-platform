# F-002 验证记录

日期：2026-10-13（Asia/Shanghai）。范围仅治理、非编码能力规范和规则门禁。

## 已验证

- GitHub API 返回 visibility PUBLIC；PR #1 合并，main 包含开发规则与原方案。
- main-quality ruleset 25008972 API 返回 active；禁止删除/强推、要求 PR、无 bypass actor、四个检查均限定 GitHub Actions app 15368。
- [故意遗漏规则回执的运行](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/38419477786)：head `6e1ebb7ecfee04753ad4b89b3d10af8e5718574f`，检查返回缺少 rules-context.json，退出 1；PR #2 mergeStateStatus 为 BLOCKED。未尝试绕过后合并。
- 隔离反例：head `03afb43fb013a50e7e1348ebff372c67cf8207c9` 的 [三个质量检查全部通过](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/38419922829)，只有 [规则回执检查失败](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/38419922786)；PR 仍为 BLOCKED，确认新门禁本身能阻止合并。
- 最新本地全量复验：Ruff、格式、Pyright strict 通过，29 个测试通过（16.53 秒，包含真实临时 Git 仓库的正反例与编码回归）。
- 初次本地 28 测试、格式、类型通过；后加 UTF-8 输出修正时 CI 检出 TextIOWrapper 类型未知，已采用有边界的标准输出配置修正，保留 strict 检查。
- 规则 loader 在默认 Windows 管道曾显示乱码；改为明确 UTF-8 后实跑中文可读。增加旧编码子进程回归测试。
- 父工作区 AGENTS 已补本仓库路由；本机 Git 身份设置为已登录 GitHub 账号的 noreply 邮箱，仅本仓库生效。

## 复验命令

```powershell
uv run --locked --no-sync python dev.py check --all
uv run --locked --no-sync python dev.py context --task F-002 --scope . --record
uv run --locked --no-sync python -m tooling.rule_context check --base origin/main --head HEAD
```

回执生成只证明规则版本与范围相符，不能证明模型理解；初次负例故意不记录回执。最终成功状态由 PR #2 的最新 head 检查绑定；本文件不自引用包含自己的提交哈希。

没有启动独立模型冷启动任务、没有绕过 hook 信任、没有运行产品功能或 Qt 安装包验收。工作流普通 pull_request 的定义可被 PR 修改，不构成防恶意维护者的不可篡改系统。
