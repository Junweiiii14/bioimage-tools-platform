# T-025 平台入口验证

2026-10-15，Windows / Python3.12 / Qt6.12。

## 产品行为

默认入口现在打开 BioImage 平台；静态注册仅 WB 工具。新建/打开/最近项目使用实际 FigureProjectWindow 与异步存储；最近记录只在成功打开后保存，最多8个路径。不存在的工作区报错且不会写入历史。返回平台通过工具原有保存、取消、drain和closed信号完成，不强停线程。平台退出也等待工具完成关闭。--figure-project / --worker wb / --worker wb_ocr 保留，旧单图入口改用显式 --wb-manual。

## 验证

- uv sync --locked --all-groups：exit0，本地工作树独立venv。
- dev.py context --task T-025 --scope apps/desktop --scope tests --scope work --record：exit0。
- pytest tests/test_platform_host.py tests/test_figure_desktop.py -q（faulthandler_timeout=20）：exit0，12 passed in6.56s。
- Ruff三个改动Python目标：exit0。
- Pyright三个改动Python目标：exit0，0 errors。
- dev.py policy：exit0，扫描86产品文件。
- Qt渲染实际平台首页1380×880与1100×780：无截断；截图在本worktree .local/platform-preview/platform-{1380,1100}.png。DPR1.5，无预置实验原图或结果。
- Impeccable detect：exit0，仅新hub字号与圆角不在旧WB DESIGN标尺中的advisory。新hub标题23/26/22px、分区15px、工具面12px圆角和按钮6px圆角为有意分层，交由主代理记录设计系统；不把advisory当未运行。

## 集成依赖与限制

FigureProjectWindow需由主代理提交workspace_opened=Signal(str)、workspace_path只读属性、_list_documents成功_done后emit。以上测试使用该8行同等合同的临时本地补丁，未将figure_window.py纳入本子任务提交。主代理已经并行实施该合同，集成后应重跑测试。这里未验证WB新增自动化流程；全门禁和提交绑定独审由主任务统一执行。未修改主交接文件，交由主代理集中更新。
