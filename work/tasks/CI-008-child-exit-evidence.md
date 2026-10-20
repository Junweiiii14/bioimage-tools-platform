# CI-008：测试结束后的真实子进程退出码

- 状态：complete（退出诊断）；T043既有全门禁失败诊断授权。
- bbf3cc5 Windows job117368899146真实668passed/508.43秒，随后作业exit1，未执行wheel；没有timeout/native栈，不能按测试数宣告通过，也不能未看实际子退出码就称Qt崩溃。
- 父观察器在子进程退出后输出有符号十进制及32位十六进制返回码，再原样返回。既有非零退出回归同时断言输出准确，不改时限/断言答案/依赖或产品。
- 合并已独审CI007平台guard到同一个后继CI候选，精确清单及独审后正常推送；保留此前Linux与Windows失败，main不变。
- 核对固定pytest插件：unconfigure先禁用faulthandler，只在启动时已启用时才恢复。CI显式PYTHONFAULTHANDLER=1，使测试结束后的异常仍有机会输出栈；验证启动/pytest结束仍启用，不改变退出码或时限。

- 1bb1d9d真实日志取得child exit1/u32=1及1failed667passed，定位本轮为create执行6.125秒的前置等待超时，转CI009处理；旧bbf的668passed后exit1仍UNKNOWN，不能追溯认定同因。
