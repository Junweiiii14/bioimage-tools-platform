# T072 最终检查与主线集成

产品最终独审44a342ede883f05365437779b97bf751e74eab0b Accepted，后继46a4392983bcd37cc033f9f364c9d019f7073e1b仅独审证据/任务/交接。PR32精确匹配head经全部四必需检查正常合并main0630604f607415311f405efa99aff46461b46778，未使用admin/bypass；构建前核apps/tools/packages/tooling/pyproject/lock与44a整树相同且工作区干净。

- Linux quality39536779177/job119015213189：1013passed424.44s，debugger退出0，隔离wheel、真实OCR及全check0。
- Windows同run/job119015213396：1013passed513.16s，Observed child exit=0/u32=0，隔离wheel/全check0。
- rules-context39536779555、desktop-environment119015213536：SUCCESS。native-case为可选诊断SKIPPED，不冒充已跑。
- 本机Windows/CPython3.12.14从44a启动完整dev.py check --all，1013passed880.70s，随后全部wheel/桌面异步关闭/PP-OCRv6/static worker/PNG检查与外层退出0。运行后仅合入相同产品树及文档，不据此声称不同产品覆盖。

首check-v1保留1007passed/1failed856.36s：新增E2E在表可见、数据快照未到时读占位1行，修正为等待完整10行后仍断言10。没有降低数值/容差、增加skip/xfail或改门禁。早期GPU context lost/停滞轮次、原有手工坐标/native UNKNOWN继续保留；后继通过不证明这些历史根因全部已明。

PR首次2726673规则门禁失败为module-map更新后旧receipt；真实重载读取后bc0a90e修哈希，后继规则SUCCESS。没有删除回执或改检查状态。产品PR：[32](https://github.com/Junweiiii14/bioimage-tools-platform/pull/32)。精确原日志随本机交付验证目录保留，不提交安装包或私图。

## 收尾 PR33 的结果表同步修正

收尾文档头be38a0f的quality39539807356两平台均失败于既有双Fig人工暂停/继续E2E：Linux/job119024721386为1012passed/1failed328.68s，Windows/job119024721030为1012passed/1failed625.64s、原child1。两者在`tests/test_instrument_intake_desktop.py:1463`读到可见表格的1行占位，预期仍为9行；尚未运行后续wheel，因此本轮不能计为完整通过。原始两日志保留在`.local/t072/ci-closeout-{linux,windows}-first.log`。

该测试只等待mode切到results，未等待异步快照到达。仅把等待条件补为results模式、表格可见且完整9行到齐，仍保留原9行/尺寸/可见性/阶段屏障/重开/原图保持断言、原10秒截止；未变预期/容差/skip/xfail或产品代码。编辑前真实重载T072回执增tests范围。Windows/CPython3.12.14、offscreen/disable-gpu定向复跑该E2E与可靠定位无确认E2E，2passed17.54s、实际退出0；Ruff检查/格式/diff0。非作者绑定a65f2d79e7aab2d06f99adfc532302ec7834d072 Accepted、独立两相关2passed15.66s/退出0。后继仅补结论记录；[PR33](https://github.com/Junweiiii14/bioimage-tools-platform/pull/33)最终head的四必需检查与merge以服务器记录为准，未全部SUCCESS不得合并，不以产品旧头通过代替。原失败不由定向成功抹去。冻结main0630604安装器及其已验产品字节不变。
