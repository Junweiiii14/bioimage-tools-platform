# 严格边界与真实 worker

问题：怎样复用现有不可变请求/结果字段，同时阻止外部 JSON 强转、额外字段和非有限值？
选择 Pydantic 2.14.1 的封装模型，沿用已有锁版本，不修改领域类的全局配置。
ConfigDict strict/frozen/extra=forbid/allow_inf_nan=False 传播到 stdlib dataclass 字段。
依据：[严格模式](https://docs.pydantic.dev/latest/concepts/strict_mode/)、
[配置传播](https://docs.pydantic.dev/latest/concepts/config/#configuration-propagation)、
[序列化](https://docs.pydantic.dev/latest/concepts/serialization/)，访问 2026-10-14。

实测：整数版本的 Literal 可接受布尔相等值，因此协议整数标签额外检查 type。
结果 schema_version 需要在原始 JSON 层检查；对整个 result 增加 before validator 会把
JSON 元组解析带入 Python 的严格 list/tuple 规则，破坏正常往返，已移除该做法。
先检查原始标签与重复键，再用 validate_json 解析原始字节，保留合法 JSON array→tuple。
没有放松 strict、删除反例、修改预期或引入领域对 Pydantic 的依赖。

真实子进程从 TIFF 到 signal=10 的解析样例通过；source SHA 不符退出 2。
合作取消及错误取消身份不返回 ResultFrame；host 会话拒绝旧 revision、旧 attempt 和重复帧。
取消测试使用真实较大 TIFF 和排队的 cancel，不在 worker 添加测试专用延时。
入口限制数值线程，OS 无缓冲输入监听避免 daemon 持有 stdin 缓冲锁。

限制：这不是 GUI/存储/强停完成证据。宿主仍需管理进程退出、资产事务、重启恢复和
旧 revision 的显示策略。机器 schema 不替代自定义语义校验或真实科学标注。
