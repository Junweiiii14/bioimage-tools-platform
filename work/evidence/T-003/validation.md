# T-003 验证记录

环境：2026-10-14；Windows 本机；Python 3.12.14；uv 0.13.0；分支 feat/T-003-wb-product。
基线 d83e4a0；本轮产物尚待提交，提交后以 Git 版本和后续检查记录为准。

| 命令 / 实验 | 退出码 | 结果与限制 |
|---|---:|---|
| dev.py check --all，改动前 | 0 | 35 测试，无产品包 |
| 源码 8 文件冻结及逐字节对照 | 0 | SHA 清单 reference-source.json；无来源 Git commit |
| pytest tools/wb/tests -q | 0 | 23 数值与错误输入用例 |
| pytest tests/test_import_contracts.py -q | 0 | 正图通过，传递 sqlite3 与反向层级图退出 1 |
| dev.py check --all，最终 Python 源码 | 0 | 61 测试；Ruff / Pyright strict / 2 import-linter 合约 |
| 隔离 wheel 安装 | 0 | 临时干净 venv、--no-deps、-I、非源码 cwd；公开 API 两个解析用例通过 |

未运行：WB 图像输入/检测/归一化/GUI/产品 Windows 包和绑定提交独立审查。
已有 P0 包是技术探针，不是 WB 交付软件。真实样本准确率和 T-001 标注集尚无证据。
门禁变化说明与外部依据见 docs/research/2026-10-14-wb-reference.md。
