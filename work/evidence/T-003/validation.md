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

未运行：WB 检测/归一化/GUI/产品 Windows 包和绑定提交独立审查。
已有 P0 包是技术探针，不是 WB 交付软件。真实样本准确率和 T-001 标注集尚无证据。
门禁变化说明与外部依据见 docs/research/2026-10-14-wb-reference.md。

## TIFF 输入阶段，基线 3655a3a

- 38 项 WB 测试通过：含 15 个 TIFF/位深/极性/半开 ROI、不同宽度同信号、源文件及数组保护。
- 3 import-linter 合约通过；4 个独立图正/负例通过，新增 TIFF→积分传递依赖失败验证。
- 最终完整 dev.py check --all 退出 0：77 项测试、Ruff、Pyright、3 合约与隔离 wheel。
- 5 张本地真实 TIFF 的只读加载及 10 行均值烟测通过；私人路径/摘要留在 .local，
  没有认可条带标注，不能外推真实测量/检测准确率。
- wb-tool 0.2.0 构建和隔离安装通过，必要依赖由锁文件安装；不共享源码路径或宿主 site-packages。
- 初次 offline pip 解析失败：可用 wheel 缓存不等于索引元数据已缓存；改为 uv sync --locked
  --package wb-tool --no-dev --no-install-workspace 安装依赖后安装 wheel，退出 0。
- 粗糙内联 Windows 探针命令因引号失败，替换为可复用 tooling.wb_input_probe，退出 0。
