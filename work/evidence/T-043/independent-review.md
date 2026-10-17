# T-043：提交绑定只读独立复核

审查者为已获用户授权的readonly_review代理，未修改代码。作者自验另记。

1. 产品入口修复：`b4e85ea..2e5021d`，无确定性阻断问题；独立执行入口/环境14项测试，退出0。核验正常CLI进入当前网页工作台、明确legacy入口、关闭拒绝保持当前窗口、测试环境离屏和worker早路由。该审查不证明原生间歇挂起根因已修复。
2. 治理前置：`221a2df..0b786cb`，无确定性阻断问题；独立6项拒绝路径退出0。当前回执仍检查完整范围、规则、任务和精确基线；清单完整、祖先、历史规则及字节一致；普通单任务唯一回执约束保留。可追溯不证明当时阅读理解。
3. 阶段整理：以下HEAD逐阶段产品快照一致、治理三文件与已审0b786cb一致、基线链连续、显式清单全部校验退出0。T007/T026真实重载且旧blob可从原祖先读取。main/origin/main仍221a2df。此结论只覆盖整理完整性，不替代历史产品审查/CI/集成授权。

| 阶段 | 审查绑定HEAD |
|---|---|
| P0 | 34a5cc1920ea38494177f2dbedce84d0503407bf |
| WB核心 | 70d9b66ebeb9c8e79440086863b3ac9438979dee |
| Fig/OCR | c53706d8321263cf5ad1aeaad92470dc2f710948 |
| 恢复 | 948d7684e777edcf02ceb4652a959fc73e2604eb |
| 自动化 | 79a3c5fdd4dfaa9b6dd12ef17dd31583feb745f9 |
| 工作台 | d83e1bd2dbeaea2213a99c78c6168081afdb6ef0 |
| 灰度监督 | 3293cedb1dfa6c5b30e4f6ad5ec7c187c3c7e384 |
| 原图修复 | 417fefadd21455d1260dc9cb537a40f63a29cc15 |

后续阶段8若追加当前文档/回执，须重新核验受影响清单与规则；产品代码审查仍仅绑定上述产品提交。


## 最终平台修复与阶段复核

70d9b66..2b9f643的源码独审无确定问题；本次未由审查者重跑真实进程测试。最新8阶段逐一独立规则检查exit0，前置链连续，阶段1无产品变更、阶段2–8唯一产品差异逐字节等于已审单行guard。main/origin/main仍221a2df。

| 阶段 | PR | 整理独审绑定HEAD |
|---|---|---|
| 1 P0 环境与便携探针 | [#3](https://github.com/Junweiiii14/bioimage-tools-platform/pull/3) | 66e0240bc211e5d9f08e1019cf686df249adbd97 |
| 2 WB 原值定量、worker、存储与手工闭环 | [#8](https://github.com/Junweiiii14/bioimage-tools-platform/pull/8) | dd929960c4886e882d282490fd9ed59fdc8d2e50 |
| 3 Fig、多原图、OCR 与显式归一化 | [#9](https://github.com/Junweiiii14/bioimage-tools-platform/pull/9) | d7dbee51543e6cc061065fc79598d2eda7a53e8c |
| 4 元信息、归档恢复与维护基线 | [#10](https://github.com/Junweiiii14/bioimage-tools-platform/pull/10) | ef17d8a9c5dc800e6e0ea9842c3bd91714715ba0 |
| 5 实验室版式、模板与自动处理平台 | [#11](https://github.com/Junweiiii14/bioimage-tools-platform/pull/11) | 8be1c56d2399f728ead09415ab8c9800b32cdc99 |
| 6 现有工作台与网页宿主 | [#12](https://github.com/Junweiiii14/bioimage-tools-platform/pull/12) | 4a9c682883fbe552947c520e4e5b00284a8601ae |
| 7 灰度监督、标准显示与真实图验证 | [#13](https://github.com/Junweiiii14/bioimage-tools-platform/pull/13) | 4582976e4623e6ce25e433be59d08290bff3e3a9 |
| 8 原图几何、积分边界与入口统一 | [#14](https://github.com/Junweiiii14/bioimage-tools-platform/pull/14) | 0637250e33044c42a769ac8195a53b8916ff730e |

后继仅文档/回执；不将作者最终完整门禁说成独审者执行。


## CI002–004增量审查

- bcf405a..4943c03：仅增加Windows/Linux CI无缓冲、逐节点输出及60秒栈采集；独审未发现放宽15分钟门禁、断言、skip或退出码处理。
- 5decc73..b4bc8ba：隐藏宿主Qt所有权修复无阻断，审查者独立3项实际exit0（C++销毁、同步/异步拒绝关闭）。作者随后658完整check及8原图功能链exit0；离屏截图空白不作视觉验收。
- b4bc8ba..68c32654d8858331429f5f2a081dfe816ab155bd：阶段诊断无阻断，审查者独立2项实际exit0。日志可能影响调度，不作根因修复证明。
- 阶段7首次Windows初始化5秒超时后原SHA重跑成功；阶段8bcf Windows15分钟取消、5de Windows首次create10秒超时（1failed/656passed）均保留。只读调查没有确定丢回复缺陷，根因UNKNOWN。
