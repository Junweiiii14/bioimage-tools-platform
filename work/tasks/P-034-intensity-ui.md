# P034 从单图核分割结果导出目标通道强度

<!-- PROGRAM_TASK_META {"id":"P-034","status":"in_review","head_commit":"34c118a698bd2e01c2518acbcda4c40d142802b7","work_package":"W14","depends_on":["P-016","P-033"],"execution_root":"C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-plan-sync","owner":"chat-01a1bd9d-3f80-7f03-a3d2-d6fbf16e5127","base_commit":"88e89525446f3f976995f6a15cd51b3c2a522879"} -->

在已完成和重开结果页选择配对原始目标通道，明确确认同视野同坐标后异步导出 CSV 与来源。用 P033 公开样本验证 8 位单视野、失败和原结果安全，冻结后由协调窗派固定独审。

Windows 作者验收。可见工作台从 bioimage_app 正常 main 入口启动，隔离验收设置，脚本操作真实 WebChannel 按钮、Qt 文件对话框和配对确认。使用 P015 既有独立 worker、固定模型及 ExampleHuman 的 AS_09125_050116030001_D03f00d0.tif 新建项目，再选择 d1.tif。取消确认后无导出，选错尺寸显示失败且无发布，随即选择正确原图成功。返回工作台，再打开 P033 既有项目并实导，旧的“导出表、图与标签”亦成功。两次逐核导出分别由 run b4fb346072fb4c748a7dd66beed76c77 和 7f260e3820fa4027957d1bf5c01fcd5e 提供标签。每次运行 P033/verify.py 都与原始像素逐标签复算完全相等（233 行），另复验 289 个固定 PH3 核。首核 ID 1，219 px²，均值 10.269406392694064 DN，积分 2249 DN·px。两份 provenance.json 均记录原图与标签摘要、目标图摘要、执行/运行 ID、配对确认及 512×512 原坐标。输出在本机 %TEMP%/p034-lhlni78m 中的两个独立目录。

作者环境使用锁定的 uv 环境。桌面验收脚本 exit 0；核工具、UI、Web、宿主、强度回归共 33 passed；定向 pyright、ruff、policy、提交钩子均 exit 0。计划结构检查 exit 1，首报既有 P010 缺 reviewed commit。全量套件交必需 CI。F01 留到目录打包，科学准入、真人走查与安装版未验。
