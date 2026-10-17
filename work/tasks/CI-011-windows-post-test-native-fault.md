# CI-011：Windows 测试结束后的原生异常定位

- 状态：in_progress；延续用户完整门禁修复授权。
- 基线40f0258。真实Windows job117383522334在669passed/433.12秒后先Aborted再access violation，真实child3221225477/u32=0xc0000005，完整check失败、wheel未跑。Linux同HEAD GDB真实控制、669/158.32秒及全部wheel/最终check成功；WSL同锁定环境669/398.40秒正常退出，但只是pytest观察，不是完整dev check。
- 一个正常关闭最小实验page/profile在app.exec返回时均已释放，退出0；不支持“必然残留profile”假设。Linux0d测试后SIGSEGV与本次Windows异常可能相关但未证明。
- 先核验Windows原生观察工具和主来源，固定版本、独立差异审查；只捕受控测试树，保留原始异常与退出，不生成/上传内存转储、私有原图或凭据，不改系统全局调试器注册/安全策略。没有证据不猜测性清理或升级Qt。
- 原15分钟、全部断言/skip、公式/schema/依赖锁不变。修复须真实反例、独审和完整门禁；原图/旧结果/原未提交文件与main保持。
