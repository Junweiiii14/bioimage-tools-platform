# P005账本组件验证（不是整卡验收）

基线006e9f143c830f5e13be2932e8ac37a9f3a05ed1；本次新增源码工作于3215e3e之后，准确冻结提交由git历史及独审回复记录。环境为现有Windows/Python3.12.14锁定环境，未增依赖。

- 首轮新测试：7 passed / 1 failed，退出1。恢复测试首次保存revision5违反Workspace新文档须从0开始；修正为逐事件CAS保存，不修改存储约束。
- 修后账本/P007契约/Workspace：77 passed / 9.12s，退出0；其中新账本8项。真实等待子进程只有测试所有，失败finally只回收其实际Popen对象。
- Ruff format/check及contracts/runtime与新测试Pyright strict通过；不增加ignore、skip、xfail或放宽旧断言。
- 两节点组件成功、边界暂停/继续、candidate后真实exit7不成功、新attempt身份、底层提交后缺账本关联的真实重开/幂等对账、重复/错序/错身份、未启动取消、控制预算保留取消、严格JSON/schema反例已验证。复用指向原物理run，不新建PID，并同时校验持久科学计算键和解析文件绑定。

测试夹具的输出文件由测试父进程写入，不是正式WB worker图输出。这不是三节点引擎、完整文件缓存准入、GUI/CLI或故障矩阵验收；存储线程生产接线、实际环境核验、磁盘满/运行中关闭等仍未实施。未运行本提交完整门禁/独立wheels/CI；独审待准确提交。P005保持in_progress。
