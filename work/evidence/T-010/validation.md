# T-010 固定网格与原像素裁剪验证

2026-10-14，Windows/Python3.12.14/uv0.13.0，base379ffa2，feat/T-010-wb-crop-grid。

- `pytest tools/wb/tests/test_crop_grid.py -q`：9通过；整数余数/左右排除/非法数量、uint8/uint16/大端16位/MINISWHITE/RGB/RGBA/planar样本像素、位深/色度/alpha/分辨率、内嵌坐标与源摘要、无覆盖/错误SHA/越界。
- 新Qt用例真实拖出固定三泳道，保留中间空样本，后台从工作区导出原uint16，重开后坐标与稳定身份不变。初版测试未调用load_document导致超时，已修正实际用户操作，不放宽预期。
- 初次裁剪+桌面组合运行在该失败之后、旧test_desktop_draw_compute_save_reopen中原生Aborted，栈顶WBBackground._reply/replied.emit；没有捕获到原生原因。此为新的稳定性证据，不能用重跑覆盖。后续使用`-s`保存Qt原始日志，9桌面通过（11.23秒），没有重现该中止；仍需专项定位。
- GUI截图已实际检查，固定泳道、Marker排除、选择/坐标/导出入口可见；长表单可滚动，截图为合成图，私人位置在.local/requirements-review/grid-desktop.png。
- 最终`dev.py check --all`退出0：215测试（60.92秒）、Ruff/format/Pyright strict、9导入合约（72文件233依赖）、4隔离wheel/5场景。运行环境PYTEST_ADDOPTS=-s只禁用日志捕获以便诊断，未改变断言、skip/xfail/类型门禁；日志在.local/requirements-review/t010-full-check.log。
- 隔离WB安装实际调用固定网格/原像素裁剪；GUI/OCR两种worker入口和真实模型继续通过。uv.lock只有两个本地版本0.8.0/0.3.0更新，没有第三方依赖变化。

未验证：真实Marker/膜自动检测、整行模板合成、多原图项目、物理FAT、最终产品包/干净Windows、独立审查与远程CI。没有改动原图或输入资料，没有将预览图用于定量/裁剪。
