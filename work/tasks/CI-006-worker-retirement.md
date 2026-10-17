# CI-006：后台QObject退休与GUI线程销毁

- 状态：in_progress；T043继续授权，修复真实全量挂起，不改测试时限/断言/skip或依赖。
- 来源79f9070正式check --all在test_repeated_window_close_and_collection挂起，保留Python/native栈后仅停止自有pytest树，完整check实际exit1，未运行后续wheel。
- 真实三线程：main等待Qt connect mutex，worker23732在QObject析构→Sbk_GetPyOverride→PyGILState_Ensure，storage20144在queued reply PyObjectWrapper复制等待GIL。结合固定6.12源码与同版本有界正负对照支持Qt对象锁/GIL反转；远端其他超时不能未经证据一概归因。
- 先修AsyncStorage/WBBackground排空后显式退休：worker所属线程移回owner线程，再退出QThread；GUI非阻塞确认线程退出，再销毁worker，销毁后closed。保留FIFO/错误/取消/原图和旧结果。
- 回归核验真实C++析构线程、线程结束、closed后worker失效，保留原20次重复关闭和全部门禁。绑定提交独审后更新阶段清单，完整通过再同步；main不变。

- 同模式排查扩至进程解码器/项目恢复，共4后台；36项定向exit0，完整668/508.54秒及全部wheel实际exit0，绑定a811ccfd独审18项0；远端复验待完成，原测试和时限保持。

- 本地修复验收已完成；远端新候选尚未执行，整体T043继续in_progress。
