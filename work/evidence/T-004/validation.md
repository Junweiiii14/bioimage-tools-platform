# T-004 手工标注分析验证

日期 2026-10-14；Windows；Python 3.12.14；uv 0.13.0；base 93a84bb。
实现文件 wb_tool/application/analysis.py，包 0.3.0。

| 验证 | 退出码 | 证据及范围 |
|---|---:|---|
| pytest tools/wb/tests/test_analysis.py -q | 0 | 12 例解析三角形/零值、身份/来源/revision、局部失败、缺失/排除、位深提示、取消 |
| dev.py check --all | 0 | 90 测试，Ruff、Pyright strict、4 import-linter 合约 |
| 隔离 wheel 安装与 TIFF→手工分析 | 0 | 新 venv 按 uv.lock 装依赖，独立 wheel，-I/非源码 cwd；signal 10、revision 7 |
| application→具体适配器传递负例 | 预期 1 | 被合约拒绝；正例仍通过，新增负例包含在 90 测试 |

没有改变旧数值预期、skip 或放宽容差。门禁增加 application 纯度与应用层级，
测试合约总数从 3 更新为 4 是新增合约而非改成功条件。
未运行：GUI、真实进程取消/强停、工作区事务、产品打包、真实标注集、独立审查。
这不是软件完成或任务终态提交证据；宿主下一阶段还需拒绝过期 revision 并提交结果。
