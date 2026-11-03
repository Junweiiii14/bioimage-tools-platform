# PR55首轮CI：通用存储的传递依赖

准确5e69b2f，quality41494573552。Windows125446028782、Linux125446028523均在import-linter阶段exit1；pytest及wheel尚未运行，不能把这轮称全量回归通过。规则和desktop-environment成功，不代替foundation。

实际路径：storage → workflow_authoring_store → wb_tool.api → NumPy，违反既有host-storage-purity。此前作者类型/定向测试及非作者静态审查未识别这条完整传递路径；单独安装默认端口未执行编排也不证明静态依赖契约通过。

修复将具体编排处理器装配移到WorkflowAuthoringSession：在AsyncStorage线程启动前固定execute_authoring_store；通用worker仅调用装配的typed处理器，不导入具体WB。命令仍只有固定操作和不可变bytes，不接受外部callable、模块名或路径。使用原worker、原Workspace、原队列/排空和错误边界，未新建SQLite所有者。未配置编排的普通端口明确拒绝该操作。

没有修改.importlinter、依赖锁、门禁、数值或schema。修复后实际import-linter为9 kept/0 broken；原store/session、Web重开和测量等待器10passed38.59s，类型0，目标Ruff/format通过。追加已有FIFO用例验证未配置拒绝；7run真实编排用例记录处理器线程，须始终同一存储线程且不是GUI线程。最终结果和准确提交独审另记。

742c产品装配独立验证2passed15.32s，作者2passed15.73s，9导入契约独立exit0。独审另指出新归档的CI原始文本有真实行尾空格，使742c全范围diff检查exit1。现改为无损ci-5e69b2f-failed.log.gz，mtime=0；ci-log-bytes.json记录原文/压缩字节数与SHA，解压逐字节等于原件，旧742c历史仍保留原文。未trim日志、覆盖原件或扩大whitespace忽略。此修正只涉及证据，不需要重跑产品测试。

前一64c全部隔离wheel通过继续保留其准确源码范围；本次装配修改后的安装验证交最终必需CI完成，不把旧wheel结果改署新提交，不在本机再次全量回归。纯装配改动未改变预览/节点/控制逻辑，原冻结性能仍明确绑定26f/64c，不冒充新提交性能实测。
