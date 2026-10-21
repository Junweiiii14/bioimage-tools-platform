# 自动流程修复离线测试版 T072

本机工程测试候选，构建冻结main `0630604f607415311f405efa99aff46461b46778`；产品独审44a342e Accepted，PR32四必需检查后正常集成。后续文档收尾不改变该二进制来源。完整方案在[T072任务](../work/tasks/T-072-automatic-flow-repair.md)，实现契约见[自动裁图v2](contracts/wb-intake-automatic-crop-v2.md)。

## 使用

顶部新增Fig，填写Fig名、一次N及每行蛋白，跨Fig连续分配采集组，手选每组原图后启动。可靠完整几何自动保存并继续，全部裁剪→全部拼图→全部原像素定量→统一结果；多目标/N冲突/方向不足才暂停，人工修正后一次继续。小角度显示纠偏可预览、调整或恢复，原图TIFF/定量像素不变。

灰度页显示当前Fig、蛋白和原坐标测量区域，统一结果表含状态并导出Excel/CSV。普通有效结果计算说明折叠，质量/失败直接显示。中央预览先前误复用128像素缩略图，现按SHA和实际预览尺寸替换；700×300原图自然尺寸及安装态同检。既有最长边2048显示预算保留，不把8位显示数组用于定量。

19个执行采集组编号，28组参考保留单列。现有19组选图的已见参照辅助只读评估中4组满足保守自动条件，其余需明确范围/方向，不作为科学准确率或留出结论。旧人工@1和无框native版式保持；加框仅影响所属Fig，不改其他完成Fig摘要、分析或历史。

## 构建与安装

- 安装包：BioImage-WB-x64-T072-Test-0630604f6074-Setup.exe，361,660,931字节。
- SHA256：daa3633ecac6f41e027c422f203c933ae90aca07ee03f47a135d38484f8397a2。
- 私有CPython3.12.14、四锁定wheel、既有GCC15.2.0/Inno6.7.3，无依赖升级。干净main构建及安装器实际0；当前用户安装69.395s/OS0。
- 独立AppId BioImageTools.WB.AutomaticFlowTest、channel wb-automatic-flow-test、设置AutomaticFlowTest。安装目录 `%LOCALAPPDATA%\Programs\BioImage WB 自动流程修复测试版`；桌面入口“BioImage WB（自动流程修复测试版）”。旧T071及其他测试版保持。

两平台各1013、独立51核心与本机全1013/wheel/OCR检查通过，详[最终CI](../work/evidence/T-072/final-ci.md)。安装态四流程实际父OS0/无开发模块或所属残留：自动17项19.094s，原顺序13项8.765s，分组17项10.047s，灰度/OCR7项8.656s。17项自动流程覆盖信号±3°与guide±8°独立、无需裁图确认、700×300原图预览、灰度图片/区域、9表格记录、完整输出/原值保持/重开/关闭。计时仅本机证据。

桌面交付目录 `%USERPROFILE%\Desktop\BioImage-WB-自动流程修复测试版-T072`，含安装包、manifest、逐载荷摘要、使用说明、SHA256SUMS及递归验证证据。PS5.1随包新轮四报告passed、外层56.548s/OS0、无timeout/error/所属残留，观察器只读不清理。7,753构建载荷文件与安装逐项SHA一致。最终非作者产物审计Accepted，绑定冻结main与安装器SHA，核71校验成员、7753双端载荷、309源码子集和四wheel178包源文件。详[独审](../work/evidence/T-072/independent-review.md)。

## 原失败与边界

首随包四个产品报告passed/父0，但外层本地观察器误收一个旧OneDrive.Sync.Service进程（父PID复用）并在清理时停止，故外层失败保留；不记成功。已校验微软签名，重新启动同一后台exe并只读确认运行，不声称同步状态全面验收。修正观察器为CIM/实际出生身份及父子时间校验，完全移除自动终止，只观察timeout/残留并记失败；非作者绑定helper SHA独审Accepted，11纯控制0。该helper不在产品安装包内，产品字节未改。首失败报告/原helper/恢复记录随交付保留；轮询不保证捕获每个短命后代。依据[Win32_Process](https://learn.microsoft.com/windows/win32/cimwin32prov/win32-process)。

自动诊断的limitations字段沿用旧constant-images/explicit-ROI描述；本模式实际使用合成倾斜条带和伙伴图，以17个命名检查与报告模式为准，交付evidence-notes明示这处陈旧文字，未默改冻结二进制。

本机Win11；干净Win10、物理DPI/按钮、独立科学真值/留出未验。现有原图、历史结果、旧工作树27/10份未提交改动保持，旧安装不升级/删除。无正式Release或新工具扩展。
