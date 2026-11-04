# 当前恢复入口

2026-11-04：用户授权P010，从WB研究普通学生的完整流程、结果和现有缺口，并交新窗口使用真实目标模式持续推进。活动树bioimage-plan-sync，分支codex/p010-wb-discovery；继承200720f的B019本地收尾，main基线c8f1bcb。原主目录旧dirty不碰。

- 当前任务转work/tasks/P-011-wb-student-results.md；P010调研记录见work/evidence/P-010/wb-discovery.md。明确缺口：自动裁图reviewed=false与旧归一化人工标记不兼容、重复身份未结构化；归一化UI本已接入，不重写。
- 当前优先：复用已有WB测量、配对/归一化、成图导出，研究学生完整路径；样本/重复与统计交换表是候选缺口。P009已完成，不照旧审计重建执行器。
- 本聊天已成功create_goal，active、无token预算。继续P011最小完整切片，不全面扩展其他实验或Agent；P011 context/integration已记录，产品候选918af16已提交，另有测试/交接补丁未提交。
- 当前衔接修复：新增bounded_background_context@1仅扩展背景搜索许可，目标不变、限25%/裁图/膜有效区/非选中标签。任务与docs/contracts/wb-bounded-background-context-v1.md记录历史兼容；当前网页真实worker正/负例2通过，5个新边界/解析面积/旧wire回归通过。产品候选918af16已提交。
- 本机全门禁91098已终态exit1：1696passed/5failed，1427秒，父目录p011-check-all.log。CI参数定向复验7pass/1fail；抓到cancel停在confirm_draft是native测试绕过网页token。已改测试等待channel并点wf-run，v5继续前等snapshot启动的预览读取；3例最终通过，产品保护未改。新端到端3例（单图/三联图/无效反例）通过。Qtgrab内容仍可能旧帧，已用CDP验证当前DOM和实际画面，证据visual/三张PNG与capture.json；捕获工具QtWebSocket有0xc0000139日志但exit0，保留限制。
- 产品918af16，当前HEAD e349b2e（测试入口修正已提交未推送）；视觉/交接证据待提交。下一步静态检查后提交修正，先收完原PR60 Windows/PR61 CI结果（避免推送取消在跑证据），再正常集成PR61、合入main并重载P011回执。独审权限已异步问过，尚未答复；不重复问、不启动子代理。
- 用户确认不知道配对/分组重复/软件背景方法，并要求少问、自主调研。这些科学语义保留UNKNOWN，明确合成身份支持工程对照，真实科学/学生验收不宣称通过。
- 基线bf52b61归一化15测试、网页worker/CAS2测试、自动完整入口17checks通过；offscreen GPU日志及原生computer-use窗口绑定失败保留。接续树原缺依赖，已uv sync --locked --all-groups；不改锁。原生验收进程45312及实际子进程53468已正常CloseMainWindow退出，确认均不存在。
- 用户要求不要过度设计/过度防御：小文案与收尾记录随正常任务处理，不追加完整检查轮次；数据保护、科学口径和既有必需检查保留。
- 真实未验边界仍见risks及Issue57；资料目录可只读核对，原图、旧结果和未提交内容不覆盖、不上传。

- 草稿PR60：https://github.com/Junweiiii14/bioimage-tools-platform/pull/60，已attach，HEAD35cfe0b（产品918af16；测试加单图/静态捕获）。正常CI已触发；未独审/未合并。本机live全门禁没显式--disable-gpu，CI有；不要把本机失败自动归因环境。当前测试增强待单独运行，本机旧collection不覆盖新增参数。

- PR60规则失败已定位两份changed integration清单。按runbook分阶段：新PR61文档前置head3caf797，rules/desktop已SUCCESS，foundation仍运行；待正常合入后更新PR60基线与P011回执。不删除/重命名历史回执，不改门禁。两个PR已attach。

- PR60旧head35cfe双平台foundation均SUCCESS：Windows1702pass，Linux1698pass/4既有skip，隔离wheel/其余check全过。PR61 Windows仍live，其他checks成功；等其通过正常merge后更新产品基线与回执。新测试修正e349尚未推送，避免取消在跑证据。
