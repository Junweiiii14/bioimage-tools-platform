# 打开本机体验版

[启动 BioImage](../../../.local/releases/runtime-3103063d1abf-acceptance-p028-local/app/BioImageWB-Acceptance.exe) · [三工具练习指南](../../../examples/first-use/README.md) · [下载本机练习 ZIP](../../../.local/p024-first-use.zip)。这是独立目录版；保留整个 app 目录。无需安装，原来的桌面快捷方式仍指向实验室版。标题应为 0.14.0、wb-acceptance-p028-local、3103063d1abf。

**先试 WB 草稿**：从首页进入 WB → 选择仪器文件夹，选[公开单图所在目录](../../../.local/p028-test/input)。在“来源选项”可先点“识别来源与参考图”。添加 Fig，蛋白填 GAPDH，勾选原图，保留未知泳道数 N 为空，点“保存草稿”。关闭并重新启动，从 WB 的最近项目进入，可继续填写。此图不能据文件名推断 N，不能直接自动定量。要练完整流程，请改用练习指南中有已知 5 泳道的两张合成图。

**核分割与 BCA**：按练习指南选择配套 TIFF 或 CSV + record.json。新版设置只预置本机 P015 worker 和 P014 模型路径，不能将目录拷到别的电脑就保证可用；BCA 练习为合成数据。

## 本机核验记录（2026-11-09）

- 产品源码是 PR79 已合入的准确主线 3103063d1abf116ef1d98694b9cc57f4dc70ae22。旧 GCC 缓存不存在，使用锁内官方归档，SHA256 匹配后解压。clean detached HEAD，Windows、锁内 Python 3.12.14，运行现有 build_runtime_candidate --directory-only --laboratory --acceptance-id p028-local --gcc（校验后的 GCC），exit 0。没有安装器或产品改动。
- [身份与包差异](audit.json)：7900 个冻结文件、506 个归档文件、308 个已安装源码/资源通过核对；另核六包目录双向集合，只有预期的 build-identity.json 和生成缓存。与 P023 相比五个 wheel 逐字节一致，桌面 wheel 仅 intake_groups.js 和对应 RECORD 变化；打包说明另增两行。P023/P024 的三工具执行和 P027 的真实编辑冲突、参考组保护证据仅依此范围复用。
- 原生 Win32 EXE 从 TEMP 启动，无开发 PYTHONPATH 或调试端口；UI Automation 读取标题、三个入口、核环境“已配置”，正常关闭 exit 0。最初轮询在窗口句柄就绪前取了空句柄，随后读取实际窗口。另由同一 EXE 启动两次，以本机回环 CDP 驱动可见按钮，Windows 原生选择框选单图目录：识别后加 Fig、选择原图、保存；关闭后再次从同一 EXE 的 WB 最近项目进入。图 3072×2048、16 位；两次均 Fig 1/GAPDH、N 为空、已选原图、自动处理禁用。[保存](exe-saved.json)、[重开](exe-reopen.json)。前一轮确认正常关闭，未取得该次数字退出码；冷重开这一轮 exit 0。
- 补充走查使用包内私有解释器、离屏 Qt、独立 INI 与非原生对话框，保存及新进程重开成功。离屏 stderr 有 GPU/共享图像警告；不作为物理显示验收。没有重复算法矩阵或获取真人、科学或干净 Windows 验收。
- [原生窗口、来源识别与旧配置观察](observations.json)。前后比对实验室版 EXE、卸载程序、P023 EXE、原桌面与开始菜单快捷方式 SHA256，以及五个旧配置命名空间，观察值一致。独立 Acceptance-p028-local 启用自己的设置；原图/练习不修改。P024 ZIP SHA256 仍为 73ccd34c0ed1dbb971241edf200c90ccbe58539f1188189a31f387e423944d2c。该次真实入口新建了独立练习项目，不覆盖历史项目。

计划检查仍先报历史 P010 缺少 reviewed commit（exit 1），本轮没有修订旧卡。未重跑全量科学或产品门禁；未生成或发布安装器。

[固定独审通过](independent/independent-review-3103063.md)。独审用包内运行时复核 WB 草稿、真实 EXE 打开 BCA，并用 CLI 跑 P024 合成练习和冷重开。指南按钮名已按冻结包更正。源码/工件未再修改。无纯收据 PR，本机记录随下一正常任务带入。
