# F-004 验证：Dependabot PR #5

2026-10-15，Windows 本机；base 221a2dff610554092a881fc396010f032b31ae33，原PR head b826878279bbc5cd5b9c13cdb5e88408e46611be。

## 原因与修复

原 rules-context 日志明确：`PR needs exactly one changed rules-context.json; run dev.py context --record`。本次只补独立任务、按PR实际base生成的唯一规则回执与交接/验证文档。原有两个setup-uv SHA替换保持，不修改检查逻辑、必需检查、权限、uv0.13.0或锁文件。

## 上游核验

- [目标commit](https://github.com/astral-sh/setup-uv/commit/37802adc94f370d6bfd71619e3f0bf239e1f3b78)：Fetch uv from Astral's mirror by default (#809)。检查了该提交源码、打包dist和测试diff：Astral镜像优先，失败回退GitHub，镜像请求不携带GitHub token；继续现有checksum路径。
- [action.yml](https://github.com/astral-sh/setup-uv/blob/37802adc94f370d6bfd71619e3f0bf239e1f3b78/action.yml)：node24，入口dist/setup/index.cjs，post缓存入口dist/save-cache/index.cjs。本项目仍固定uv0.13.0。
- 旧SHA `94527f2e458b27549849d47d273a16bec83a01e9` 目前在上游commit API返回422，compare返回404，不能声称完整旧新diff审计。目标SHA可取得，最终以新SHA在实际GitHub runner的成功执行核验兼容；不把CI当作上游无漏洞证明。

## 本地检查

| 命令 | 返回码 | 证据与边界 |
|---|---|---|
| uv sync --locked --group desktop | 0 | Python3.12.14，按现有锁创建独立环境 |
| python -I tooling/rule_context.py load --task F-004 --scope .github --scope work/tasks --scope work/evidence/F-004 --scope .agent-handoff --record | 0 | 已读取本分支规则/任务，回执基线为上述main |
| uv run --locked --no-sync python dev.py check --all | 0 | Ruff/42格式/Pyright0错误/29测试（22.30秒）；产品扫描0，本分支无产品代码，不是产品验证 |
| uv run --locked --no-sync python dev.py smoke-env | 0 | Qt6.12.0、QProcess、offscreen、中文路径uint16 TIFF通过；不覆盖DPI/产品包 |

规则回执最终验证与远程CI绑定提交后在主开发目录F-003证据补记；推送前必须本地通过，远程四项未完成前不称完成。独立审查未执行；本任务无产品修改，不合并或发布。

## 推送后的真实结果

修复提交 `01f35ae27c86849a3db8e5975ab806c2ce9bc7a2` 已推送原Dependabot分支。本地 rules-context check 返回0。

- [rules-context](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/38696979789)：SUCCESS，5秒。
- [quality](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/38696979780)：Ubuntu SUCCESS/14秒、Windows SUCCESS/46秒、desktop-environment SUCCESS/30秒。
- PR #5：OPEN / CLEAN；未合并。本收尾提交只更新任务与交接文档，最终head的检查另核对。
