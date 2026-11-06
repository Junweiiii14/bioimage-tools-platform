# P022 可选工具装配与重启停用

<!-- PROGRAM_TASK_META {"id":"P-022","status":"done","work_package":"W13","depends_on":["P-021"],"execution_root":"C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-plan-sync","owner":"chat-01a1b0c7-c5ea-71a2-9e7e-b25ee7daaa74","base_commit":"2a3c7a32936c6e4daf63dac23fb953cc4512e840"} -->

2026-11-06 上游明确派发。起始 HEAD e5b3d52cee737f3cd7f7fad46ecd30aeb1cc47ad，干净，保留 P021 本地收尾。状态：工程完成。PR74/main b13e71a与指定独审47ded5e同树，必需CI通过；Linux首轮挂起UNKNOWN按独审判断保留非阻断。详[最终交付](../evidence/P-022/final-delivery.md)。一次本地收尾后释放共享树，上游新窗派下一任务。

## 范围与验收

- 先以隔离 wheel 和普通桌面入口证明现有耦合，最小修复 WB/核分割/BCA 可选装配；默认保持三工具。
- 已知可信注册，简单设置，下次启动生效；缺包、停用、缺重模型环境分开提示。
- 有界矩阵：仅平台、各单工具、全工具、移除或停用一项后重启；单工具各一既有非私有样例执行、正式保存和重开。核分割复用冻结隔离 worker。
- 缺工具历史明确不可执行；原字节不删不重算，剩余工具有真实代表链。静态边界、wheel 安装、真实启动分别记录。记录最小依赖和磁盘，性能未测明确标注。
- 不改算法/权重/参考/依赖版本，不做热插拔、SDK、市场、任意代码加载、安装器管理，不发布/替换用户安装。
- 遵循 B021：冻结 base/head、PR、自验和边界后回传上游指定独审；不自行找审查或合并。合入后一次本地记录并释放共享树。

## 检查

作者真实wheel矩阵、指定首审/最终增量审查、准确候选双平台check --all及wheel成功，详[最终交付](../evidence/P-022/final-delivery.md)。Linux首次挂起和唯一一次重跑分别记录，根因UNKNOWN未关闭。本机16项关闭/运行复验成功；跨修复本机全量exit0仅诊断。科学、真人、物理DPI、目标机、用户安装不声明通过。
