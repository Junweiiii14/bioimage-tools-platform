# P022 首审：changes_required

2026-11-06，独审窗口 `01a1af0d-808e-7131-ae29-237aded27938`（local）。PR74：https://github.com/Junweiiii14/bioimage-tools-platform/pull/74。

- reviewed base：`2a3c7a32936c6e4daf63dac23fb953cc4512e840`
- reviewed candidate：`47c8d08730dce974ba3d2d4488e8e032dede2ad3`
- 独立树：`C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-review-p022`，detached、tracked clean。
- 独立开发验证环境：`.local/reviewer-venv`，`uv sync --locked --all-groups --offline` exit0；另外为真实装配构建6个wheel、创建5个全新venv。未修改作者树、原图、历史、已有环境或用户安装。

范围为B021 A1–A3当前适用的已知WB/核分割/BCA可选桌面装配、重启启停、实际缺包及历史拒绝。不是热插拔、插件市场、任意代码加载、未来工具零修改接入、Agent或科学准入审查。当前 **changes_required**，仅下述R01为阻断；正向矩阵成功不能抵消该入口造成的剩余工具阻断。

## P022-R01 / P2：停用WB后目录拖放污染全局打开状态

位置：`apps/desktop/src/bioimage_app/web_window.py:489–495`（`start_from_images`），后续轮询失败在:814。WB未装配时，首页WB卡仍可接收本地目录拖放；方法先写 `_starting=True`、`_stage="opening"` 等状态，随后 `self.host` 属性才检查工具并抛异常。外层拖放处理只展示错误，未撤销这些生命周期写入。

独立复现：WB已停用、BCA仍启用，向首页WB卡实际DOM坐标发送 `QDragEnterEvent` / `QDropEvent`，经过真实WebEngine目标定位及异步native回调，不直接调用私有drop方法。正确停用提示出现，但阶段卡在opening；150ms轮询反复抛“WB已停用”。再进入BCA选择CSV，被拒绝“请等待当前任务完成，或先取消运行”，却无真实任务能完成。未观察到原图/历史损坏，不扩大为数据丢失。

最小整改：在 `start_from_images` 任何状态修改前 `tools.require("wb")`，保留明确拒绝提示。可补充前端不可用拖放提示，但仅拦卡片click不足。复审范围：WB停用/物理缺失时真实drop不污染阶段，剩余BCA能继续；原有效WB导入和关闭仍正常。

命令：`.local/reviewer-venv/Scripts/python.exe -I -B -m pytest .local/ui-review/test_disabled_wb_drop.py -q -s -p no:cacheprovider --basetemp .local/ui-review/drop-tmp`。**exit0，1 passed / 4.84s**，通过指成功断言现存缺陷，不是产品通过。证据 `.local/ui-review/disabled-wb-drop-results.json`、`test_disabled_wb_drop.py`、`receipt-47c8d08.md`。事件循环异常作为缺陷证据捕获；窗口已正确关闭。

## 非阻断 P022-N01：复现驱动未沿用最终证据的设置方式

`work/evidence/P-022/run_matrix.py:108`的disabled场景仍在新命名空间直接传 `disabled=["wb"]`。重跑这个驱动会重新写开关，不能复验“沿用上一进程设置”。最终 `matrix.json.gz` 已有真实共享settings_name及preserve_settings=true的正确记录，故不否定现有产品证据。建议随R01把驱动同步为共享all场景设置并保留，不单开回合；本审独立矩阵已经按真实持久设置重启验证。

## 实际独立验证

Windows / CPython3.12.14 / PySide6 6.12.0。以下Qt使用offscreen；主矩阵及回归为 `--disable-gpu --disable-software-rasterizer`，子审UI为 `--disable-gpu`。GPU/shared-image及缺Qt字体目录警告保留；不宣称物理GPU、字体或目标设备问题解决。

### 真实安装矩阵

命令 `.local/reviewer-venv/Scripts/python.exe -I -B .local/run_review_matrix.py`：**exit0，13场景完成**。自有driver从准确候选独立构建并安装wheel、按锁创建5个隔离环境，`-I`验证app实际来自各venv，使用已逐段审阅的仓库 `desktop_probe.py` 驱动真实 `__main__` / WebChannel / WorkflowSession / Workspace。该复用驱动替代文件选择以提供公开样例，未模拟算法、worker或提交。独立driver另核安装清单/状态、共享设置重启，以及不同工具的卸载/恢复。复用脚本及wheel摘要、全部命令与退出码见 `.local/installed-review/receipt.json`，分场景日志与report同目录。

| 场景 | 独立结果 |
|---|---|
| 仅平台 | 首页/WebChannel及正常关闭；三个工具missing；无实验包、NumPy、Pillow或重模型库 |
| 仅WB + 新进程冷重开 | 真实既有16bit三节点流程completed，20个资产摘要不变；无核分割/BCA |
| 仅核分割 + 新进程冷重开 | 真实冻结StarDist worker得到46核、completed，8个资产摘要不变；宿主无WB/BCA/scipy/重模型库 |
| 核分割已启用但缺模型配置 | 准备提示与missing/disabled状态分开；未替换算法或猜模型 |
| 仅BCA + 新进程冷重开 | 真实固定单板样例completed_with_issues，12个资产摘要不变；无WB/核分割/Pillow/scipy |
| 全工具 + 新进程逐项冷重开 | 三条既有真实流程运行并分别恢复，资产摘要不变 |
| 全工具窗口设置下次停WB后重启 | 直接沿用同一QSettings、preserve_settings=true；WB disabled，BCA继续真实完成，WB历史明确拒绝且20个资产不变 |
| 仅在审查all-env卸载BCA后重启 | WB仍真实执行；核分割历史仍可重开；BCA missing、历史明确不可执行，原12个资产不变 |
| 装回同一BCA wheel后重启 | BCA旧项目可恢复，12个资产不变；无重算替换历史 |

核分割只只读调用已冻结的 `p015-research/worker-env` 与 `p014-research/models/2D_versatile_fluo`，输入是既有公开Ganglioneuroblastoma_10图。没有升级或修改这些环境/模型。单环境运行截图是离屏探针抓图，不能当作真人或完整原生视觉验收；已查看平台首页和核流程画布。

### 回归、历史及生命周期反例

1. `.local/reviewer-venv/Scripts/python.exe -I -B -m pytest -q tests/test_optional_tools.py tests/test_project_navigation_session.py tests/test_research_authoring_web.py tests/test_web_folder_start.py`：**exit0，18 passed / 34.70s**，日志 `.local/targeted-47c8d08.log`。包含既有WB导入、草稿/保存/取消/关闭、新设置及研究图回归；未覆盖的R01另行成立。
2. 真实BCA worker取得PID后改变下次启用设置，当前session不变；请求退出得到confirm_busy，选择返回可继续至正式提交；新窗口读取同一设置后BCA确实停用。`.local/reviewer-venv/Scripts/python.exe -I -B -m pytest .local/ui-review/test_restart_lifecycle.py -q -s -p no:cacheprovider --basetemp .local/ui-review/lifecycle-tmp`：**exit0，1 passed / 3.53s**。非真人，未改当前运行注册。
3. 自有P021合成已完成BCA历史复制反例：停用/缺失两种原因均拒绝load/results/save/freeze/bind/export及真实Session.reopen；projection为空、未进入执行注册、无工具导入/worker，91个文件含数据库逐字节不变。屏蔽WB/核分割导入后BCA三输出仍可核验读取；未知tool身份模型拒绝，未降级WB。独立脚本最终 **exit0**，各子命令及结果见 `.local/provenance-review/receipt.json`、`probe.py`、`followup.py`。这里的缺包使用导入拦截，物理卸载另由上表证明。
4. 历史探针初版错误要求跨源码提交matches_run=true而exit1，原日志保留；核实仅host_runtime_source摘要变化，当前宿主合理将旧成果标为不匹配当前运行环境，同时保留可验证的历史读取。未修改产品或原测试以抹去该失败。
5. 普通历史命令拒绝前仍会经过通用Workspace.open。崩溃遗留prepared/running/staging会按既有恢复协议诚实标中断/隔离，因此“91个正常已完成历史文件不变”不能扩大为“任意异常工作区毫无磁盘变化”。

### 依赖、来源与门禁

- 锁文件85条中仅bioimage-app结构变化；78个第三方条目的版本、来源、全部工件摘要逐项完全相同。去掉默认BCA/核分割，新增bca extra，保留nuclei/wb extras；开发根仍三工具。
- `installed_wheels.py`七段旧probe字符串逐字不变、installed_check AST不变，新增无工具普通桌面入口/关闭，基础与全工具组合相应调整；没有削弱旧门禁。本轮独立矩阵实际运行了对应装配，不将静态导入当启动证明。
- 26项作者工件索引大小/摘要全部匹配，15份最终报告ok；对照最终设置与卸载记录支持其声明。作者早期探针时序/退出失败保留，不冒称本主审执行。
- 算法工具/API、通用包、模型/参考、第三方技能及其他保护路径zero diff；自研只在固定宿主装配点分支导入，没有项目指定模块名、第二执行器或插件SDK。源码职责与重复检查受限于真实入口/生命周期边界，未见须阻断的无消费者抽象。
- 只读分析exit0，证据 `.local/boundary-review/inspection.json`。准确base/head `tooling/rule_context.py check` **exit0**；`git diff --check base candidate` **exit0**。

## 未验与下一步

本主审未重跑全量CI、科学/化学真值/LoQ/训练重叠、真人、物理拖放设备、DPI/OS IME、干净目标机、用户安装或发布。真实Qt事件回放不等于物理鼠标验收。没有独立测冷缓存/峰值内存；作者逻辑磁盘字节与单次暖启动数据只按其测量口径引用，不称新增物理占用或性能保证。

最后查看PR时base/head匹配，rules-context与desktop-environment成功，双平台foundation仍运行、native-case skipped；不称必需CI全部通过。R01已回传规划窗口交原开发最小修复，N01可同次同步。原定矩阵已收束，所有本审窗口与任务已结束，不再扩扫；新候选仅复审修复/受影响边界并沿用未变矩阵。原失败结论绑定47c8d08保留，作者树仍由原窗独占，审查者不合并或释放它。
