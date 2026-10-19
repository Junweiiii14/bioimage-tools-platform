# Current Work Log

## 2026-10-14 / T-002（部分验收）

源码真实 Qt 操作、35 项测试通过。修复 Linux libEGL 缺失；四项 CI 在 293c6c0 全通过。Nuitka 裁剪未用依赖，模块 1025→359，713 秒构建成功；应用 183.5MiB，含固定大图测试集 ZIP 794MiB，解压 330 文件逐 SHA 校验。包态单图/批次、合作取消/5 秒强停/崩溃恢复通过。净化环境从中文目录启动 EXE 后，用户物理 Esc 停止 Computer Use，包态原生 GUI 与 125/200% 缩放未测；严格保留待办和草稿 PR #3，不合并、不宣称完整 P0 通过。

## 2026-10-13 / T-002（实施中）

按用户授权启动 P0，创建独立 Qt/worker/合成样本/基准与 standalone 构建探针。基线 29 测试通过；修复 Windows 管道/DLL 加载锁冲突与 uv 启动器子进程问题后 35 测试通过。三类单图各 5 次与 20 图批次 3 次源码基准已运行；窗口、打包和包态证据待补。用户指定干净机验收后续进行。

## 2026-10-13 / F-002

依用户明确要求公开仓库、合并 PR #1，并启用 main ruleset 25008972。新增按范围加载规则与绑定 base/head 的回执检查，补非编码研究规范及父目录路由。29 个测试通过；GitHub 上单独缺回执时其余三个检查通过但 PR BLOCKED，补回执后四项通过。修复 Windows 输出编码，去除重复 CI，并让本地已同步环境使用 --no-sync。交付 PR #2，集成状态以 GitHub 为准；没有开始产品开发。

## 2026-10-13

完成原方案阅读、官方技术文档和 GitHub 技能调研，恢复 GitHub CLI 授权并建立私有仓库。建立规则、模块地图、ADR、任务/PR 模板、CI、依赖锁、边界检查、交接和 5 个技能。uv/项目 Python 及 67 个依赖可用，环境 smoke、质量门禁、14 个测试与漏洞查询通过。解决缓存路径和 uv Python DLL 启动器问题，GCC 15.2.0 编译运行通过；Windows/Linux 三项 CI 通过。已建立草稿 PR #1，没有合并或启动产品开发。未创建产品模块或算法。

## 2026-10-19 T-050 规划修订

用户确认清单驱动的仪器原图流程。对产品a234354只读审计，核对原始PDF；从main221a2df独立文档分支创建新版规划和README入口，避免夹带未集成产品。清单/固定N/原像素定量是已确认需求，局部异常续作/独立输出目录/可选OCR发行是待审建议。代码、依赖、锁、门禁及原始PDF未改。旧main恢复快照留档。

## 2026-10-19 T050 审核回复落盘

根据用户回复更新第5/6/7/8节：批准局部暂停与独立结果目录，独立灰度定量OCR作为继续支持的功能。主流程不加载OCR与安装发行拆分是不同事项，后者未决；同步任务/风险/待办和交接。未改产品/PDF/依赖，旧审查不外推本轮修订。

## 2026-10-20 E7 governance integration

INT001 resumes authorized E7 only in this temporary historical integration tree. Merged planning main43d520f into original governance0b7, retained immutable RULE001 receipt source; loaded/read exact rules and current full scope. Main PR/CI not yet accepted. WB product development/checks remain in t051, not represented by this zero-product checkout.
