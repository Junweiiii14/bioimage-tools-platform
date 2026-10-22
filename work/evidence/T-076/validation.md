# T076 检查记录

最新基线 T075 `7fcb8192ada7acf5695e74f23cbe010ffd862966`；当前产品 `d3aff15d53bf04c822976af0dd6b261f2b4dd6a1`。活动分支 `codex/t076-platform-home-scroll`。Windows 11、Python 3.12.14、uv 0.13.0、PySide6 6.12.0 / Chromium 140.0.7339.225；以下网页检查使用 Qt offscreen，成功回归使用 `QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu`、`PYTHONUTF8=1`。

## 已运行

| 命令 / 范围 | 结果与原始证据 |
|---|---|
| `uv run --locked --no-sync pytest tests/test_platform_home_scroll.py tests/test_project_navigation_session.py tests/test_intake_web_ui.py tests/test_workbench_appearance.py -q --tb=short` | 最终产品 56 passed / 37.80s / 0，`.local/t076-final-regression.log`。含 1440×900、960×640、1440×960 zoom 1.5、末格真实命中、保存可达、返回双轴位置与焦点、科学状态不变、草稿保护、四主题与已有曲线编辑。 |
| 同范围首轮稳定回归 | e7eb3a2 实现阶段 51 passed / 34.38s / 0，`.local/t076-regression.log`；不代替最终 56 项。 |
| `pytest tests/test_project_navigation_session.py tests/test_platform_home_scroll.py -q --tb=short` | 修复后 18 passed / 15.23s / 0，`.local/t076-review-fix-tests-v2.log`。四种首页导入组合保护草稿，一条实际确认新建；连续快照仍定位可编辑输入。 |
| 独立代码复审 | d3aff15，21 passed / 19.06s / 0，包含审查者原始反例；Accepted。见独审报告。 |
| `uv run --locked --no-sync ruff check .` / `ruff format --check .` / `pyright` | 检查通过；最终 Python 格式由提交钩子再次确认；Pyright 0 errors / 0 warnings / 0。无 ignore、skip、timeout 或预期容差削弱。 |
| `uv run --locked --no-sync python -m tooling.capture_workbench --assets apps/desktop/src/bioimage_app/web_ui --output .local/t076-visual-settled --platform-home` | 12 张完整截图 / console 空 / 0；本地 Noto 加载。入场动画结束后采样。源截图 e7eb3a2，d3aff15 只改变会话与定位逻辑，视觉审查者明确确认原静态结论仍适用。 |
| 有界视觉独审 | `ship`，只涵盖提供的稳定截图，详见 `visual-review.md`。6 项局部字号/几何端头 advisory 不构成 material issue。未改全局设计世界。 |
| `uv build --package bioimage-app --wheel --out-dir .local/t076-wheel` | d3aff15 wheel 构建 / 0；36 个前端文件在源码、wheel 与桌面预览副本逐字节一致。清单 `preview-resources.json`。 |
| `uv run --locked --no-sync python .local/t076_bundle_smoke.py` | 0，`.local/t076-bundle-smoke-v3.log` / `bundle-smoke.json`。实际双击入口的 file 重定向、字体、平台/WB 指针反馈、命中区域稳定、快速往返最终状态、10×18 末格命中均通过。是程序化事件，不是物理延迟/60fps 证明。 |
| `git diff --check` 与提交钩子 | 0；Ruff、format、repository policy 通过。 |

## 初次失败与修正

- 初次未禁用 GPU 的已有 32 项检查：30 passed / 2 failed / 34.01s / 1。角度测试 canvas 未绘制，Qt D3D/Skia mailbox/context lost；曲线测试初次失败后单项 1 passed / 2.16s。保留原输出，不认定原生根因已修复。后续禁用 GPU 的成功不能推广硬件渲染稳定。
- 新四项初次失败：测试选择器错误及真实矩阵宽度错误，修正既有字段选择器与 grid `width:max-content` 后 4 passed / 6.42s。未放宽可见/命中断言。首命令末尾输出日志掩盖外层退出码，实际 pytest 失败仍按 1 记录。
- e7eb3a2 独审 Changes requested：主页独立导入向旧项目追加；连续快照替换 DOM 后定位请求丢失。原反例失败保留 `code-review-e7eb3a2.md`，d3aff15 修复并由原审查者复验。
- 新首页测试第一轮 4 failed / 14 passed / 34.99s：仅等待原生存储 ready 就注入草稿，前端首个 route 尚未完成并会清空测试草稿；改为等待实际页面 `mode=quant` 再造草稿及断言草稿存在。没有延长现有超时或改变产品答案；第二轮 18 项通过。
- 本地新 smoke 第一/二次失败：脚本两个顶层 JS 求值重复声明 `const r`，WB 指针事件未执行；用局部 IIFE 修正测试脚本，未改产品。第三轮通过、console 空。原日志仍保留。
- 最初静态主题图捕获到半帧，未作为验收；仅诊断工具在静态采样前结束动画并等待 compositor，重新采集 settled 12 图。产品未为截图削减动效。
- 编写检查阶段的格式、导入、行长和新测试 monkeypatch 类型错误已按规则修复；未添加忽略或改门禁。

## CI 与交付边界

最终证据提交推送后须等待当前 HEAD 的 Windows / Linux foundation、desktop-environment、rules-context 四检查。结果落 `.local/t076-final-ci.json` 并复制桌面交付目录；成功前任务不完成。没有将旧 T075 CI 替代本轮。PR 基于最新 `codex/t075-ui-system`，不自动合并。

桌面预览 `BioImage-平台首页预览-T076-d3aff15` 使用合成数据，不执行科研重算。没有新安装器或替换安装；原 T075 5c56f55 候选保持。干净 Win10、物理 DPI / IME、科学留出及历史 Qt/D3D/native UNKNOWN 继续保留。≤800px 单列源码存在，高缩放行为回归覆盖有效窄内容区，但本轮静态截图只覆盖 960 / 1440。
