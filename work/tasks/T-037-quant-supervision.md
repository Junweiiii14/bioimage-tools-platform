# T-037 灰度定量监督

- 状态 implementing；用户批准WBQuant1.4.3算法/表格基准、自动泳道/计算填表、无逐图确认，当前桌面同源网页内监督，不跳旧窗口。
- 基线e8e5e21；分支codex/t037-quant-supervision，保留已有布局/动效与原像素。
- 指定G4末尾11597、M2末尾26751两叠加源图验收；旧软件目录只读。
- 范围tools/wb、apps/desktop、tests、docs、work、.agent-handoff、PRODUCT.md、DESIGN.md、.impeccable。
- 分工：算法兼容和导出核心、网页监督UI、宿主桥接集成；代码分树，最终独审绑定提交。
