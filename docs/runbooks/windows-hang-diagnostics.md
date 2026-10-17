# Windows挂起诊断

正常门禁仍为 `uv run --locked --no-sync python dev.py check --all`，CI的15分钟上限、所有用例、断言和退出码保持。Windows CI额外设置 `BIOIMAGE_NATIVE_STACKS=1`；本地需要时可显式设置同一环境变量，结束后移除。Linux使用原执行路径。

只有pytest子进程60秒没有完整输出行才触发一次native观察。父进程逐行转发输出、返回原测试退出码；诊断失败仅输出失败类别，不改检查结果。开关从测试子环境移除，避免递归启动观察器。只追踪该父进程创建的Python树（Windows venv启动器与实际解释器），不扫描用户工作台。

原生观察限定Windows AMD64，最多4个进程、各32线程/24帧。线程仅在GetThreadContext期间短暂停止，在finally恢复后才使用DbgHelp展开；未生成内存dump或输出内存字节、环境、路径、科研图像。仅模块basename、函数、偏移进入检查日志。DbgHelp调用串行且不使用外部符号路径；不保证可用私有符号、完整或原子栈，活动线程可能变化。没有添加终止测试的计时器，原15分钟CI负责最终超时。

先按日志节点判断是执行、收回执、关闭或native调用；结合Python/native栈匹配具体版本源码。诊断会改变调度，单次通过、观察到锁等待或人工构造复现均不自动等同产品根因。保留失败与UNKNOWN；不得以提高上限、skip、改成功状态或拆开全量代替修复。CI005证据记载既有Python栈和最小实验。
