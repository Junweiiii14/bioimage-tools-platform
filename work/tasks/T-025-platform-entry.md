# T-025 平台入口

状态：review（实现/作者自验完成，等待主任务集成与独审）

目标：默认启动真实工具平台，提供WB项目新建、打开、最近项目和安全返回入口；不将规划工具标为可用。

范围：apps/desktop/src/bioimage_app/platform_window.py、__main__.py、tests/test_platform_host.py、apps/desktop/README.md。

实现：真实项目窗口生命周期、仅成功后最近历史、打开失败保持原因、安全返回与关闭、旧命令兼容；静态单工具注册不从项目加载模块。

设计：继承冷白/青绿Operate视觉，左工具导航、中项目操作、右流程说明。用户已明确自主实现，无需再做候选轮。

验证：12项平台/桌面集成测试通过，Ruff/Pyright/策略检查通过，2个原生尺寸截图检查。详细命令、截图与待集成host信号合同见work/evidence/T-025/validation.md。全门禁/绑定独审由T-024主任务统一完成。
