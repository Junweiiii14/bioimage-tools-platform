# T081 安装态真实恢复发现与修复

P4源码81d8d87已独审Accepted、四required成功并经PR42正常合main b59123e；Linux1291/442.16s和Windows1291/620.87s及全部wheel完成。初1eb的Windows2fail和Linux20min取消均保留；Linux停于旧WBWindow QObject退休，非本次算法改动，原生原因UNKNOWN，后继通过不当作根因修复。

R1构建/实际升级exit0、用户哨兵保留、7793载荷/209源码SHA匹配、随包双模式自检、163安装态加载模块来源/摘要和33项有限验收通过。**这些窄检查未覆盖全部恢复图片的可读性**：查看真实恢复结果页截图后发现18辅助源缩略图失败，独审进一步确认9原值裁图及4Fig图片也被重映射成`source.json`。因此R1产物独审Blocked，不能据33 passed宣称完整交付通过；旧201成员stage/ZIP及所有收据保留在ignored `.local/T081/package`，未发布桌面安装包。

根因：`archive_restore._assets`只把当前`rows.source`归入TIFF，遗漏明确声明的`intake.sources`、`intake_crops.raw_crop`和`intake_figures.image`。原始字节/SHA没有丢失，但默认.json使TIFF读取器拒绝，影响恢复后预览、改选来源及同组引导裁剪。修复仅依已有typed role恢复全部原图/原值裁图为.tif、Fig图片为.png；普通测量/输出metadata仍.json，不根据不可信文件名猜格式。SHA、size、TIFF单页/32MP/512MiB检查保持；PNG补充格式/CRC、32MP及512MiB解码预算。实现初稿额外64MiB PNG文件上限由root移除，避免新增未有契约的普通Fig文件限制；全局MAX_MEMBER仍512MiB，OCR原有独立限制未改。

环境：Win11/Python3.12.14，锁定uv环境，未升级依赖。新增`test_intake_archive_sources.py`通过真实导出→恢复验证选中/未选中原图、raw_crop逐像素/dtype/SHA一致，Fig PNG可读、JSON元信息保持；伪装成.json的typed TIFF及.tiff的metadata仍依角色处理；多页和超32MP TIFF、超32MP PNG仍拒绝。

- 修改前新四个反例：exit1，4 failed，`.local/T081/restore-auxiliary-tiff/red.log`。
- 最小实现与既有恢复回归：exit0，30 passed/6.05s，`green.log`。
- Ruff/Pyright最终0（新测试超长行/空set标注已修，无ignore/放宽），`lint-final.log`/`types-final.log`；diff空白0。
- root移除额外64MiB上限后，`uv run --locked --no-sync pytest tools/wb/tests/test_intake_archive_sources.py -q` exit0，4 passed/2.11s，`final-budget.log`；同两文件Ruff/format及handoff容量检查0。
- 开发源码真实UI重开旧180完整目录：`uv run --locked --no-sync python -X utf8 .local/T081/source_reopen_probe.py`（offscreen/disable-gpu）exit0，1passed/9.41s。增强断言验证27源TIFF可读、9raw_crop原值逐像素一致、4Fig.png、全部27缩略图缓存、源交付127文件SHA不变，`ui/source-restore-attempt2.log`及attempt2截图/收据。这是开发源码验证，不冒充R2安装态通过。首次直接pytest helper因common模块路径缺失collection exit2，未跑产品；wrapper显式加入本次helper路径后通过，原失败保留。
- 准确SHA、独审、必需CI及R2实际安装另按真实结果补录；尚未完成不记通过。

结果页黄色“上次执行未完整提交”与图片类型缺陷分开：既有`wb-intake-output-v1.md`明确导出中归档，重开将活动export标interrupted，保留已完成裁剪/测量，重试写新目录。这不是缺失裁剪越过门槛；说明书补充选择新输出位置后继续。旧私有180交付字节无需覆盖，修复读取器可直接正确恢复旧归档。

R2准备位于`.local/T081/package/r2`，保留R1原路径/摘要绑定；新安装态实际180恢复加强为全部27原图TIFF可读、9原值裁图逐像素、4Fig PNG及全部缩略图完成。随包仍只放合成练习，不放私有180图或截图；桌面独立私有项目WB-180-T081保持。
