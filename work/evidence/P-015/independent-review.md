# P015 独立审查

只读审查者：`/root/p011_independent_review`；用户已明确授权。作者自验不替代以下结论。

## 首轮：b1e348ac821d2b1a77ce94878cc98d8eb4461ff6

审查者独立执行工具16项测试，16 passed/exit0；只读核验9份已提交标签与P014逐像素、逐ID一致，原始输入/标签/出处摘要、模型摘要、核数和原坐标一致。没有运行额外模型或GUI全套。

发现两项已复现问题，首轮**未通过**：

1. P1：Pillow把SampleFormat=2的int8 TIFF读作mode=L；入口没有检查339标签，把负数静默解释为uint8。要求仅接受unsigned（SampleFormat=1或缺省）。
2. P2：worker把异常截1500字符，但ExecutionEvent.reason上限1024；1200字符RuntimeError导致构造failure再次异常，只有hello/accepted，没有终态原因。

作者修复：新增SampleFormat校验及真实int8 TIFF拒绝回归；异常截断改为1024，新增实际子进程长异常回归验证hello/accepted/failure、退出2和原因。未调容差、skip、xfail或降低检查。新增用例总计20项通过；严格类型0 errors/3个既有研究源码缺失warnings。因产品改变，最终绑定提交复审仍待执行。

科学/训练重叠/实验室/学生/16bit、完整门禁与主线集成不由本次只读检查代替。

## 增量复审：9c9f81ed09466afdb86a8753192648a94d7111a9

独立审查者结论：通过，两项问题关闭，无新增发现。独立运行四项定向回归4 passed/1.34s/exit0，包含signed TIFF拒绝、长异常终态、正常原值读取、打开stdin时native导入。只读复核第三轮9份已提交结果，每像素/实例ID、资产和原始输入摘要及核数匹配P014；没有重跑模型或GUI全套，没有修改文件。

本记录提交只更新证据/任务/交接，不修改被审产品、参数、测试或门禁，因此该产品审查继续适用。最终全仓及CI收据仍待完成。

## 显式虚拟环境入口补审

主代理发现并请求独立检查Linux venv入口提前resolve的疑点。审查者确认P2：Linux解释器符号链接被解析成基础Python会绕开用户指定虚拟环境；依据Python3.12官方venv文档，当前Windows不冒充Linux实测。最小修复保留absolute入口、is_file校验；新增实际子进程sys.prefix回归，并加强实际宿主失败测试要求研究依赖错误，不能用找不到nuclei模块冒充预期失败。21项新增测试本机通过；Linux实际路径回归等待最终CI。数值/模型/输入/输出方法代码未变，第三轮Windows14场景证据继续适用。

### 最终产品增量结论：a490d2ed293953d6e0560b9e7a426d113e711d56

独立复审通过，无新增问题。独立运行tests/test_nuclei_host.py：3 passed/1.93s/exit0。解释器absolute入口保留venv及is_file验证，sys.prefix实际子进程和研究依赖错误断言有效。未修改文件或重跑模型；先前方法/数值审查继续适用，Linux实际符号链接路径留待最终CI。本结论之后的收据提交仅文档/交接，不改被审产品、测试或门禁。
