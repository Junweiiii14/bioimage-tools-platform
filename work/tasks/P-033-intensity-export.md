# P033 已提交核标签的目标通道强度导出

<!-- PROGRAM_TASK_META {"id":"P-033","status":"done","head_commit":"4fb45866cda22a3509cdd42d805f375ca6dab3a4","work_package":"W14","depends_on":["P-016","P-032"],"execution_root":"C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-plan-sync","owner":"chat-01a1bd6d-3ea8-7303-8448-27d9d1848f1b","base_commit":"fb6638eb7145dc9f0af61679a48aaef24a681606"} -->

继承 P032 收尾 d6de0df。通过正式 CLI 选择已提交核分割项目与同坐标目标通道原图，按原标签导出逐核原始强度。验收覆盖真实结果、官方固定标签参考、稀疏编号和零核。

Windows 本机以 P015 固定 worker 和模型对 ExampleHuman 的 AS_09125_050116030001_D03f00d0.tif 执行 nuclei_cli，再通过 nuclei_intensity_cli 配对 d1.tif。已提交 run 58a49b09055a41088bfee997c38bd08c 输出 233 行。运行 `uv run --locked --no-sync python work/evidence/P-033/verify.py <workspace> <d1.tif> <per-nucleus.csv>`，逐个掩膜核对 CSV，并用 P032 固定标签比较 289 组 PH3 编号、面积、均值和积分，全部精确相等，exit 0。两套标签来自不同分割方法。P015 历史 regression-03/valid-empty 运行同一导出入口得到仅有表头的 CSV 和核数 0 的出处。Windows 本机 tools/nuclei/tests 21 passed，ruff、定向 pyright 和 policy exit 0；未在作者机运行全量套件。

独审 R01/R02 修复。导出前沿解析后的目标父目录查找项目标记，任何项目内部均拒绝；用两个有效项目复验，A→B/results exit 2，B 随后正常导出并逐核复算。测量函数移至宿主的独立 NumPy 模块。相对 PR 基线 `tools/nuclei/src` 零差异，原分割器身份校验完整保留。第一轮 233 核工作区是在改动分割包前生成的，未覆盖首版宿主与旧 worker 的组合。现用修复后的宿主、原 P015 worker 和固定模型重新运行 nuclei_cli，run 8491c70064a0439aa6b53b1013d5e98d 成功；正式导出及 verify.py 对 233 个实际标签、289 个 P032 固定标签均 exit 0。两组针对性测试共 22 passed，定向 pyright、policy exit 0。计划检查仍首报既有 P010 缺 reviewed commit。

R03：计算函数迁至现有 nuclei-tool wheel 的同级命名空间 nuclei_intensity.api，宿主仅通过公开接口编排与发布。原分割包和指纹算法相对基线零差异。为同一 src 下两个已登记包调整 AST 按目录扫描一次并核对 owner 与实际目录，加入错误目录和未知包负例；import-linter 将强度包纳入工具独立性与纯计算约束（12 kept）；既有独立 wheel 探针新增已安装强度 API 来源与计算断言。无锁文件或阈值变动。以新 wheel 在隔离虚拟环境运行该探针 exit 0；原 P015 worker 在新版宿主产生 run 7f260e3820fa4027957d1bf5c01fcd5e。普通输出目录含另一应用的 workspace.json 时仍可导出，逐核 233/289 精确复核；项目头识别复用 WorkspaceFormat。核工具、导出与边界回归合计 36 passed。

[最终固定独审 PASS](../evidence/P-033/independent/independent-review-4fb4586.md) 绑定 4fb45866cda22a3509cdd42d805f375ca6dab3a4。北京时间 2026-11-09 08:01:31，[PR84](https://github.com/Junweiiii14/bioimage-tools-platform/pull/84) squash 至 main 88e89525446f3f976995f6a15cd51b3c2a522879，与已审 HEAD 的 git diff --exit-code 为 0。规则 5s、桌面环境 31s、Ubuntu 18m53s、Windows 27m53s 均通过，native-case 条件跳过。共享树一次本地收尾释放。

F01 留给下一次含此方法的目录安装候选：将 nuclei_intensity 纳入安装源码逐文件映射与私有运行时导入探针，按原提交兼容旧候选六个命名空间。未来接收任意数组的调用方还需区分零像素网格与有效图像零核，当前 TIFF 入口已拒绝零像素。
