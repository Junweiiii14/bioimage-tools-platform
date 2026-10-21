# T072 最终检查与主线集成

产品最终独审44a342ede883f05365437779b97bf751e74eab0b Accepted，后继46a4392983bcd37cc033f9f364c9d019f7073e1b仅独审证据/任务/交接。PR32精确匹配head经全部四必需检查正常合并main0630604f607415311f405efa99aff46461b46778，未使用admin/bypass；构建前核apps/tools/packages/tooling/pyproject/lock与44a整树相同且工作区干净。

- Linux quality39536779177/job119015213189：1013passed424.44s，debugger退出0，隔离wheel、真实OCR及全check0。
- Windows同run/job119015213396：1013passed513.16s，Observed child exit=0/u32=0，隔离wheel/全check0。
- rules-context39536779555、desktop-environment119015213536：SUCCESS。native-case为可选诊断SKIPPED，不冒充已跑。
- 本机Windows/CPython3.12.14从44a启动完整dev.py check --all，1013passed880.70s，随后全部wheel/桌面异步关闭/PP-OCRv6/static worker/PNG检查与外层退出0。运行后仅合入相同产品树及文档，不据此声称不同产品覆盖。

首check-v1保留1007passed/1failed856.36s：新增E2E在表可见、数据快照未到时读占位1行，修正为等待完整10行后仍断言10。没有降低数值/容差、增加skip/xfail或改门禁。早期GPU context lost/停滞轮次、原有手工坐标/native UNKNOWN继续保留；后继通过不证明这些历史根因全部已明。

PR首次2726673规则门禁失败为module-map更新后旧receipt；真实重载读取后bc0a90e修哈希，后继规则SUCCESS。没有删除回执或改检查状态。产品PR：[32](https://github.com/Junweiiii14/bioimage-tools-platform/pull/32)。精确原日志随本机交付验证目录保留，不提交安装包或私图。
