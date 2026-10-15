# T-030 平台入口与自动项目准备

状态：implementing。用户已批准 T-028；按 T-029 分工实施。
范围：platform_window.py、新 project_entry.py、相关测试。本分支不改宿主 figure_window、数值语义或设计文档。
契约：平台选择原图，调用宿主 start_project_from_images(paths, project_parent=None)；扫描与目录创建在后台，原图只读，不覆盖已有项目。
检查：待运行。

实现：平台移除右侧常驻说明，选择 TIFF 文件/原图文件夹直接委托宿主；保留打开/返回/最近项目，最近打开时间只表示实际打开，不冒充分析完成。保存位置默认 Documents/BioImage/Projects，可改父目录。扫描排除自有 workspace/outputs、符号链接与 junction，去重、取消和 512 图/4096 目录预算；目录分配仅建父路径，最终创建交由 Workspace。
验证：Windows/Python3.12.14，uv sync --locked --all-groups 退出0；pytest tests/test_project_entry.py tests/test_platform_host.py 9通过；ruff、scoped pyright退出0。截图 .local/t030/platform-1100.png、platform-1440.png（不提交）实际Qt，检查1100画面无截断，空态移至列表顶部。
设计检测：Impeccable检测已运行，报告新色板/28px/8px不在旧DESIGN中的advisory；这些是T028已批准重设计，根任务负责更新统一设计文档，不能以旧色板否决新设计。无浏览器DOM，不能宣称无障碍全通过。动效和宿主start_project_from_images由T029集成；本分支不独立宣称端到端新建自动化验收通过。
状态：implemented-awaiting-integration-review。未更改数值/schema/旧测试预期；独立审查由根任务绑定集成提交。

T029宿主集成测试补充（host f8cb05d，本树cherry-pick 5d4e406）：tests/test_project_start.py新增4个用户行为测试。初次运行退出1：3通过、1失败。取消扫描、无效TIFF不建项目/历史、原图目录重叠保护通过；中文来源名称/未指定蛋白的有效原图自动输出失败，实际错误“这些标签需要导入支持相应文字的TTF/OTF/TTC字体”，已报告根任务修复，未削弱预期。scoped pyright与ruff通过。等待字体/显示标签修复后复验。

字体阻塞复验：根修复348fb3e（本树efe7a46）将新导入行缺失蛋白标签表示为可移植的Unassigned，表示未知蛋白，不使用Source编号冒充身份，也不改变实验语义。测试对应明确断言该占位；保留中文原图目录和完整PNG/XLSX/status输出断言。pytest tests/test_project_start.py 4通过，退出0（2.88s）；pyright和ruff退出0。此前失败保留为发现与修复证据。
