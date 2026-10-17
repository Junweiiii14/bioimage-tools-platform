# 文件资产与运行契约

公开入口 tool_contracts.api。不可变 Pydantic 严格模型：工作区格式、资产引用、
文档修订、运行记录、进程退出回执与恢复报告；机器 schema 从模型生成。
不含 WB/IF/IHC 参数，不加载 GUI、数值库或数据库，不在导入时访问工作区。

内部资产路径使用规范 ASCII 相对路径（显示名称保留在工具文档中），拒绝 Windows 设备名/别名；
数字不接受布尔或字符串强转；失败/中断须有原因，
只有 succeeded 可以引用结果。pid=0/code=None 表示宿主确认尚未启动；启动进程须有退出码。
退出回执由宿主 OS 生命周期观察产生，模型本身不能代替实际观察。

测试与隔离安装通过仓库根 `uv run --locked --no-sync python dev.py check --all`。
