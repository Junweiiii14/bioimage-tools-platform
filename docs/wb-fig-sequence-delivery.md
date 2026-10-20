# Fig 顺序自动化离线测试版 T071

本机工程测试候选，构建源码冻结在 main `710bb85de99e88a970f4d0f5613ca554b705ecf7`。用户批准的完整方案见[Fig 顺序计划](wb-fig-sequence-automation-plan.md)，当前状态与实际失败见[T071](../work/tasks/T-071-fig-sequence-automation.md)及其[证据](../work/evidence/T-071/validation.md)。后续文档提交不改变这一已验证二进制的来源。

## 使用与交付

在上方新增 Fig，分别填写 Fig 名称、一次填写本 Fig 的 N、每行一个蛋白名。程序按完整采集组顺序跨 Fig 连续分配；逐组手选裁剪原图后，一个“开始自动处理”入口保存并启动。整批全部裁剪→全部拼图→全部原像素定量→统一结果，按真实提交自动切页；需人工处理时暂停，修正后一个入口继续。主动浏览保留页面和草稿，重开不自动续跑。

本轮已明确的真实目录仅19个仪器采集组占编号，28组参考结果保留单列、不占顺序。旧对应和历史执行不静默重排。

- 桌面交付：`%USERPROFILE%\Desktop\BioImage-WB-Fig顺序自动化测试版-T071`。
- 安装包：`BioImage-WB-x64-T071-Test-710bb85de99e-Setup.exe`，361,622,169 字节。
- SHA256：`760b3ee0d7e9c3d22f8f470185791f3c11b26f051babce2c3d4d94f57df75c94`。
- 随附 `build-manifest.json`、`SHA256SUMS.txt`、7,751文件的安装载荷摘要清单、说明与验证报告；安装包/私图不提交Git。
- 当前用户安装：`%LOCALAPPDATA%\Programs\BioImage WB Fig 顺序自动化测试版`；桌面入口“BioImage WB（Fig 顺序自动化测试版）”。

独立AppId `BioImageTools.WB.FigSequenceTest`、channel `wb-fig-sequence-test`、设置命名空间 `FigSequenceTest`。旧[T069交付](wb-grouped-intake-delivery.md)、原图/项目/历史结果、旧树未提交改动均保持。

## 实际验证

| 范围 | 证据 |
|---|---|
| 独审与集成 | 最终5f2090a诊断增量Accepted；PR30四必需检查成功，精确正常合main710bb85；非作者核两者整树相同 |
| 本机完整 | a952启动源979/825.65s、原child0/u32=0、全部wheel/OCR及check0；不冒充覆盖后续5f诊断增量 |
| 最终两平台 | Windows979/615.77s、child0/u32=0；Linux979/332.14s、debugger0；全部四wheel、真实OCR/PNG/static worker及完整check0 |
| 发货页面 | 两Fig顶部填写/选源/一次启动、两次人工修正继续、真实阶段屏障、两个worker、9槽、原值/输出/安全重开和所属关闭；源码与安装态分别验证 |
| 真实三目录 | 当前85TIFF/76内容，19执行组/28参考组；19回归Fig/74槽，20次真实运行含一次局部修订；非作者只读复核38裁剪逐原图ROI数组/位深及新旧输出摘要 |
| 构建与安装 | 干净冻结main、私有CPython3.12.14与四锁定wheel、既有GCC/Inno；编译/安装器/当前用户安装实际0；7,751载荷文件构建与安装摘要逐项一致 |
| 安装态三流程 | 新Fig顺序、旧采集组兼容、独立灰度/OCR报告passed/errors空；各父OS实际0，无所属残留或开发模块，私有runtime/isolated路径核对 |
| 随包自检 | Windows PowerShell5.1.26100.9711执行安装目录selfcheck.ps1，三份新报告passed、外层0、无超时/残留/观察错误 |
| 交付独审 | 非作者绑定冻结main及安装器SHA只读Accepted；41校验成员/37证据副本、302源码文件/4wheel及7751载荷独立核对，无新增可证实P0–P2 |
| 原成果保护 | 旧T069安装器/两个manifest的3文件SHA、旧树10份dirty文件SHA、HEAD与dirty列表均匹配构建前记录 |

交付最后的非作者审计记录见[独审](../work/evidence/T-071/independent-review.md)。新目录里的manifest记录精确源、锁文件、四wheel及安装器摘要；这些本机文件才是产物清单，不把GitHub上的文档HEAD当二进制来源。

首次随包外层观察器因无BOM的UTF8脚本被PS5.1按ANSI解释中文路径而未进入产品，自身退出-196608/无三流程报告，按失败保留在验证目录的first-failure文件。只给本地外层脚本补BOM后重新执行成功，未修改产品或安装包。其他实际初败、Windows旧手工坐标偏差及关闭native未知见[CI记录](../work/evidence/T-071/final-ci.md)，不因后继成功删除。

本机为Win11。干净Win10、物理按钮/多DPI、独立科学真值/留出尚未验；当前真实图为已见参考辅助开发回归，不主张生物配对或科学准确率。历史native UNKNOWN继续保留；本轮没有正式Release或依赖升级。
