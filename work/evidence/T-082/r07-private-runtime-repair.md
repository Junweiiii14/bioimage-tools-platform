# R07 真实私有解释器验收发现与修复

## 真实失败

`d66655b0cfd241c07f3b8647e08b1b3ef567e2d3` 完整门禁已 exit 0（1501 pytest + 独立 wheel）。实际构建在深路径 Inno 压缩时失败，文件存在且路径 260 字符；相同提交在短路径 `C:/Users/70236/AppData/Local/Temp/T082-final-d66655b` 经完整构建成功。旧版升级起点 `244c5da1b03e47f6d17801912cb38003e8edab27` 也成功构建为同一隔离 acceptance 身份。两个安装器均未替换 Laboratory。

新干净检出的 PowerShell 5.1 wrapper 使用最终候选自带 `app/runtime/python.exe` 核验该候选，真实 exit 1，报告错误 `Unexpected payload file: runtime/Lib/__pycache__/argparse.cpython-312.pyc`。报告留于 [r07-private-runtime-failure.json](r07-private-runtime-failure.json)；原完整请求/输出/exit 在 `.local/T082/r11/最终候选 核验-ps51/` 与 `final-verify-ps51*`。第一轮在 PS5.1 失败即停，PS7 的真实候选检查尚未运行，不能写成双 shell 通过。

候选构建在 14:54:08 结束，argparse 缓存实际创建于 14:55:47，即 wrapper 调用时。wrapper 原先只使用 `-I -X utf8`；隔离模式不禁止字节码写入，验证器导入标准库先污染自身待验运行库，严格文件清单随后正确拒绝。此前测试的解释器位于候选之外，未覆盖同路径情形。

## 最小修复与有效反例

wrapper 只补 `-B` 并说明原因，保留 `-I`、UTF-8、准确退出码、报告留存及现有缓存拒绝。验证器实现未放宽文件清单或跳过缓存，模块文档和运行手册明确私有解释器直接调用也使用 `-I -B`。

新回归在新的临时候选中复制当前锁定 CPython/标准库，冻结 payload，再分别通过实际 PowerShell 5.1/7 使用该候选自己的 Python 验证它。原 wrapper **2 failed / 9.43s**，两个失败报告均是未冻结 argparse 缓存；修后 **2 passed / 21.43s**。每例要求完整 payload 文件集与字节摘要保持，并追加未认证缓存后确认仍失败且缓存保留。没有改 skip 条件、容差或成功预期，没有清理真实失败候选。

`tests/test_candidate_acceptance.py` + `tests/test_runtime_integrity.py` **48 passed / 43.44s / exit 0**；Ruff、格式、Pyright、产品/测试 diff 检查通过。原始 red/green/regression 输出位于 `.local/T082/r07-private-python-{red,green,regression}.txt`。

## 后续路径

独立审查者 `/root/independent_review` 对 `f5d7ac9e05b0d701818ceced7277edd09d10024b` 相对 d66655b 的八文件差异给出 **Accepted**。独立命令 `uv run --locked --no-sync pytest tests/test_candidate_acceptance.py -k 'wrapper_private_python or windows_wrapper_preserves or unfrozen_bytecode' -q --tb=short` 为 **5 passed, 29 deselected / 21.13s / exit 0**，日志 `.local/T082/r07-private-python-independent-f5d7ac9.txt`。另双 shell 实际探针确认 isolated、dont_write_bytecode、utf8_mode，中文/空格/特殊字符路径与尾反斜杠保持，Python exit 7 原样返回；材料在 `.local/T082/r07-independent-f5d7ac9/`。无新产品改动、缓存清理或清单放宽。

独审也比对深/短路径构建：源码、工具、uv lock、运行库和四 wheel hashes 完全相同，短路径编译及安装器退出码均 0；失败报告与原件相同，污染候选的 argparse.pyc 仍存在。

现在重新冻结必要门禁及最终包；首次失败候选的额外缓存和失败报告保持，使用新的冻结构建输出验证，不删除缓存促成通过。旧升级起点已用外部可信开发 Python `-I -B` 完成严格核验，并于独立中文路径安装 exit 0，登记版本为 `0.14.0-Acceptance-t082-r11-a-244c5da1b03e`；其已安装 7794 个载荷文件与清单完全对应，额外仅 unins000.exe/dat。五快捷方式只指向本轮目录，旧 Laboratory 的登记/设置/快捷方式/身份文件摘要与安装前相同。它仅用于跨版本升级，不声称最终安装态已通过。实际最终升级、旧 schema、双诊断与卸载仍待完成。
