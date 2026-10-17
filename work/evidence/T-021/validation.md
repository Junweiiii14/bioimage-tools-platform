# T-021 主集成验证

- 日期：2026-10-15（Asia/Shanghai）；Windows/PowerShell、CPython3.12.14、uv0.13.0，锁定Qt6.12/Pillow12.3.0等依赖。
- 主工作树：C:/Users/70236/.codex/worktrees/t021-coordination/bioimage-tools-platform；分支codex/t021-coordination。
- 产品提交：1e6cd5ab02968dc7493b2cecc5b3625564f23b8d；整轮base bb5601addda64fa96fa007612ceda0a0e1ed9b74。原主目录既存产品改动保留。
- 三个子任务各有独立worktree/venv并提交后集成；解码和兼容证据见本目录专项文件，模板后端测试随产品提交。

## 实际检查

| 命令 | 退出码/结果 |
|---|---|
| `uv sync --locked --all-groups` | 0；建立独立venv |
| `dev.py context --task T-021`（tools/wb、apps/desktop、tests、docs、tooling、uv.lock、work、.agent-handoff） | 0；读取输出；更新module-map后再生成回执 |
| `uv lock --offline`及`uv sync --locked --all-groups` | 均0；只更新wb-tool0.19.0/app0.14.0两本地版本，无第三方变更 |
| `uv run --locked --no-sync pytest tests/test_figure_template_ui.py tools/wb/tests/test_figure_template_io.py -q -o faulthandler_timeout=20` | 0；26通过，6.98s（18后端、8桌面） |
| 截图检查：模板跨工作区桌面用例及`tests/test_laboratory_layout_ui.py` | 0；3通过，18.75s；模板和分段原生Qt截图已查看，常用1300×950逻辑窗口，当前系统缩放；非DPI矩阵 |
| `uv run --locked --no-sync pyright` | 0；0 errors/warnings |
| Impeccable scoped context及`detect --json`两修改UI文件 | 均0；沿用现有Qt Operate界面，检测[]；Python文件检测不代替截图/Qt测试 |
| `uv run --locked --no-sync python dev.py check --all` | 0；490通过/174.80s，Ruff274文件、Pyright0、9合约；4wheel及4个隔离环境通过 |

完整门禁在主集成代码完成后启动，运行中仅提交相同代码及更新文档/规则回执；受测产品代码与1e6cd5a一致。已安装wheel实际执行schema7读写/渲染和模板公开API往返，普通WB安装不加载Qt/存储，完整宿主真实OCR/PNG路径通过。

## 行为与限制

模板只含通用设置/字体；旧style=null保留旧模式。实际跨工作区导入字体、新建空项目、保存旧项目、重开及目标字体渲染通过；取消/关闭/新编辑和保存完成后状态变化均拒绝晚到替换。旧schema1–6与bb5601a独立实际产物像素/完整manifest一致；schema7定量/OCR关联/归一化和ZIP恢复保持。重复解码用调用计数和逐源释放验证，不是实际大图性能基准。

主线初次Ruff报告两处新长行，格式化后通过；集成产品测试无失败。子任务初始夹具/预期纠正见各自证据。无已有断言/容差/skip/xfail/type-ignore放宽。installed_wheels仅增加schema7/模板验收，未删除门禁。

源码Qt截图保存在主worktree的.local/qa/T-021/（合成样本）。未新增真实科学准确率、人工真值、真实实验配对、大项目性能、DPI矩阵、FAT/断电、最终Windows包态、干净机、远程CI或发布证据。旧Qt中止/停滞根因仍UNKNOWN，本次通过不将它们标记修复。独立审查见independent-review.md。
