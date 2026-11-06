# P016 单图核分割研究流程交付

最终验收：PR67已合入main 6bd4680530dc4697f8d394a96fd288723222ddb8，与候选16d32b12f3980cf2dcaeb3ec9d145488378c6dcd文件树diff退出0。quality42157212799成功：Windows1737 passed/10 warnings/1410.11s；Linux1733 passed/4既有Windows专用skip/10 warnings/951.94s；两平台随后wheel/check --all完整通过。rules42157213226、desktop-environment通过。只读独审绑定候选通过。2026-11-06已成功向上游01a19bfd-f3ab-7502-86da-9f61953d1c8a(local)发送正式入口/截图/证据/CI/独审/PRmain/边界和下一建议，要求自动接续。观察进程87597已exit0。

## 使用与演示

当前源码工作台首页 → 单图核分割 → 运行设置（首次由维护者准备环境/模型后选择路径）→ 选择原图 → 开始分析 → 原图/实例轮廓/缩放与已保存核数 → 导出表、图与标签。关闭后打开已保存项目目录，读取同一正式结果。完整5步导航及公开46核练习见[使用指南](../../../docs/runbooks/nuclei-single-image.md)。

最终截图为本机 `.local/p016-final-1440.png` 和 `.local/p016-final-960.png`；可从当前源码重开下面已保存项目演示，不重跑模型。旧安装未更新。

- 项目：`C:/Users/70236/Documents/BioImage/Projects/Nuclei-2e1ef41119f6`
- Run：`e1ac56de87bd4842bab553b63a9ca027`，46核，标签与P014逐像素/ID一致。
- 来源：公开已见 Ganglioneuroblastoma_10.tif，SHA256 `77f7b965733145a6edae173090ba1b9081266c708a3f141a12f8b281af640074`。
- 导出：`C:/Users/70236/ResearchVault/Codex-Workbench/p016-research/核分割结果-72c9e7896ad8`，CSV、显示PNG、原整数labels.npy和provenance齐备。

## 验证

[首条实际GUI](first-gui-run.json)与[真实模型风险回归](gui-regression.json)证明正常46核、真零核0、缺模型失败、不支持输入拒绝、取消与历史保护；原图SHA不变、导出字节一致、重开同run且没有新增推理。后者使用替代原生选择器的真实Qt控制器，不能冒充人工学生操作。单次心跳观察最大约63ms，不是跨机器性能承诺。

[审查与验证](review-and-validation.md)记录完整命令、异常修复与测试差异。16d32b1准确提交只读独审通过，SQLite异常P2已关闭；没有其他可复现阻断问题。c08979d本地全门禁1735通过并完成全部wheel检查，最终修改定向验证通过。最终CI、主线集成与正式回传均完成，见[逐项审计](objective-audit.md)。

## 保留边界与下一最小建议

仅固定P015单图unsigned uint8/BlackIsZero/TopLeft单通道单页TIFF；没有16bit、强度、全细胞、批处理或人工改核。显示图只用于显示，原整数标签与出处保留。默认没有TensorFlow/StarDist，首次环境由维护者准备，不自动下载。没有替换安装器或旧GUI。

这是开发者在已见公开图上的工程验收，不是学生或科学准入；训练数据重叠、患者独立性、真实实验室适用性、四主题/高DPI、独立目标机、Linux真实模型等仍未验证。WB配对/独立重复/背景方法未知亦未变。

下一项建议：由上游按现有计划派发“首次准备与打开结果的可操作走查”，优先把现有准备指南变成界内可发现说明，并验证一个维护者准备后普通用户的完整练习；不扩大算法、16bit、安装发布或科学结论。编号/范围由上游决定，当前任务结束后自动接续，不等待用户催促。
