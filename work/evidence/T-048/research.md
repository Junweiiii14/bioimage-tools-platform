# T048 离线安装依据（2026-10-19）

- 当前锁定 PySide6/Qt 6.12.0。Qt 官方 [6.12 支持平台](https://doc.qt.io/qt-6.12/supported-platforms.html) 指定 Windows 10 1809+、x86_64；不因用户版本未知而静默支持更早系统。Inno 使用 `MinVersion=10.0.17763`、`ArchitecturesAllowed=x64os`，不改依赖锁。
- ONNX Runtime 官方 [安装说明](https://onnxruntime.ai/docs/install/) 要求 Windows VC++ 运行库；[Windows 说明](https://onnxruntime.ai/docs/get-started/with-windows.html) 列出 Win10 1809+。Microsoft 官方 [本地部署](https://learn.microsoft.com/en-us/cpp/windows/deployment-in-visual-cpp?view=msvc-170) 允许运行库随应用目录分发，提醒本地版本需随应用维护。
- 最小实现：复制固定 Qt wheel 自带 MSVC140 DLL 到私有 python.exe 目录，保留各 wheel 自带副本和许可证；不从宿主 System32 抓取 DLL、不安装全局运行库、不下载目标机依赖。manifest 记录十个 DLL 摘要。
- [Inno MinVersion](https://jrsoftware.org/ishelp/topic_setup_minversion.htm) 对低于最低版本的系统报错退出。实际 ISCC 6.7.3 编译接受上述系统和架构限制；没有旧 Win10 实机拒绝路径实测。
- `.local/t048/final-import-audit.json` 使用现有 MinGW objdump 扫描581个 PE 的静态导入名。四个未使用的 Qt SQL 驱动另依赖 Firebird/Mimer/Oracle/PostgreSQL 客户端；产品没有 Qt SQL 功能，不将其归为已支持功能或软件前置条件。此扫描不证明所有延迟加载路径或 Win10 API 兼容。
- 真正使用路径由安装后 GUI/worker/OCR 验证补足：MSVC 实际加载来自应用内，开发目录不参与。宿主 Win11、宿主操作系统 API 与驱动仍参与；不能据此推断干净 Win10 全验收。
