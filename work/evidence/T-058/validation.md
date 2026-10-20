# E5/T058 验证（最终工程阶段完成）

base9d747ef，Win11/Python3.12.14/Qt6.12.0，锁/门禁未改；规则输出已读取，回执随任务保存。

- 新核心3 passed/2.58s：1–96槽数性质、重复蛋白独立身份/空值、裁剪失败显式状态、schema13旧表结构不变/schema14旧读拒绝、部分索引/恢复资产重映射摘要稳定。
- 新导出/旧归档/E4核心联合37 passed/8.34s（.local/t058-core-adapter.txt）；新增最后CSV解析预期后7 passed/5.09s（.local/t058-core-final-substep.txt）。两Fig全部原图/固定槽位、原始三角积分400×来源倍数×槽位、无信号空值、输出索引实际成员SHA/长度、完整导出/重复导出旧ZIP不变/归档重新检查、缺run降为部分、变源、取消和ENOSPC注入均覆盖。
- 纯适配测试的RunRecord PID123明确为应用边界夹具，不是实际worker或本机成功收据；真实宿主/worker到导出/CAS未验收。
- 开发失败保留：初次裸test模块导入不适用当前pytest importlib模式，改为现有命名空间测试助手路径；StagedProjectArchive误用位置参数导致摘要拒绝，改明确关键字而不改预期。首版冻结复制无扩展被既有TIFF入口正确拒绝，现仅按已验证容器头保留读取器扩展，不绕过TIFF/原值检查。新增测试块一度置于取消测试中间产生NameError，已修回所属测试；没有弱化断言/容差/预算/时限。
- 核心/适配定向Pyright0，第一次全仓Pyright仅测试decoded列表缺注释3项，补明确LoadedProjectResult类型；最终全仓待重跑。Ruff格式/导入机械修正。新进程API不加载任何PIL模块探针0。
- 未完成：宿主/界面/恢复故障集成、隔离wheel14、最终完整check、绑定最终提交非作者独审。E5仍implementing。

## 真实宿主与最终候选

- 5e579a3核心/适配首轮独审P2：仅冻结原资产，ZIP再次读取外部run路径可能降级而外层仍complete。02ce5b6增加有界冻结请求/结果副本、重读ZIP状态一致检查；外部原run变更/冻结副本篡改两故障注入，9 passed/6.21s；独立9/6.30s，P2 resolved。旧记录不删除。
- 823077e连接真实宿主、工作线程、Web桥接、输出状态和恢复：24桌面+9UI共33 passed/61.09s，原进程0（.local/t058-host-final.txt）。真实两worker具PID/终态/结果，完整CSV/XLSX/ZIP/index，重复新目录旧ZIP字节不变；新宿主恢复外来历史、实际本机runs为空，再export-only续跑通过1/11.65s。故障claim-save、output-save、发布后迟到取消、worker写盘失败、执行前取消5/26.95s0，失败不变done、不登记伪收据。
- 浏览器第一批检查发现旧groupReview优先拦截真实intake量化结果；修正group_review路由guard，旧独立灰度仍保留。最终登记CAS后view清空展示表，增加真实已核验表刷新。9UI/10.26s0；真实restore重复1/10.78s0并断言最终16固定槽位（.local/t058-real-restore-route.txt）。合成平坦原图均未检测，空值与质量原因保留，不作为科学准确率。
- 823独审P2：同步prepare/retry/approve失败前提前begin导致无异步任务busy悬挂。8feffce将begin移至同步验证之后；真实output-save故障后再次导出1/8.48s0，当前快照/输出根列表保持且宿主空闲（.local/t058-repeat-save-fault.txt）。独立实际方法探针0、P2 resolved，绑定8feffceefb6ca83b0ef90c61bcfe2a5aac877dfb无新增P0–P2。
- 全仓Ruff0、Node intake语法0、API无PIL探针0；823首轮完整check在Pyright拒绝新增len(object)断言退出1，未进入pytest/wheel，保留.local/t058-fullcheck-final.txt。8feffce只加类型cast不改预期/容差/时限；全仓Pyright0。最终8fe全量check正在串行执行（.local/t058-fullcheck-8fe.txt），未提前记通过。
- Impeccable context本会话仅此前一次；E5 detector一次0primary/68既存advisory（31颜色/22字号/15半径），没有忽略或canonize。作者截图两批后停止自检，四张1280×720已逐张打开：.impeccable/review/t058-browser-{complete,partial,unregistered,busy}.png。完整视图由合成图真实运行快照投影，其他三张明确状态样例；真实故障以Qt测试而非截图证明。独立finish reviewer disposition: ship（823同UI，后续8fe未改界面），长路径/缺口/未登记/忙态均匹配。不是原生物理DPI/科学验收。
- 测试初次schema13/export pending预期失败2项是新正常链明确升级14/自动输出所致；已改对应新版本预期，旧13读取/表格语义兼容仍单独测试。Pyright测试局部类型修正无ignore；未更改锁、算法、预算、skip/xfail或门禁。

## 最终门禁与收尾

8feffce最终 `uv run --locked --no-sync python dev.py check --all` 实际退出0；.local/t058-fullcheck-8fe.txt：858 passed/623.78s，Observed child exit=0/u32=0x00000000，9导入契约、全仓格式/类型、全部隔离wheel（含14纯API/旧版读取/无PIL）、真实离线PP-OCRv6 CPU/worker/PNG OCR和桌面异步关闭均完成。inventory仍344/truncated，不等于泄漏证明；历史purecall UNKNOWN未销账。Qt/WebEngine离屏告警保留；没有因此削弱断言、预算或检查。

非作者独审最终绑定8feffce，核心与宿主两P2均resolved，无新增P0–P2；UI ship及documenter No changes。E5本机源码工程阶段done，继续E6/T059；科学留出/真实确认批次/干净Win10及物理DPI、main与安装版尚未完成。本轮只读查询远端PR状态，不修改远端。
