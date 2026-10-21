# T074 固定提交安装交付

- 产品/构建源：569674a82e33（完整SHA见build-manifest），此提交增量独立审查Accepted。
- 构建：锁定依赖、独立SupervisionTest安装身份/设置目录，退出0；安装退出0。
- 安装包：.local/releases/runtime-569674a82e33/BioImage-WB-x64-T074-Test-569674a82e33-Setup.exe
- 安装包SHA256：94a5342d691faa0daf8519a36616be5b4caeb5bb80dd4d8deee41593b918da04；361770693字节。
- PS5.1 selfcheck调用安装目录exe --verify-supervision-installation，退出0；实际隔离runtime及site-packages，不是源码入口。
- 报告：C:/Users/70236/AppData/Local/BioImage-WB-Supervision-Test/Diagnostics/20261021-224135-cac5b623bb684fe3bb15d6709e97a32e.json
- 报告SHA256：ffdd14a287bd921584c5173c5f5aed033e6deacae3fd52fe5f45c68e7ff15291；phase=passed，10.875秒。

- top-fields-one-start
- no-human-crop-confirmations
- real-workers
- original-pixel-crops
- display-correction
- signal-direction-independent-of-guide
- missing-is-not-zero
- committed-output
- original-preview-replaces-thumbnail
- visible-gray-image
- visible-results-table
- automatic-navigation
- stage-barriers
- supervision-curve-grid-export
- safe-reopen
- grid-safe-reopen
- originals-unchanged
- owned-resources-closed
- owned-window-deleted

本流程使用合成uint16双Fig N4/N5；验证封底保存后的新测量提交、单Fig浏览不跳裁剪、单Fig导出、1列/17间距/反序网格持久化、PNG/TIFF全尺寸RGB一致及预览缩放一致、schema15重开与原图/旧输出不变。不代表科学真值/留出或干净Windows/物理DPI验收。

保留首054a163数组校验失败、9483ebc视图字段丢失失败及源码最小定位记录；仅据这些具体失败追加修复/重建/相关复验。没有额外环境冒烟、本地全量或无关压力测试。原T073及更早安装、旧dirty目录、原图和历史结果保持。

GitHub PR35提供最终HEAD的四个必需检查实时状态；不沿用中间提交成功，不绕过失败，不自动合并。
