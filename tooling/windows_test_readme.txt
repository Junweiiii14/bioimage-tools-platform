BioImage WB 测试版（T048）

本包仅供测试，尚未作为正式版上线。独立安装，不覆盖原版或此前候选版。

系统要求：64 位 Intel/AMD Windows 10 1809（内部版本 17763）或更新系统。
32 位 Windows、ARM 系统及更旧 Windows 不支持。可按 Win+R，输入 winver 查看版本。
建议使用 Windows 10 22H2 并安装可用系统更新。

安装：双击 Setup.exe，阅读说明并点击安装。无需管理员权限。
运行环境、Qt、数值计算库、VC++ 运行库和 OCR 模型均已包含，无需联网下载，
无需预装 Python、uv、Node、Office、WebView2 或 Visual Studio。
安装过程会建立当前用户桌面和开始菜单快捷方式，并登记 Windows 卸载入口。
默认位置：%LOCALAPPDATA%\Programs\BioImage WB Test
安装完成后可直接启动，也可双击桌面“BioImage WB（测试版）”。
程序窗口中的“候选版”字样同样表示测试通道。

环境自检：开始菜单 → BioImage WB（测试版）→ 环境自检。
自检使用临时合成图片，检查本地模型、定量任务、项目保存与重开、取消和退出。
不会导入或改写你的原图/项目。报告保存在 %LOCALAPPDATA%\BioImage-WB-Test\Diagnostics。
通过自检不代表实验定量结果已通过科学验证，仍需按 Fig 审核泳道、曲线和封底。

卸载：Windows 设置 → 应用 → BioImage WB（测试版），或开始菜单“卸载测试版”。
卸载移除本测试程序与入口，保留用户自行保存的项目、原图、结果与个人设置。

验收范围：本包在本机 Windows 11 完成安装和运行验收；尚未获得干净 Win10
机器的实测记录，不能将其写成 Win10 全面验收通过。目标电脑请先运行环境自检，
如有失败保留报告并反馈；不要删除原版或仅有的原始数据。

交付目录 SHA256SUMS.txt 可用于核对安装包是否完整。
