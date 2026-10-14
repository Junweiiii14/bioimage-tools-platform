# T-005 后台协议与真实 worker 验证

2026-10-14；Windows；Python 3.12.14；uv 0.13.0；base 45d0c5f。
包 0.4.0；协议 v1；积分 profile_integral@1 未改变。

| 验证 | 退出码 | 结果与范围 |
|---|---:|---|
| 最终 dev.py check --all | 0 | 123 测试、Ruff、Pyright strict、4 导入合约、独立 wheel |
| worker 专项 | 0 | 33 个正/负例纳入最终检查 |
| 真实源码 worker | 0 / 预期 2 | TIFF 解析信号 10；错误源/协议失败；合作取消及无 ResultFrame |
| 隔离 wheel worker | 0 | 新 venv 锁定依赖，-I、非源码 cwd，python -m wb_tool.worker 真实执行 |
| JSON Schema 漂移 | 0 | Pydantic + 现有 dataclass 唯一字段源，机器快照一致 |

额外验证：整数布尔版本拒绝，额外字段（含深层 ROI）、非有限值、重复 JSON 字段、
过大帧、缺换行、过期 attempt/revision、重复结果、取消后的结果、未请求取消的确认均拒绝。
结果结构检查不是科学算法独审，也不是 host 终态事务证明。

过程失败真实保留：pytest.raises 的测试调用参数错误，后续内联小修未指定 UTF-8 产生 GBK 读失败；
采用文件补丁修复。Literal 相等值导致 bool 被接受；对结果添加 before validator 又导致
JSON array→tuple 的 strict 模式变为 Python 输入规则。最终改为原始 JSON 标签/重复键预检，
再解析原字节，所有原预期通过；未削弱 strict/extra/finite 或删除负例。

未测：宿主 QProcess/UI、强停/进程树、工作区原子发布/SQLite、重启恢复、Windows 产品包、独立审查。
干净 Windows 按用户先前决定保留待办。目标继续 active。
