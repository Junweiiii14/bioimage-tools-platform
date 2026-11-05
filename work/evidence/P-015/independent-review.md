# P015 独立审查

只读审查者：`/root/p011_independent_review`；用户已明确授权。作者自验不替代以下结论。

## 首轮：b1e348ac821d2b1a77ce94878cc98d8eb4461ff6

审查者独立执行工具16项测试，16 passed/exit0；只读核验9份已提交标签与P014逐像素、逐ID一致，原始输入/标签/出处摘要、模型摘要、核数和原坐标一致。没有运行额外模型或GUI全套。

发现两项已复现问题，首轮**未通过**：

1. P1：Pillow把SampleFormat=2的int8 TIFF读作mode=L；入口没有检查339标签，把负数静默解释为uint8。要求仅接受unsigned（SampleFormat=1或缺省）。
2. P2：worker把异常截1500字符，但ExecutionEvent.reason上限1024；1200字符RuntimeError导致构造failure再次异常，只有hello/accepted，没有终态原因。

作者修复：新增SampleFormat校验及真实int8 TIFF拒绝回归；异常截断改为1024，新增实际子进程长异常回归验证hello/accepted/failure、退出2和原因。未调容差、skip、xfail或降低检查。新增用例总计20项通过；严格类型0 errors/3个既有研究源码缺失warnings。因产品改变，最终绑定提交复审仍待执行。

科学/训练重叠/实验室/学生/16bit、完整门禁与主线集成不由本次只读检查代替。
