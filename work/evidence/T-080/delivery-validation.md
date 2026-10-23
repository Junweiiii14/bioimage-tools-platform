# T080 命名项目交付与桌面接入验证

日期：2026-10-23；执行者：P4 实现子代理（作者自验，不算独立审查）。
工作树：`C:/Users/70236/.codex/worktrees/wb-lab-installer/bioimage-tools-platform`。
分支：`codex/t080-crop-evidence-plan`；基线 HEAD：
`2d2c9727ec93c7a625e46964696788f06f8f4834`。这些修改尚未单独提交，最终提交和独审由主任务绑定。
环境：Windows、PowerShell、项目锁定 `.venv`，Python 3.12.14；Qt 测试沿仓库 offscreen
环境，显式 `QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu`，与其他 Qt 验证串行执行。
未升级依赖，未上传原图，所有测试使用合成夹具与 pytest 临时目录。

## 已落实

- 新 `application/intake_delivery.py` 纯命名/版本化输出位置；内部清单 schema5
  用 legacy_schema_version 保持 v1–4 计算摘要与旧序列化。输出位置不进入数值输入。
- 新 `adapters/intake_delivery.py` 分阶段整理、裁图归位、完整封存和目录检查。
  Fig/蛋白中文目录在裁剪前真实创建，采集组所有原始图保留原字节；未分配来源单独保留。
  已完成原值 TIFF 与显示 PNG/TIFF 立即归位。辅助图仅按完整同坐标证据或完全重复
  SHA 裁剪；仅同尺寸白光图保留原图并记录未裁剪原因。
- 最终同目录包含按 Fig 输出、总拼图、总表、分 Fig 表、标准恢复 ZIP、原始运行及
  文件名映射和真实状态。沿用旧标准 ZIP/证据检查；分 Fig 表读取同次冻结运行副本。
- 桌面 `IntakeWorkflowSession`：worker 只读选择代 → 保存交付状态 CAS → worker
  建目录/整理来源 → 每次 raw crop CAS → checkpoint → 后续阶段；最终索引导入及
  CAS 后才完成。保存失败不创建目录，归位失败停止推进。全部批量文件 I/O 在 worker。
- 输出选择持久化，移动工作区后不写旧绝对路径；输出当前快照必新代。封存目录、名称
  分组或已归位裁图配方改变后另建代，旧目录不覆盖。快照提供 delivery 的目录名、
  工作区绑定、根路径和阶段，未封存重开不凭猜测宣告已整理或完成。
- 公开契约：`docs/contracts/wb-intake-delivery-v1.md`；新 WBJob 操作
  `intake_delivery_materialize` / `intake_delivery_finalize`。恢复目录 API 支持取消。

## 命令与真实结果

以下命令均在上述工作树执行，前缀为 `uv run --locked --no-sync`。

| 命令 | 结果 | 退出码 |
| --- | --- | --- |
| `pytest tools/wb/tests/test_intake_execution.py tools/wb/tests/test_intake_output.py -q`（早期兼容检查） | 18 passed，8.51 s | 0 |
| `pytest tools/wb/tests/test_intake_delivery.py tools/wb/tests/test_intake_execution.py tools/wb/tests/test_intake_output.py tools/wb/tests/test_intake_grouping.py tools/wb/tests/test_intake_sequence.py -q --tb=short` | 44 passed，9.11 s | 0 |
| `pytest tests/test_instrument_intake_desktop.py -q -x --tb=short --show-capture=no` | 34 passed，69.78 s；新增 CAS 用例加入前 | 0 |
| `pytest tests/test_instrument_intake_desktop.py::test_fixed_n_crop_run_review_original_asset_and_reopen tests/test_instrument_intake_desktop.py::test_delivery_configuration_cas_failure_never_creates_output_directory tests/test_instrument_intake_desktop.py::test_complete_intake_fig_is_saved_before_real_worker_and_restores_verified_runs -q --tb=short --show-capture=no` | 最新补强 3 passed，12.25 s | 0 |
| `pytest tools/wb/tests/test_intake_delivery.py -q --tb=short`（最终安全路径/同代续用/取消检查） | 8 passed，4.10 s | 0 |
| `ruff check <下列14个Python文件>` | All checks passed | 0 |
| `ruff format --check <下列14个Python文件>` | 14 files already formatted | 0 |
| `pyright <下列14个Python文件>` | 0 errors / warnings / informations | 0 |
| `ruff check / ruff format --check / pyright application/intake_delivery.py 与 test_intake_delivery.py`（最后绝对路径检查后） | 通过，无类型忽略 | 0 |

静态检查完整文件参数：

```text
tools/wb/src/wb_tool/application/intake_delivery.py
tools/wb/src/wb_tool/adapters/intake_delivery.py
tools/wb/src/wb_tool/application/instrument_intake.py
tools/wb/src/wb_tool/application/intake_workflow.py
tools/wb/src/wb_tool/application/intake_output.py
tools/wb/src/wb_tool/application/intake_result_table.py
tools/wb/src/wb_tool/adapters/intake_table_export.py
tools/wb/src/wb_tool/adapters/intake_output.py
tools/wb/src/wb_tool/application/desktop_data.py
tools/wb/src/wb_tool/ui/background.py
tools/wb/src/wb_tool/api.py
apps/desktop/src/bioimage_app/intake_workflow.py
tools/wb/tests/test_intake_delivery.py
tests/test_instrument_intake_desktop.py
```

## 验证含义及修复记录

1. 新后端用例验证：旧 wire/摘要保持；危险字符、保留名、重名、Unicode 和非法相对
   路径；真正配置阶段仅建目录/原图；之后成功裁图归位且另一 Fig 保持未完成；16 位
   像素与原 ROI 完全一致；全部组内及未分配来源；同尺寸白光不能裁图；匹配字节幂等；
   外来目录和篡改拒绝；续用未封存目录、修改裁图换代；部分/完整状态；分 Fig 表；
   标准归档恢复模型一致；成员篡改与取消检查。
2. 桌面补强用例通过真实 AsyncStorage/CAS 与 worker：选择外部中文输出位置，配置
   前不创建目录；执行准备保存后目录和两份原图出现，尚无裁图；第一行成功后原值
   TIFF 等于资产字节、显示文件出现，第二行与后续定量仍未完成；重开保留位置。
   CAS 注入失败保留原项目且连默认 outputs 都未创建。
3. 完整桌面用例真实运行两个测量子进程，Fig 先保存后测量；当前表包含 16 槽；
   恢复旧运行、另存新快照、迁移到新工作区后再次导出、旧 ZIP 字节不变均通过。
   这不代表科学准确率或最终安装器已验收。
4. 旧测试文件名改为新公开布局 `项目恢复.zip` / `灰度汇总.xlsx`；故障注入更新为
   `intake_delivery_finalize`。失败前已创建的命名目录应保留，因此故障断言分别检查
   目录存在和索引是否封存；未减少“不完成、不伪造成功”的断言。
5. 早期 33 项受影响测试曾有 2 失败：新测试把“初始化补齐已有成功裁图”误当无裁图，
   已改为真正未处理配置快照验证初始阶段；历史旋转夹具触碰新版原图边界，主代理
   已在旋转任务按真实边界修正并说明。后续 44 项全部通过。
6. 首轮桌面 9 passed / 1 failed：人为 259 字符限制拒绝嵌套较深的正常工作区；改为
   原生路径上限并保留真实文件系统错误后，完整 34 项通过。无静默截断目的路径。
7. 初始静态检查的长行、私有 helper 调用与测试 `tifffile.imread` 不完整类型均已
   修正为格式化、明确验证复制入口和 `TiffFile/TiffPage.asarray`；未添加 ignore、skip
   或 xfail，未削弱门禁。

## 真实素材暴露的 TIFF 元数据编码修复

主任务首轮真实 180/PNG 项目在首行原值裁剪已 CAS 后，命名目录显示 TIFF 归位失败：
`TIFF strings must be 7-bit ASCII`。日志 `.local/T080/real-project-first.log` 保留，
未把该轮写成通过。原因是 `load_tiff` 的饱和/转换等中文 `source_warnings` 进入
ImageDescription，原有 UTF-8 JSON 不符合 TIFF ASCII 标签要求。

只对 TIFF 做 JSON ASCII 转义，解析信息完整；PNG 继续保留原 UTF-8 JSON 字节，
使失败前已发布 PNG 可以同代幂等续写。未删警告、改中文名称、覆盖已发布文件或把
异常当作成功。新回归用中文原图目录/原图名称、实际 uint16 上下限像素触发中文警告，
验证 TIFF ASCII 可逆 JSON 与 PNG 内容一致、中文原名保留、原值像素/位深及原图
字节保持，并再次归位检查已发布文件字节不变。

命令前缀 `uv run --locked --no-sync`：

- `pytest tools/wb/tests/test_intake_delivery.py tools/wb/tests/test_intake_sequence.py -q --tb=short`：
  25 passed / 5.81 s，exit 0。
- 新夹具首轮因测试 helper 把中文 raw 资产名直接用作平台 ASCII asset_id 而失败
  （24 passed / 1 failed，exit 1）；已按真实存储契约用 ASCII 内部资产 ID/相对路径，
  外部输入目录与文件名继续中文，不放宽平台 schema。
- 本轮精确 5 文件 `ruff check`、`ruff format --check`、`pyright`：最终均 exit 0；
  参数为 `adapters/intake_delivery.py`、`application/intake_sequence.py`、
  `tools/wb/tests/test_intake_delivery.py`、`tools/wb/tests/test_intake_sequence.py`、
  `tests/test_instrument_intake_desktop.py`（前两项位于 `tools/wb/src/wb_tool/`）。

该修复后真实失败工作区的断点恢复由主任务执行，结果另记；本记录不预先宣告通过。

## 尚未由本子任务完成的集成工作

最终全仓门禁、提交绑定独审、真实私有素材 UI 验收、签发安装包与干净 Windows 安装
由主任务继续；本记录不声称这些已经通过。新目录封存后不可补写，部分快照重试需新代。
仅同尺寸不能证明白光同坐标；此类来源保持原图并明确未生成辅助裁图。
