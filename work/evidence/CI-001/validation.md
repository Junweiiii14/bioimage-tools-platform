# CI-001 验证

远端阶段2–7 Linux foundation在进入pytest前报process_tree.py:154的3项严格类型错误；最终阶段同源。Windows不能暴露这个静态分支问题。本地对修改前文件指定Pyright Linux目标复现相同3错误，退出1。

修复仅close条件补上`os.name == "nt"`，与构造器仅Windows分配job/_kernel的既有不变量一致；不改变实际POSIX/Windows生命周期，不加ignore，不改门禁或预期。

最初借用活动树解释器运行旧阶段测试，导入了活动产品，结果不能验证本阶段；再用PYTHONPATH指向旧阶段但-I worker仍来自新活动环境，造成7通过1协议漂移失败。这两次均不是有效本阶段通过证据，保留诊断。

随后在阶段树单独按其原uv.lock执行uv sync --locked --all-groups，使用自身已安装包、解释器与-I worker重新验证；没有修改锁文件或活动产品环境。最终结果另随绑定提交记录。
阶段独立原锁环境：tests/test_process_runner.py 8passed/10.89s/exit0，包含真实worker、PID许可、取消与进程树清理。Pyright Linux和Windows目标均0errors/exit0。


CI001之后最终产品树fa9c5f2正式完整check实际exit0：657passed/451.28s，全部隔离wheel含真实OCR完成。日志.local/t043/check-final-ci001.log；文档后继与此产品内容相同。
只读独审70d9b66..2b9f643无确定缺陷：Windows成功/构造失败清理与幂等关闭保持，POSIX不执行Windows操作；审查者本次未重跑8测试，不混称作者测试为独立执行。
