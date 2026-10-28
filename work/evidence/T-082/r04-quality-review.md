# R04 门禁独立复核

非作者审查 `/root/independent_review`：**Accepted**，准确提交 `918598c0385f91a7669290f07d3ee658100915a5`，基线 `bd794747c0002ce2ba7f0f998f167f755f2b053a`。

独立运行 `npm run check:web` 和实际 pre-commit web-quality hook 通过。受控探针确认缺工具、版本错误、子检查非零都会失败，dev.py 传播失败并停止后续步骤。79 个锁定包均为开发依赖、固定版本/官方 registry/SHA512；setup-node 固定 SHA 与官方 v7 引用一致。

AST复核 advanced.js 仅提取原 payload 构造，字段/顺序/value对象身份/加载顺序保持；intake_groups.js 仅格式变化。既有 Python 门禁保留，差异空白检查通过。未发现阻断。

类型覆盖限于真实请求生成器及共享身份契约；非整个UI。未运行远端CI、最终完整门禁或重复作者Qt UI；本次Accepted不替代这些验证。
