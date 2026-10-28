# R02 TIFF 解码前准入

基线c55a157（产品cb5f2c6）；Win11/CPython3.12.14/tifffile2026.9.20/NumPy2.5.4。使用小合成数组及受控头部，不做实际OOM。科学源/合成基线文件未修改。

## 改动与范围

公共定量/预览/OCR TIFF入口先检查维度、dtype、通道、排列、方向和单页，再按可配置像素及估算内存预算准入。内存考虑原解码、RGB uint32及表达式临时量、不可变副本/OCR、padding tile/strip、压缩分组；锁定一个解码worker。原值裁剪第二次读原通道及写后验证也使用准入，原样发布、SHA和无覆盖保持。

版本化操作政策/默认依据/限制见`docs/contracts/wb-tiff-resource-admission-v1.md`；调研见`docs/research/2026-10-28-tiff-resource-admission.md`。没有改变公式、位深、ROI、MINISWHITE、BT.601、项目schema或模型。

## 验证

- 首组16例在c55a157旧码全失败，exit1/4.19s，均到达禁止asarray探针：`r02-red.txt`。修复首轮含现有像素/原值裁剪42 passed/3.67s/exit0。
- 最终受影响集：`uv run --locked --no-sync pytest tools/wb/tests/test_tiff_admission.py tools/wb/tests/test_input_profiles.py tools/wb/tests/test_crop_grid.py tools/wb/tests/test_png_ocr.py tests/test_wb_background_terminal.py tools/wb/tests/test_ocr_protocol.py -q --tb=short`：**101 passed / 19.24s / exit0**。
- 新39个纯输入案例：uint8/uint16、灰/RGB/RGBA/planar、两入口压缩巨幅头部、4种不支持dtype、通道/体积/多页、巨型tile/编码字节声明、内存精确阈值、14配置错误及裁剪重读拒绝。真实WBBackground新增预览拒绝后正常小图、pending和关闭验证；原20终态例保留。
- 既有mean/profile积分、原值裁剪七模式（含big-endian/MINISWHITE/planar）、原始SHA/通道/位深/不可变性、PNG/TIFF OCR及真实OCR进程身份/取消均通过。Ruff检查/格式、严格定向Pyright均0。
- 新RGB五通道反例初次没指定contig，tifffile将其解释为四通道planar合法图，1失败38通过；修正fixture明确contig后测试实际不支持5通道，未改产品规则或放松断言。

## 旧完整运行与GPU对照

462aa4e发起的完整门禁：静态检查/9导入契约通过；pytest **3 failed / 1310 passed / 1308.13s / exit1**，wheel阶段未运行。原始日志保留`r01-fullcheck-superseded.txt`。期间推进补丁/R02使运行失去准确提交一致性，不能当cb5f2c6或本项完整验收。OCR子进程取消失败只保留了指向tiff_input导入尾部的截断stderr，混合源码是可能原因，不伪称已定位；冻结源码的上述101项包含该真实进程例并通过。

另两例为rotation canvas等待超时，伴SKIA写失败和GPU context lost。固定源码复验受影响101+UI3：2失败102通过/38.88s，两个宽/窄canvas例失败，旋转handle例通过。新进程局部`QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu`复验相同UI3：**3 passed / 7.01s / exit0**，未改等待时限、断言、应用代码或全局环境。只支持软件渲染下当前回归通过，不认定硬件GPU根因已修复。

下一步：提交独审，最终冻结集成树运行全门禁（含wheel）。期间不再编辑该检查进程读取的源码。工程问题继续，不以旧失败或科学留出暂缺冻结其他条目。
