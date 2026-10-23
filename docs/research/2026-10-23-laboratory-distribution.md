# 实验室离线发行：兼容与清理依据

访问日期：2026-10-23（北京时间）。问题：最新两项整改如何交付给没有开发环境的实验室人员，并安全替换本机测试版？

## 选择

保留已经真实安装验证的私有 CPython 3.12.14 + 锁定四 wheel + Qt/WebEngine/OCR/VC 运行库配方，不升级锁、不重新采用失败的 AOT。新增实验室身份，稳定用户安装目录、快捷方式和自检；旧测试身份独立，卸载清理与新安装分开。

## 原始来源

- [Qt 6.12 Windows 支持](https://doc.qt.io/qt-6/windows.html)：x86_64 Windows10 1809+ 和 Windows11；本包仅 x64，不据 ARM 支持表推断本包支持 ARM。
- [Inno PrivilegesRequired](https://jrsoftware.org/ishelp/topic_setup_privilegesrequired.htm)：lowest 不请求管理员权限，适合每位普通用户独立安装。
- [Inno UninstallDelete](https://jrsoftware.org/ishelp/topic_uninstalldeletesection.htm)：禁止用全目录通配清理安装目录，避免误删用户文件。新安装器不设置此项；本机旧包使用自身卸载程序，再核对剩余数据。
- 私有运行库、许可证和启动器的既有来源见 [2026-10-19 配方研究](2026-10-19-windows-candidate-packaging.md)。编译器继续使用既有固定 Inno6.7.3/MinGW，不混入研究聊天新安装工具。

## 验收方法与限制

真实安装后限制PATH/用户site，检查模块均来自安装目录，运行合成灰度/OCR和两Fig主链、T077拖入/未审核导出回归；用全部安装文件摘要比对构建载荷，并执行卸载/重装。旧软件先盘点及保留用户数据/改动，再按解析绝对路径清理，过程单独记录。

官方支持范围是打包目标，不能替代干净Win10、每种物理DPI/显卡或科学真值验证。当前可用环境与最终结果只见T079验证记录；建议8GB/4GB为部署空间建议，不是本轮性能保证。构建时间/压缩使安装器摘要可变，按固定输入和行为可复现，不宣称字节级可复现。
