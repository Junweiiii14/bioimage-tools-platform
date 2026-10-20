# 采集组离线测试版 T069

本机工程测试候选，构建源码冻结在 main `60808671cc2a3e9bb255bce85d546a18416c64a5`。完整计划见[采集组计划](wb-grouped-intake-plan.md)，状态与原始失败边界见[T069](../work/tasks/T-069-grouped-intake-offline.md)及其[证据](../work/evidence/T-069/validation.md)。后续收尾仅修改记录，不重新生成这一已验证安装包。

## 本地交付

- 文件夹：`%USERPROFILE%\Desktop\BioImage-WB-采集组测试版-T069`。
- 安装包：`BioImage-WB-x64-T069-Test-60808671cc2a-Setup.exe`，361,584,364 字节。
- SHA256：`99c0ec5540161c27a0bcea990e5286aebadeea65b3372239fab1ed4a9cbb6d97`。
- 随附 `build-manifest.json`、`SHA256SUMS.txt`、安装载荷摘要清单、安装说明和验证报告；安装包与私图均不提交 Git。
- 当前用户安装到 `%LOCALAPPDATA%\Programs\BioImage WB 采集组测试版`；桌面/开始菜单有独立入口。

AppId `BioImageTools.WB.GroupedIntakeTest`、channel `wb-grouped-intake-test`、设置 `BioImageTools/GroupedIntakeTest` 与旧发行分开。旧安装、原图、项目、历史结果及旧工作树保持。

## 已执行验证

| 范围 | 实际证据 |
|---|---|
| 产品集成 | PR28 head `93d1ef0` 四必需检查成功，2026-10-20T13:52:48Z精确正常合 main `6080867` |
| Windows/Linux | 956项分别520.17s/406.82s，child0/debugger0，全部隔离wheel及真实OCR完成；main随后quality也成功 |
| 原生取证 | 独立手动完整pytest为956项/382.32s、debugger0、无deadline；没有复现旧关闭挂起，不表示根因已明 |
| 真实三目录 | 95 TIFF/76内容、19三图组、74槽；一次4A修正只重算两行，新输出并保存重开；独审38份裁剪读取与原坐标切片一致，旧218/新219成员摘要相符 |
| 构建/安装 | 干净冻结提交、私有CPython与锁定四wheel；编译/安装器/当前用户安装实际均0，载荷7,749文件逐字节摘要相同 |
| 安装态分组 | 17项、两个真实worker、单次真实快捷键/精确设置重载、原值裁剪/新输出/重开/资源关闭；父OS退出0、无所属残留/开发模块 |
| 独立灰度/OCR | 安装态实际通过，父OS退出0、无所属残留/开发模块 |
| 随包自检 | Windows PowerShell5.1.26100.9711运行安装目录selfcheck.ps1，两流程实际0 |
| 交付独审 | 非作者绑定冻结main6080867只读接受，无新增可证实P0–P2；安装器/32摘要成员/7,749载荷文件/四wheel及旧原文件与工作树已核对，见[独审记录](../work/evidence/T-069/independent-review.md) |

首个父采集器漏持有进程句柄，拿到的原退出码为null，因此采集器实际1；不把该次报告passed改判为进程成功。保留旧报告后先验证0/17控制，再运行新报告并取得实际0。详见T069安装证据。

## 继续保留的边界

本机为Win11；干净Win10、物理按钮/多DPI和独立科学真值/留出尚未验。真实图是已见、参考辅助开发回归，不提供自动准确率、生物配对或科学泛化结论。原Windows诊断具体触发、Linux历史关闭挂起根因仍UNKNOWN，旧失败不会被后继成功覆盖。这是本地候选，未创建正式GitHub Release或自动升级依赖。
