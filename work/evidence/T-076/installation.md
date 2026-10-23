# T076 用户验收后安装交付

用户验收首页样式并明确要求“直接改在软件里”。冻结候选 `971d860dec6686abfb72935bfdd22ab0c5b3e93f`，基于最新 T075；相比已审 UI d3aff15 仅调整安装器 T076 版本和说明，页面/字体/动效资源不变。既有 UISystemTest 通道、AppId、QSettings 与依赖锁保持。

## 构建与安装

- `uv run --locked --no-sync python -m tooling.build_runtime_candidate --ui-system-test --iscc <既有固定 Inno 6.7.3/ISCC.exe> --gcc <既有固定 t075-toolchain/mingw64/bin/gcc.exe>`：0。私有 CPython 3.12.14、四 wheel 和锁定 Qt/OCR；没有升级或另换依赖。构建清单见 `build-manifest.json`。
- 安装器 `BioImage-WB-x64-T076-Test-971d860dec66-Setup.exe`，383827013 字节，SHA256 `a01e4ee92dea2fa74b7f386160a266559727fa4adff23f5e0622c332e9efba65`。
- 安装前确认新目录不存在，执行 `/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /DIR="C:/Users/70236/AppData/Local/Programs/BioImage WB 界面系统测试版 971d860" /LOG=<.local/t076-install.log>`，`Start-Process -WindowStyle Hidden -PassThru -Wait` 返回实际退出 0。
- 同 AppId 的 Inno 默认会复用已注册目录；本次保留旧版依靠显式 `/DIR`，不宣称安装器自动按每版隔离。桌面/开始菜单入口和当前通道卸载注册指向新目录；旧目录不再是该通道的活动卸载注册。其他通道、用户原图/项目、旧预览均未删除。

## 实际检查

| 范围 | 实际结果 |
|---|---|
| 完整安装载荷 | 构建 app → 新安装 7782 文件逐 SHA256 一致，无缺失/变化，20.282s；旧安装 launcher/manifest/34前端共36文件抽样未变。旧整个目录未声称重新逐文件审计。 |
| UI 资源 | 源码 → 本轮 wheel → 安装 36 文件完全一致；包含原本地 Noto、SVG、CSS、JS，无安装专用样式。 |
| 安装私有运行库 | `runtime/python.exe -I .local/t076_installed_acceptance.py`，19 passed / 26.97s / 0；涵盖平台导航、四新建入口草稿保护、真项目切换、矩阵10×18/缩放/焦点、连续快照及四高级工具保存重开导出。仅借用源码测试/pytest，产品、worker、Qt均来自安装目录，完整模块来源保留在本地报告。 |
| 主链与退出 | Windows PowerShell 5.1 运行已安装 `selfcheck.ps1`，19 checks / 11.343s，报告 phase=passed 且外层实际0；真实worker、原像素、矩阵、输出重开、原图不变及所属资源/窗口回收。报告 `installed-selfcheck.json`；所有新安装目录进程在测试后观察为0。 |
| 固定渲染器对照 | 安装 Python -I 运行 `tooling/capture_workbench.py --assets <安装web_ui> --output .local/t076-installed-capture --platform-home`，12图 / console空 / 0。Win11 offscreen、disable-gpu、DPR1、1440×900/960×640。 |
| 对照结果 | 10/12逐像素相等；1440的matrix-last/editor各19像素不同，范围x1197–1252/y11–13，最大RGB差2，仅圆角文件按钮上边缘。所有文字、尺寸、字体、状态records一致。保留原始差异，未修改图片、未改CSS、未以容差掩盖字体替换或布局差异。 |
| 用户实际启动 | 从新安装 exe 启动，初始记录 launcher32928 / Python13036 / Qt18456，Python HWND656338，标题“BioImage · 工具平台与 WB 界面测试版 T076”，Responding=true；这些是用户可见实例，保留运行，不算测试泄漏。 |

原始日志在 `.local/t076-{build,install,installed-acceptance,installed-capture,installed-selfcheck}.log`；静态图位于 `.local/t076-installed-capture/`。有限静态视觉结论与运行验证各保留范围。新安装仍记录 GLES/mailbox stderr；通过不证明历史 native/GPU 根因消失。干净 Win10、物理DPI/输入延迟/IME、科学留出不在本轮证明范围。

## 入口与最后闸门

桌面现用 **BioImage WB（界面系统测试版）** 已指向新候选；交付目录 `C:/Users/70236/Desktop/BioImage-工具平台-T076-971d860` 含相同安装器、`启动 BioImage.lnk`、说明、首页截图及验证。已批准 HTML 保持在原 `BioImage-平台首页预览-T076-d3aff15` 文件夹。PR37 保持草稿，不合并/公开发布。

代码独审绑定 d3aff15，包装元数据及安装交付独审绑定971d860，安装结论 **Accepted**；见 `install-review-971d860.md`。审查者独立复核载荷、旧样本、资源、真实快捷方式/注册、截图像素与正在运行的用户窗口。最终提交含跨窗口测试启动等待修正及证据，产品和安装资源与候选相同，无需重建。最终 HEAD 的四必要 CI 必须成功，不能沿用被后续授权变更取代的893e0ad运行（quality被新提交自动取消）或旧T075结果。最终在线事实记录 `.local/t076-final-ci.json` 并复制两个桌面交付目录；全部完成后无需为纯状态再提交以重启CI。
