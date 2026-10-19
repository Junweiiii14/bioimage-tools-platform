# Windows 候选安装版：来源与最小实验

访问日期2026-10-19。问题：完整 WebEngine/WB/OCR 软件能否独立于开发目录与 Python 安装运行，并与旧版并存？

- 现有锁定构建器 Nuitka 4.3 / CPython 3.12.14 / PySide6 6.12.0。沿用完整 standalone；不继承 P0 排除 scipy.signal 等科学依赖的配置。官方说明 standalone 可独立于本机 Python；PySide6 官方部署工具同样基于 Nuitka。来源：[Nuitka manual](https://nuitka.net/user-documentation/user-manual.html)、[Qt pyside6-deploy](https://doc.qt.io/qtforpython-6/deployment/deployment-pyside6-deploy.html)。文档不等于本产品部署已通过。
- 外层安装器 Inno Setup 6.7.3，固定官方发布资产，由官方下载页链接到 GitHub `jrsoftware/issrc` 的 `is-6_7_3/innosetup-6.7.3.exe`。仅 ignored `.local/t047/toolchain` 保存；SHA256 `9c73c3bae7ed48d44112a0f48e66742c00090bdb5bef71d9d3c056c66e97b732`，本机 Authenticode Valid、发行者 Pyrsys B.V.。编译器已在该工具目录安装，未创建工具图标。来源：[官方下载](https://jrsoftware.org/isdl.php)。本机安装的 License.txt 允许使用/再分发并保留声明；构建工具不随产品分发。
- 安装器选用 `PrivilegesRequired=lowest`，独立 `AppId=BioImageTools.WB.Candidate` 和当前用户程序目录；明确桌面/开始菜单任务，不关联 TIFF，也不结束旧实例。来源：[PrivilegesRequired](https://jrsoftware.org/ishelp/topic_setup_privilegesrequired.htm)、[AppId](https://jrsoftware.org/ishelp/topic_setup_appid.htm)、[Icons](https://jrsoftware.org/ishelp/topic_iconssection.htm)。
- 完整包包含项目包、WebEngine及网页资源、ONNX OCR模型、依赖许可与绑定提交的源码归档。锁定OCR只有ONNX引擎，未安装的其他推理后端不作为产品能力。构建清单保留源码提交、锁摘要、命令、退出码与安装器摘要。

最小实验：源码态 `--verify-installation` 用临时生成的16位TIFF经真实宿主/worker提交两泳道结果，离线加载OCR，核验原始字节未改并退出；v3报告passed、6.422秒、进程exit0。v1/v2诊断请求缺少当前项目/选择绑定而失败，未将失败当作成功；源码实验不是安装态证据。

最终采用内置运行库方案，完整AOT未通过真实启动/OCR验收，不作为交付。uv 管理的 Python 来自 Astral python-build-standalone，见[uv 官方说明](https://docs.astral.sh/uv/concepts/python-versions/)及[独立运行库文档](https://docs.astral.sh/python-build-standalone/)。本轮未升级运行库，复制已验证的同一 CPython3.12.14并记录二进制摘要，安装锁导出的产品依赖及四个wheel，保留运行库许可。`-I` 隔离工作目录/用户site，语义见[Python3.12命令行](https://docs.python.org/3.12/using/cmdline.html)。固定路径原生启动器转发参数与标准流、透传真实退出码，Job对象仅包含其创建的进程树，语义见[CreateProcessW](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessw)及[Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects)。

最小实验已落到实际安装：b6df40e包态正常Windows窗口七检查通过，真实OCR子进程识别Fig1A/AKT、定量协议退出码通过；无剩余所属进程，316个加载模块未出现开发环境路径。桌面/开始菜单/卸载入口与原图/旧快捷方式摘要核对。实际快捷方式已启动响应正常的用户候选窗口。细节与限制见T047 validation，历史AOT初始化exit3仍UNKNOWN；没有将网页预览或源码检查当成安装态成功。干净Windows、多DPI和物理关闭按钮仍未验收。
