# P023 本机候选工程验证

2026-11-06，Windows x64、本机现有环境，作者验证（不代替独审）。真实流程构建源码为 `969347929eefabe1d23009f653846d58ef899a05`，应用 0.14.0，独立通道 `wb-acceptance-p023-local`。后续冻结构建的准确提交/同源对比另见最终目录审计，不把未检查的新包当旧包。

## 启动与边界

本地 `.local/releases/runtime-969347929eef-acceptance-p023-local/app/BioImageWB-Acceptance.exe` 直接启动，私有 Python 3.12.14 / Qt 6.12.0，无开发 PYTHONPATH、无外部注入 Python、无软件渲染替代。从仓库外工作目录启动，实际窗口标题确认版本/通道/SHA。外部 CDP 驱动只操作本机 127.0.0.1:9233 的 DOM 控件/读取状态；原生文件对话框由 Computer Use 操作。目标进程没有 mock worker。`cdp_probe.py` 为复现辅助，不进入产品包，普通启动无需调试端口。

核环境通过实际设置界面选择一次：`../p015-research/worker-env/Scripts/python.exe` 与 `../p014-research/models/2D_versatile_fluo`，复用既有固定 StarDist 环境，不安装/下载/升级。尚未配置时首页明确准备提示，配置后持久化到本验收通道。

## 已观察

`native-evidence.json.gz` 保存 DOM 捕获、SQLite 正式记录、原始摘要、模板图、退出码及 native 日志。截图仅保留本机 `.local/p023-desktop`，不提交媒体或模型。

|流程|结果与冷重开证据|
|---|---|
|WB 编排内置 triangle_u16|真实 verify/analyze/publish 三 worker 成功，正式结果 signal=4000、valid；关闭后正常打开项目读取相同成果|
|单图核分割|既有公开 Ganglioneuroblastoma_10.tif，固定模型实际 worker 得到 46 核；run `7a669a88298b4b39bf95c6fef5d2f165` 冷重开一致|
|BCA|仓库 synthetic.csv + record.json，经真实 worker 正式提交；run `bb3cad34665a4d1d87aa6dc97bd944bc` 冷重开一致，保留 partial/超范围状态|
|模板复用|从 WB 导出模板，通过正常模板入口以新 uint16 图创建独立项目；新图为原合成图+20，原图未改；新 SHA d3f9a6e…5047，三 worker 成功，正式 signal=4000|
|设置重启|实际停用 BCA，第二进程确认停用且核配置保留；恢复后第三进程确认三个工具启用|
|正常退出|三次 Alt+F4 退出分别返回 0，未强杀；本机本轮未复现 Linux 关闭挂起，历史根因仍 UNKNOWN|

WB/核/BCA 冷重开前后共 40 个正式资产/结果文件 SHA256 不变；完整路径、run/PID/source摘要在压缩证据中。第三进程重读 WB/BCA 时个别立即捕获仍显示“正在处理”，随后 settled 图和正式记录确认完成，不把中间态宣告为完成。首次 CDP 直接 click 被模态框阻塞而超时，改异步点击；一次错误 DOM selector 抛 TypeError；均为外部驱动问题，没有重写产品结果。

## 交付完整性与体量

`directory-audit.json.gz` 为真实构建逐文件 payload 摘要、Git archive 同源、六包 308 个安装源码/资源核对及独立私有解释器依赖清单。源码比较只允许已列文本的 CRLF/LF 差异，payload 字节哈希保持精确。实际核指南 `.md` 首次未在文本白名单而拒绝，确认仅换行差异后补 `.md`；未容许内容改变。

基线目录逻辑体量 1,154,760,191 字节（包含源码、缓存和运行库），其中私有运行库 1,138,179,375 字节；核 worker 外置 2,028,900,854 字节、模型 5,772,540 字节。不把源码体量当运行体量；峰值内存、冷缓存时延未测。

## 检查和未验

`targeted-tests.log.gz`：runtime_integrity + candidate_acceptance 49 passed / 32.34s；`.md` 允许后既有 CRLF/精确 payload 反例 1 passed / 1.21s。前轮测试因原 fixture 四包数量断言5与新六包实际7不符而1 fail/48 pass，现断言7（六包加helper），不改容差/skip。之前可选工具相关18 passed，见任务记录。Ruff通过；类型日志单列。

不声称干净 Windows、真实学生、物理 DPI/GPU、科学/化学准确性、商业签名、安装器或公开发布通过。旧实验室安装、旧设置和历史项目未替换。核/BCA研究边界不变，聊天卡片堆叠预览未实施。PR必需检查和准确提交独审尚待完成。
