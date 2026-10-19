# WB worker protocol v1

入口：`python -m wb_tool.worker`。入口在加载数值库前，将 worker 的 OMP、OpenBLAS、
MKL、NumExpr 线程数量限制为 1；不修改宿主环境或用户配置。一个进程只处理一个任务。
大图使用 source_path 和来源 SHA256，图像数组不进入消息。worker 不写工作区或 SQLite。

stdout 为 UTF-8 NDJSON，每条消息 payload 最大 4 MiB，以 LF 结束；日志使用 stderr。
输入缺换行、非法 JSON、重复字段、过大帧、额外字段、类型强转、NaN/Inf 和版本不符均拒绝。
所有消息含 protocol_version=1；整数标签不接受布尔值。

| 方向 | kind / sequence | 内容 |
|---|---|---|
| worker→host | hello / 0 | 协议版本和容量 |
| host→worker | start / 0 | run_id/attempt_id/request_id、文件路径、完整请求快照 |
| worker→host | accepted / 1 | 同一身份，任务已接收 |
| host→worker | cancel / 1 | 同一身份的一次合作取消 |
| worker→host | result / 2 | 带原请求的严格 AnalysisResult，尚未提交宿主终态 |
| worker→host | failure / 2 | 明确错误码和简短原因 |
| worker→host | cancelled / 2 | 合作取消的结果候选；宿主仍须确认进程已退出 |
| worker→host | protocol_error / 1 | start 无法建立身份时拒绝请求，退出码 2 |

机器 schema 由 Pydantic 和现有 dataclass 字段生成：`wb-worker-v1.schema.json`。
反向解析复用现有请求验证，不手写另一套 ROI 或积分字段定义。额外语义校验包括：
结果数量/身份/标注与请求一致，剖面尺寸/极性/位深一致，基线来源与值一致，
失败/缺失/排除不携带有效测量，待复核不冒充 valid；有效信号非负有限。
解析结果结构不是对条带科学正确性或积分算法独立审查的替代。

`WorkerConversation` 是纯宿主会话门禁，拒绝错误身份、乱序、重复终帧、旧 revision、
取消后的结果和未经请求的取消确认。它不管理 OS 生命周期或保存事务。
取消监听使用不带 Python 缓冲锁的 OS 读，避免 daemon 在线程退出时持有 stdin 缓冲锁。
在文件解码等不可中断区间，取消等待检查点；后续宿主负责超时强停并标记 interrupted。
未知崩溃、无终帧或未完整提交不等于成功。CLI 正常 result/cancelled 退出 0，明确失败退出 2。

v1 的图像剖面会随结果发送；超过容量时明确失败，不截断、不返回部分成功。
后续工作区资产提交可接管较大结果，UI 仍需保持来源 revision 和提交一致性。
