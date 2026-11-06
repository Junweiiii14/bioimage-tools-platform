# P022 最终增量独审：pass（本任务工程范围）

2026-11-06，独审窗口 `01a1af0d-808e-7131-ae29-237aded27938`（local）。PR74：https://github.com/Junweiiii14/bioimage-tools-platform/pull/74。

- reviewed base：`2a3c7a32936c6e4daf63dac23fb953cc4512e840`
- reviewed candidate：`47ded5e5e3ef01afadadf2b9a76e9c59cbb8ed69`
- 增量起点／首审候选：`47c8d08730dce974ba3d2d4488e8e032dede2ad3`
- 独立树：`C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-review-p022`，最终detached准确候选、tracked clean。未修改作者树、产品、原图、历史或用户安装。

**pass**：本任务的三个已知工具可选装配、重启启停与缺包历史边界，在已声明工程范围内通过。原P022-R01与非阻断N01均关闭，无剩余实质问题。此结论不代替准确候选必需CI；不代表热插拔、任意工具免修改接入、科学准入、真人或安装交付完成。

首审 `.local/independent-review-47c8d08.md` 的changes_required保留。最终产品增量只有 `web_window.py:481` 在 `start_from_images` 任意状态写入前检查 `tools.require("wb")`；没有补偿状态框架、额外依赖或算法变化。其余为新增反例及证据驱动同步。未改弱旧测试、容差、skip、锁或门禁。

## R01 关闭：真实缺包／停用时拖放不再阻断剩余工具

独立构建本候选app wheel，新建两个仅本审查使用的venv：`.local/ui-r01-final/bca-only-env` 实际无WB包，`.local/ui-r01-final/wb-disabled-env` 实际安装WB 0.19.0与BCA、启动设置停用WB。未修改首审矩阵环境；未变contracts/runtime/WB/BCA wheel只读复用首审构建。安装来源、wheel摘要、全部准备命令及exit0见 `.local/ui-r01-final/preparation-receipt.json`。

自写独立探针直接使用已安装的WebWorkbenchWindow、Qt/WebChannel及真实BCA worker，无pytest、源码树模块导入或计算mock。发送实际QDragEnterEvent/QDropEvent到页面WB卡DOM坐标，经过真实native回调。两例均观察到：

- Qt事件成功投递，宿主明确提示“WB未安装”或“WB已停用”；保持 `stage=idle`、`_starting=false`，跨越多次150ms轮询后 `sys.excepthook` 异常列表仍为空。
- 随后从BCA实际界面选择CSV和板记录，真实worker取得PID、完成正式提交；独立read_result验证成果与部分样本状态，没有把缺失值转成零。
- 原CSV/record、拖入目录及首审WB历史91个文件（含数据库）的逐字节摘要不变；两个窗口正常关闭并销毁。

实际命令（环境变量 `QT_QPA_PLATFORM=offscreen`、`QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu`）：

| 命令 | 结果 |
|---|---|
| `.local/ui-r01-final/bca-only-env/Scripts/python.exe -I -B .local/ui-r01-final/installed_drop_probe.py wb-missing wb-missing-final` | exit0 / 5.95s；真实run `65e3c22d68fe44cd97d06dc3728dd22f` |
| `.local/ui-r01-final/wb-disabled-env/Scripts/python.exe -I -B .local/ui-r01-final/installed_drop_probe.py wb-disabled` | exit0 / 5.45s；真实run `40ae7a8724b64d56b0164a3ae95b282a` |

结果分别在 `.local/ui-r01-final/wb-missing-final/report.json` 与 `wb-disabled/report.json`，原始日志同名`.log`；子审汇总见 `.local/ui-r01-final/receipt-47ded5e.md`。两份已安装web_window源码与准确候选经换行归一化后完全一致。前述事件回放证明本次入口/状态修复，不等同物理鼠标或真人验收。Qt GPU/fallback及事件构造弃用警告保留。

首轮新探针使用QTest.qWait，drop部分已正确，但随后BCA结果等待30秒超时、关闭15秒未排空，进程实际退出码为 **-1073740791**（Windows无符号3221226505）；该轮不计为通过。原脚本 `installed_drop_probe-first-attempt.py`、`wb-missing/report.json`、`wb-missing.log`保留。仅将探针等待改为独立QEventLoop后，同产品、同输入、同30秒阈值的两例通过；未改变产品、断言或放宽超时。不能把此探针调整解释为历史原生退出/GPU问题已解决。

## 有效路径与其他增量检查

1. 独立开发venv Windows CPython3.12.14 / PySide6 6.12.0，offscreen，`--disable-gpu --disable-software-rasterizer`。命令 `.local/reviewer-venv/Scripts/python.exe -I -B -m pytest -q tests/test_optional_tools.py tests/test_folder_drop.py tests/test_bca_web.py`：**exit0，15 passed / 31.49s，11条Qt事件构造弃用warnings**。覆盖有效WB目录拖放/缩放、缺失与停用反例、BCA真实运行；日志 `.local/final-47ded5e-pytest.log`。
2. **N01关闭**：`run_matrix.py`的disabled场景使用前一all进程的实际 `configuration.name` 作为settings_name，并设 `preserve_settings=True`；不再重写开关。静态核对其与desktop_probe的命名空间规则一致。未重跑整套矩阵；首审已独立验证同一持久设置方式。
3. 准确base/candidate `tooling/rule_context.py check` **exit0**；增量 `git diff --check 47c8d08 47ded5e` **exit0**。
4. 工件索引31条大小与SHA全部独立核对一致，exit0；作者新增两份真实wheel反例均ok，无errors，作为只读核验，与本审实际执行明确区分。
5. 增量diff完整核对：唯一产品行如上，保护的算法/API/权重/参考、依赖版本/锁、门禁无变化。新增测试未改动既有预期；证据probe增加Qt事件回放，不修改科学实现。

## 沿用与未验边界

首候选的13场景真实装配矩阵、18项回归、运行中设置/关闭返回检查、六种历史操作与未知身份反例，以及锁/门禁/第三方保护核验继续有效；具体命令、环境和限制见原首审报告。新head没有重跑未变科学或全矩阵，不将旧证据改写为本候选重跑。

科学/化学真值/LoQ/训练重叠、真人、物理DPI/OS IME、目标机、冷缓存/峰值内存、用户安装或发布仍未验；已完成历史的保护也不扩大为崩溃恢复时数据库绝不变化。作者跨修复运行的本机全量只作诊断，不能充当本候选准确全量证明。

最终查询PR74时base/head与本报告一致，OPEN；rules-context与desktop-environment成功，双平台foundation仍IN_PROGRESS、native-case SKIPPED。**不宣称全部必需CI通过。** 已向规划窗口回传本范围pass；上游继续核对准确候选CI终态后按正常PR集成，并负责交付记录及作者树释放。审查者不合并、发布或替作者释放工作树。纯收据归档只核diff，无需重复科学链。
