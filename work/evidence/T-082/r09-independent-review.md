# R09 工具独立复核

**Accepted**，绑定`8d26a9c4db9a797ccb3708ace94884443c03159c`，基线`34824e1`，仅认可工具可进入真实测量。原预审误完成反例已修。临时Qt slot转交原request→publish→snapshot/JSON，随机nonce只附加于该请求；实际render成功才记序号/nonce，回执/状态/render同nonce且序号增长，双rAF后继续一致，才能计成功样本。

非作者独立运行 **16 passed/2.04s/exit0**；额外只读探针验证非trusted/重叠点击零样本、KeyboardInterrupt传播且snapshot恢复。受审4文件与准确提交一致，diff check为0。按生产同步处理器顺序核查，缺handler、仅替换state、render或后续边界异常、旧/缺nonce、重复及绘制前覆盖不能伪造成功。

未修改产品或门禁；预设调查预算、30次nearest-rank、49152 pending项、合成缩略图及PSAPI前后采样限制保留。超时/边界/关闭失败会在成功报告写出前中止。**没有运行GUI或性能测量**；实际Qt派发、点击/绘制机会及正常退出仍待真实执行，驱动失败不能记录为产品性能通过或超线。
