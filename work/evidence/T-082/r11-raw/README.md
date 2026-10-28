# R06/R07/R11 原始文本证据归档

本目录只保留真实执行的原始文本证据，不是安装包或新的验收结论。当前状态及未验边界由 [T082](../../../tasks/T-082-reliability-remediation.md) 管理。产品源码/最终完整门禁/最终构建源码均绑定 `ed830e1d3bab3d0c8c57f3766a898991e8a0f431`；更晚的文档提交不改写构建来源。

- [r11-evidence.zip](r11-evidence.zip)：183 个文件，压缩前 22,893,099 字节，ZIP 2,954,135 字节。
- ZIP SHA256：`78b0e5809bdb85911b9f5d1754bfc9f0a75b4686fe17ebd24f80620070695bf8`。
- [manifest.json](manifest.json)：每个成员的原始绝对路径、成员名、字节数和 SHA256；列出选择范围、排除项与归档自验。
- 归档使用逐字节原件，保留 BOM、换行、空日志及失败输出。ZIP 中 `packaging/package-r11-evidence.py` 是本次选择及打包脚本，执行时拒绝覆盖已有归档目录。

## 恢复入口

| ZIP 路径 | 内容与边界 |
| --- | --- |
| `gates/` | `44ee78c` 的实际失败，以及 `d66655b`、`ed830e1` 完整门禁日志和 exit/HEAD 记录；旧失败不因后继通过而删除 |
| `builds/d66655b-deep-failed/` | 深 worktree 路径构建的 Inno 失败日志及当时 manifest；没有把失败安装器阶段写成成功 |
| `builds/d66655b-temp/` | 同源码短路径构建；之后旧 wrapper 运行污染和后续缺文件记录仍在 `r11/` |
| `builds/244c5da-temp-upgrade-base/` | 真实跨版本升级的旧版构建文本、manifest 和 payload 清单 |
| `builds/ed830e1-temp/` | 最终源码首次 Temp 构建的文本；后续严格核验失败，不能作为最终验收工件 |
| `builds/ed830e1-persistent-final/` | Temp 外重新构建的最终工件；完整依赖/产品 wheel/编译/安装器日志、外层及 app manifest、payload 清单 |
| `r11/*候选*核验*/`、`requests/` | 实际 PS5.1/PS7 与不同候选的失败、恢复和通过报告，以及报告所绑定的原始请求 JSON |
| `r11/升级起点候选 核验/`、`r11/升级前安装内容 核验/` | 旧候选与实际旧安装的严格核验 |
| `r11/ed830e1 升级后严格核验/` | 最终真实安装目录的严格核验；与仅候选验证区分 |
| `r11/ed830e1 安装态双诊断/` | 两项实际启动器诊断、模块路径探针、stdout/stderr、进程身份/退出/超时与后续缓存记录 |
| `r11/ed830e1 安装态历史项目/legacy-verification.json` | 安装私有运行时对 schema 1–6 的旧金样验证；合成样本不证明独立科学适用性 |
| `r11/最终历史样例 d66655b/fixtures.json` | 合成样本来源及摘要；本包不含图像和生成的项目 ZIP |
| `r11/install-*`、`r11/upgrade-*`、`r11/uninstall-*` | 实际初装、同 AppId 跨版本升级、卸载的启动/退出/完整日志与数据保留清单；卸载辅助脚本保留实际边界检查 |
| `r11/laboratory-*.json`、`r11/acceptance-shortcuts-*.json` | 在用 Laboratory 的散列快照及独立验收快捷方式身份记录；Lab 注册表/设置仅保存摘要，不包含原始值 |
| `r11/missing-payload-investigation.json` | 三个 Temp 候选后来各缺失 98 个零长度文件的只读调查；删除原因/进程/时间仍为 UNKNOWN |
| `r11/installed-native-screen*`、`r11/native-screen-probe.py` | 安装 Qt 的原生屏幕指标观测，不代表实际交互、全部物理 DPI 或多屏验收 |

`r11/live-checkpoint.json` 是 **15:14 时的历史检查点**，其中运行会话、旧安装与下一步不能作为当前状态；后续 exit、升级、诊断及卸载记录保留其真实演进。原始诊断 `limitations` 的“本工具不执行安装/升级/卸载”是该诊断工具职责边界；实际安装生命周期由本包另列的进程及安装器日志证明，不能相互替代。

私有 Python wrapper 的缓存失败及 `-B` 修复详见 [R07 修复证据](../r07-private-runtime-repair.md)。归档保留真实失败报告及后继新候选的恢复关联，没有删除缓存、补造零长度文件或改写失败状态促成通过。

## 本地保留位置与范围

最终独立验收安装器保留于：

`C:/Users/70236/.codex/artifacts/T082-ed830e1/.local/releases/runtime-ed830e1d3bab-acceptance-t082-r11-a/BioImage-WB-Acceptance-t082-r11-a-Windows-x64-ed830e1d3bab-Setup.exe`

记录的安装器 SHA256 为 `5c49309132a8152c8b095dd255acdcef9adf02ecfa68175e36a6de83be724268`，384,432,982 字节；对应 `r11/ed830e1-persistent-artifact.json`。它是 `t082-r11-a` 可弃工程验收身份，未替换 Laboratory，也不是正式发布。

原始文本仍留在 manifest 所列本地路径。只收 `r11/` 顶层文本、明确列出的报告目录、报告引用的请求、三个冻结门禁，以及五个候选根的构建文本和 app manifest。没有递归收取源码检出、已安装运行时、私有原图或任意用户目录。安装器、EXE/DLL、模型、图像、`source-code.zip`、历史验证生成的二进制渲染/项目归档均未纳入；其摘要仍可见于原始验收记录。未收取的源 checkout 可从仓库准确提交恢复，合成样本可由已有仓库验收工具重建；重建不替代本次原始执行记录。

打包脚本对 183 份内容执行文本解码和凭据模式扫描（私钥、常见 GitHub/OpenAI token、Bearer header、URL 内用户名密码），发现 0 项；这与明确的合成材料选择一起限制暴露范围，不宣称通用秘密检测保证。本地路径及测试设置哨兵是刻意保留的执行证据。

## 归档自验

本次打包退出码 0；所有成员重新读取，通过 ZIP CRC、字节数/SHA256 与原始文件字节比较。只运行归档自验，没有再次运行产品、测试、安装或清理。

新检出可用 Python 标准库只读核对（从本目录运行；不解压、不执行成员脚本）：

```python
import hashlib
import json
import zipfile
from pathlib import Path

manifest = json.loads(Path("manifest.json").read_text(encoding="utf-8"))
archive = Path(manifest["archive"])
assert archive.stat().st_size == manifest["archive_bytes"]
assert hashlib.sha256(archive.read_bytes()).hexdigest() == manifest["archive_sha256"]
with zipfile.ZipFile(archive) as package:
    assert package.testzip() is None
    assert set(package.namelist()) == {item["member"] for item in manifest["files"]}
    for item in manifest["files"]:
        data = package.read(item["member"])
        assert len(data) == item["bytes"]
        assert hashlib.sha256(data).hexdigest() == item["sha256"]
```

归档完整性不等于科学适用性、干净 Win10、其他员工设备、物理输入/DPI/GPU 或外部 Office 验收通过。这些结论继续按任务及独立复核保留。
