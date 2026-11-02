# P005账本组件验证（不是整卡验收）

基线006e9f143c830f5e13be2932e8ac37a9f3a05ed1；本次新增源码工作于3215e3e之后，准确冻结提交由git历史及独审回复记录。环境为现有Windows/Python3.12.14锁定环境，未增依赖。

- 首轮新测试：7 passed / 1 failed，退出1。恢复测试首次保存revision5违反Workspace新文档须从0开始；修正为逐事件CAS保存，不修改存储约束。
- 修后账本/P007契约/Workspace：77 passed / 9.12s，退出0；其中新账本8项。真实等待子进程只有测试所有，失败finally只回收其实际Popen对象。
- Ruff format/check及contracts/runtime与新测试Pyright strict通过；不增加ignore、skip、xfail或放宽旧断言。
- 两节点组件成功、边界暂停/继续、candidate后真实exit7不成功、新attempt身份、底层提交后缺账本关联的真实重开/幂等对账、重复/错序/错身份、未启动取消、控制预算保留取消、严格JSON/schema反例已验证。复用指向原物理run，不新建PID，并同时校验持久科学计算键和解析文件绑定。

测试夹具的输出文件由测试父进程写入，不是正式WB worker图输出。这不是三节点引擎、完整文件缓存准入、GUI/CLI或故障矩阵验收；存储线程生产接线、实际环境核验、磁盘满/运行中关闭等仍未实施。未运行本提交完整门禁/独立wheels/CI；独审待准确提交。P005保持in_progress。

## 后续存储线程接线与修订分离

首版26f7f78独审Request changes见journal-review-r1.md；非零图generation不能直接当新请求文档revision。后续新attempt请求固定新文档revision0，图generation仍保留在冻结plan。新增实际plan revision7/真实Workspace准备反例验证修正。

AsyncStorage新增固定workflow命令，在既有存储线程读取/校验/归约/序列化/CAS，仍无新SQLite DDL。调用者不能传入RunRecord/manifest充当存储事实；从实际Workspace读对应记录和已提交manifest，并检查其请求/全部输入输出文件。复用另从旧持久账本读取科学计算键。关联写盘失败后保留真实run，重开按独立文档/请求摘要精确查找，不造第二个run。

新增3项（合计11项账本/存储测试）：非零generation与节点document0、失去控制回复后相同ID/旧CAS幂等；真实准备完成后注入ENOSPC使账本关联写入失败，真实关闭重开恢复interrupted且唯一run/PID=None；存储线程序列化受屏障阻塞时主GUI计时器继续响应。原重开组件案例现通过实际workflow存储命令恢复/复用，并验证篡改测试自有成果后拒绝缓存且目标账本不变。

接线首轮17项pytest通过3.55s；首次Pyright6个测试注解/私有导入使用错误，补类型并使用公开函数引用后0错误，无ignore。随后受影响账本/异步存储/RunSession/模块RunSession/图契约/Workspace共99passed26.33s/exit0；新增物理缓存损坏反例后最终99passed26.76s/exit0。Ruff/Pyright/policy/九个import-linter约束均exit0。尚无生产GraphSession、固定注册worker图、当前环境实测准入或完整M1；准确新head仍须独审，未跑完整门禁/wheels/CI。
