# T-023 验证记录（候选与正式实现）

- 基线059d01b；分支codex/t023-ui-candidates；只新增候选HTML/JPEG/文档与交接，未改任何产品Python、依赖、schema或数据。
- Impeccable已在本会话加载，不重复context。新方向seed ef6e01a4 / Operate，已运行并读取；Taste在独立交付目录实际抽取quiet-instrument / seed1443278531。
- A/B由两个设计子代理独立写稿，C由主代理完成（第三位中止，未提交C文件）；均统一1440×900、内联CSS/SVG、无脚本和外部资源。不是已实现桌面功能。
- 使用in-app browser真实加载三个本地HTML并保存JPEG；三者实际1440×900。初次B/C截图处于默认视口，随后重拍正确尺寸，不以截断图交付。
- A/B首轮已目视检查；C曲线标签对比度不足，一批改为浅色标签后重拍确认。未运行独立产品代码审查、网页营销inspect或Qt功能测试，本轮没有产品代码变化。
- `impeccable embed-prompt --scan`：6 rasters，0 missing（3交付图及3选择页副本）。来源为本地静态设计稿浏览器截图，无AI生成图、库存素材、私有原图。
- 选择页http://127.0.0.1:63028/已可见三张完整候选，保留为deliverable；源码及截图交付.local/deliveries/WB-UI-candidates-20261015。该候选阶段后用户在聊天选择A，转入正式实现。


## A 正式实现 / 2026-10-15

- 产品提交：0d9aad94c8bd7a93f34a24163af4fabe8d017d56；base45e19854aefdc38dbe7def69b54f993d92de87f2。仅Qt交互与显示，未改科学算法、schema、依赖或门禁。
- 原相关流程33项48.73s通过；新增证据+workflow最终15项7.89s通过。独立绑定HEAD审查再跑15项8.13s，退出0，无可行动发现；见code-review.md。
- 首次完整门禁504项180.79s、Ruff295、Pyright0、9合约和4wheel隔离环境通过（退出0）；运行期间又增加staleROI回归及曲线注释，故该次不是最终HEAD完整证据，已重新运行最终门禁，最终结果见下。
- 原生截图逻辑1440×900/1100×780，DPR1.5，实际2160×1350/1650×1170。生成于独立合成工作区，真实计算两行结果、compose、refresh后逐页QWidget.grab；未调用被Esc停止的原生CUA。
- 建造检查2轮：首次发现定量整体scroll及重复chrome导致曲线/基线出首屏，一批压缩并确认。独立finish审查全部13图有效；要求补曲线数值刻度/图例/LR与安全seed引用说明，修后同尺寸重采，审查两项resolved，disposition ship只覆盖修复清单。详见visual-review.md。
- 截图来源元数据：impeccable embed-prompt --scan，13 rasters / 0 missing，退出0；截图在.local/deliveries/WB-evidence-20261015/screenshots。
- 演示源码/独立合成工作区/使用说明在.local/deliveries/WB-evidence-20261015；--show-only启动并写live.json，launch.stderr.log空。
- 未执行远程CI/PR集成/发布、真实科学准确率、物理DPI及干净Windows包态验收；既有Qt未知问题不因本次通过而关闭。

- 最终HEAD首次全门禁：2026-10-15 20:07:37开始pytest，20:12后仍停在约100用例，约4分钟无新输出、无子进程，未配置超时栈。只停止该pytest PID22592，门禁退出1。没有修改代码或弱化测试；以PYTEST_ADDOPTS="-o faulthandler_timeout=30"重新执行同一全门禁以获得诊断。原因UNKNOWN，不能用重跑抹去。

- 最终产品0d9aad94诊断重跑：`PYTEST_ADDOPTS="-o faulthandler_timeout=30" uv run --locked --no-sync python dev.py check --all`退出0；505 passed in173.57s、Ruff298、Pyright0、9合约、4wheel隔离环境及真实OCR worker通过，未输出超时栈。未改测试预期/容差/skip/门禁；新增5项测试。停滞根因仍UNKNOWN，保留风险。DESIGN.md及design.json已按最终源码提取核验。
