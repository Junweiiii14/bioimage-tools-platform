# T045验证记录

- 环境：Windows、锁定uv/Python3.12.14；新隔离树codex/t045-wbquant-manual-and-fig，base f42f069。用户原活动目录缺Git/隐藏资料，现存受管文件与base规范化换行后全部相同。仅新建一个worktree；旧树与旧dirty不动，不改桌面快捷方式。
- 用户指定原图SHA256 a2db16a4833db3116196968f22461e2b6d204f7d027c12e15881ae29885556d1；只读。生成结果与原OCR日志放ignored .local/t045，不提交原图。
- uv sync --locked --all-groups：0。首轮T044独立量化11项：11passed/9.73s/0。
- 首轮手动核心4+原工作台1：5passed/18.58s/0。解析独立双峰1000/800、整段1800、人工范围1000；共享原图新组、schema读取和不修改源字节通过。
- 旧多峰回归发现作者排序把中间None槽移到末尾：1failed15passed；已将新排序限制到人工补峰，旧检测峰顺序保持。后继12项8.35s/0。
- 桌面增量曾有作者变量ordered重名导致Qt snapshot异常，已改名；未修改原测试预期或屏蔽异常。
- 新手动控件测试前两轮输入项目目录在原图目录内部，被既有边界正确拒绝；修正测试资料为sibling目录。后续发现等待前端状态镜像不充分，按project generation同步；再发现正常保存修订使撤销历史误失效，改成精确参数快照（忽略运行修订）并在还原时使用当前修订。最终新手动桌面1passed/9.88s/0，正常worker多峰/复制与坐标修改/补峰/撤销重做/重选保留结果/新组/保存重开。该用例首框明确种下几何草稿，不声称覆盖原生指针绘制。
- 自动初步二维/一维峰检测有双瓣过分割、弱带漏检，保留.local/t045/partition.json及proposals.json；不能以分组个数算检测准确率。后继使用二维区域、同图重复宽度和分段证据；I/L和缺标签显式提示。
- 真实首次探针选择未稳定，修探针等待；第二次真实发现Qt表格重建会下转schema8，旧新证据校验正确拒绝，已补schema9保留。真实第三次正常后台进行中，未算通过。
- 合成Fig域/安装/取消/schema9两项已通过；最终静态/全门禁/真实重开/绑定提交独审待完成。

## 已完成真实回归与修复

- 第三次正常产品链：33 Fig、106条带行、106计划/worker运行全部succeeded；源SHA不变。保存工作区和回执在ignored `.local/t045/real/receipt.json`。真实重开106结果、schema9、UB8曲线；共享原图预览只传1份，wire约1.31MB。不是独立留出准确率。
- group rename/move初版使用model_dump再严格解析，丢失LaneROI类型，针对测试失败；修正为保留原字段类型。新手动1passed10.89s/0；未放松FigureRow验证。
- 视觉发现确认框线造成UB尾部伪峰；复用冻结WBQuant细边框判断，仅排确定框，解析双峰整段1800保持。真实2整段行重算，历史run保留；104其他行不重算。`.local/t045/reopen-final.json`恢复106，UB有效范围仍整段而非局部峰。
- 首次全门禁check-all.log发现上述rename失败，约250项时作者明确停止自有pytest以修复，外层-1；不是完整通过。用户PID33256未动。
- a2cda5f独立审查30项0，发现UB改框丢整段模式、同包围框切回网格不换策略、粗描边、缺平移和分组导航挤压。3f4c593集中修复，独立33项10.12s/0及四张有效截图评定原5项resolved；又发现Space全局拦截按钮激活，待窄修复。不将修复清单评分写为全产品验收。
- 作者修复后20项10.99s/0；最终9项10.93s/0含UB移动/缩放/序列化重开、相同包围框策略切换、真实Qt鼠标平移/取消/缩放平移后原图坐标框选。指针用例开始曾异步事件未同步、选取点落视口外，保留失败；改为等待事件状态并在可见区域选择，未降低原坐标或积分答案。
- 全项目Ruff/539文件格式、Pyright0，Node两份JS语法0，policy128产品文件/0；3f4c593完整check-all-final.log运行中。
- Impeccable两轮作者检查后按独立清单一次修复并同文件重捕；不运行第二次detector。documenter只读核对，无token变更；预存DESIGN/sidecar/PRODUCT原生入口等文档漂移保留。私图截图不提交。

- 3f4c593完整check在19%停留后作者停止已核验自有pytest48496，外层实际1、wheel未跑。外部native采集受现有owned-tree guard拒绝ValueError/1；不绕过诊断安全边界、不推断具体锁根因。原日志保留。8246eb1后继使用既有BIOIMAGE_NATIVE_STACKS/BIOIMAGE_WINDOWS_FAULTS与faulthandler_timeout=60重新完整检查，`.local/t045/check-all-observed.log`，尚未完成。
- 最后Space修复作者1项11.26秒0，独立1项10.17秒0，disposition ship仅针对修复与相关回归；见review.md。没有新截图/视觉改动，documenter确认无token更新。
- 真实分组导出`.local/t045/real/export-final/receipt.json`：33组135条带结果行545数值、106来源运行；CSV/XLSX均新文件写入、再次导出拒绝覆盖且字节不变，脚本0。Start-BioImage.ps1 --verify-launch/0确认候选源和web资源；没有启动可见用户应用或改快捷方式。

- 指针用例坐标断言允许±1原像素，仅覆盖QPoint屏幕整数取整再映射的量化误差；积分解析值与既有数值测试预期未放宽。诊断轮后来已推进28%，线程快照不作为证明挂起或具体根因，先前轮停止仅为作者主动停止。

- 8246eb1完整诊断轮自然结束：1failed/746passed/512.86s，原child1（0x00000001）与外层1，wheel因pytest失败未运行。唯一失败为旧兼容测试仍将schema9视为未知；不是数值失败或原生退出。f18589a只把该未知反例9改10，99/True/字符串7及旧schema1–6渲染SHA保持，schema9正例已由Fig测试/真实重开覆盖。此预期变化是新格式边界更新，单独提交并交独审，不削弱已知版本校验。
- f18589a相关兼容+Fig14passed4.11s/0；最终完整check带逐用例日志`.local/t045/check-all-release-candidate.log`运行中。临时环境只加诊断/verbosity，不改门禁、时限退出策略、预期或skip。

- f18589a测试后继独审14项6.28秒0，认可已知schema9/未知10边界；没有产品代码修改。最终保全复核`.local/t045/preservation-final.json`：旧活动树四个相关核心文件与base f42f069仅规范化换行后相同，原图SHA仍原值；本轮只创建一个t045树，无改快捷方式/删除旧树/原项目同步。

## 最终结果

- 产品/测试f18589a（产品内容等同已审8246eb1）执行`uv run --locked --no-sync python dev.py check --all`：747passed/517.90秒；原pytest child exit0/u32=0x00000000，全部隔离wheel含真实OCR、桌面/协议/字体/归档验证成功，最终外层exit0。Ruff/Pyright/格式539文件/9导入合约均通过。完整日志`.local/t045/check-all-release-candidate.log`。
- 最终临时环境：QT offscreen；BIOIMAGE_NATIVE_STACKS=1/BIOIMAGE_WINDOWS_FAULTS=1/PYTHONFAULTHANDLER=1，PYTEST_ADDOPTS只加-vv和faulthandler_timeout60。未调整测试退出、预期容差/skip、依赖锁、产品算法以绕过失败；诊断不等于历史原生问题已解决。
- 后继仅文档/回执/交接，增加.gitignore对私图截图`.impeccable/review/`的忽略，避免原图捕获误提交；不忽略产品/测试或任何门禁输入。已提交源图不含原图/结果/截图/模型/安装包。容量维护按既有技能归档旧段再整理。
- 本地工程交付完成，未push、PR/main集成、改快捷方式或发布；科学留出/原生历史UNKNOWN/最终干净Windows与DPI按既有任务保留。
