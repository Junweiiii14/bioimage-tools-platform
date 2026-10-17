# T-018 作者验证：CSV 与统一归档

2026-10-14，分支feat/T-018-project-result-archive；本轮从ba8a678继续。实现提交c5f5787；作者自验不是独立审查，整体WB Goal尚未完成。

## 实现与环境

wb-tool0.16.0 / bioimage-app0.11.0，Python3.12.14 / uv0.13.0；Qt6.12.0、NumPy2.5.4、Pydantic2.14.1、tifffile2026.9.20、Pillow12.3.0及OCR锁版本保持。uv.lock仅两个本地包版本变化，未增加第三方依赖、放宽测试预期/容差/skip/ignore/门禁。

源/OCR/归一化CSV复用XLSX表构建器，文字采用可逆text:前缀，数字与None分别保留。ZIP新增archive.json v2成员SHA/大小/角色、已核验请求/原结果和CSV/XLSX；旧manifest/PNG和原值TIFF保持。宿主先保存精确修订，通过AsyncStorage核对run并解析路径，后台重新读资产。坏结果逐行隔离，取消/关闭/代际变化和无覆盖发布保持。详细契约wb-project-archive-v2.md；独立审查、ZIP恢复和最终产品验收待办。

## 实际验证

命令在仓库根以 `uv run --locked --no-sync` 执行，除另注外退出0。

| 检查 | 结果 |
|---|---|
| pytest tools/wb/tests/test_project_analysis.py tools/wb/tests/test_figure_project.py -q | 30通过，1.12秒；原有数值/拼图回归 |
| pytest tools/wb/tests/test_project_archive.py -q（首轮修正测试夹具后） | 19通过，2.18秒 |
| pytest tests/test_project_archive_ui.py tests/test_project_measurements.py tests/test_figure_desktop.py -q -o faulthandler_timeout=20 | 27通过，41.93秒 |
| pytest tools/wb/tests/test_project_archive.py tools/wb/tests/test_figure_project.py -q（最终边界） | 35通过，2.07秒 |
| dev.py check --all（索引计入总预算前） | 363通过115.73秒、Ruff234文件、Pyright0、9合约、4wheel/5隔离安装场景，退出0 |
| dev.py check --all（最终） | 364通过113.15秒、Ruff235文件、Pyright0、9合约、4wheel/5隔离安装场景，退出0 |
| uv lock --offline / uv sync --locked --all-groups --offline | 退出0，仅本地版本变化 |
| git diff --check | 退出0；已有CRLF文件仅Git换行提示 |

新增25核心/4Qt用例；另扩展原有完整PNG OCR→保存重开用例，验证真实三次运行的统一归档、OCR和归一化CSV。覆盖4000/8000/16000、真0/空位/缺失/过期、显式配对0.5及相对1/0、重名标签、带引号/逗号/CR/LF/全角等号/前导零/已有text:、数字类型、损坏请求/结果/OCR/不匹配run/未提供证据、失败/取消/中断、成员和表预算、最终发布取消/已有目标、原像素/位深/资产原字节与每成员SHA。

Qt实际进程计算后，外部故意破坏测试结果资产，CSV/ZIP重新校验使该行不可用而第二源保持8000/16000/0；不使用已显示的旧缓存值。受控后台延迟验证取消/关闭/新草稿不发布，也不覆盖新名称。同步guard放在finally释放，超时走ValueError，未引入无回复AssertionError。独立wheel新增普通WB CSV API和ZIP索引逐成员摘要，原隔离/真实OCR/PNG worker场景保持。

## 失败与复核记录

- 新核心测试首轮8失败/11通过：测试夹具误把OCR行对象传给要求row_id的绑定函数，同时把pairs写成samples；修正测试构造以符合既有API，未改产品行为/预期，19通过。
- 类型检查指出新测试中的tifffile.imread宽重载、未标注lambda和从别模块访问非导出引用；改为TiffFile.asarray、显式Callable和定义模块导入，无ignore。新增公开API补入__all__，格式问题按Ruff修正。
- 首轮全门禁通过后自查发现archive.json自身未计入总容量/成员预算；改为经同一有界writer写索引。序列化时成员列表不含索引自身，继续避免自引用摘要；增加容量临界反例。因产品改动重新运行完整门禁，不重复测试来掩盖失败。
- 先前Qt原生Aborted及T-017停滞根因仍UNKNOWN，本阶段通过不能证明根因修复。

完整日志均ignored `.local/requirements-review/T018-check-all-before-index-budget.txt`、`T018-check-all.txt`。本阶段没有重新测真实实验准确率、外部Excel兼容矩阵、大项目性能或物理FAT，没有改动用户资料。合成/真实worker验证不是干净机最终包态验收。未执行独审/推送/PR/远程CI/main集成/发布。
