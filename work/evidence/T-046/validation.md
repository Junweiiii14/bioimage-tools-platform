# T046 验证记录

环境：候选t045隔离worktree，Windows，锁定uv Python3.12.14，Qt离屏；base e78a14a。
原ResearchVault工作区、用户原图、原应用窗口/快捷方式未修改。私图及测试项目只在ignored `.local/t046/`。

- 首批数值/手动/冻结参考/schema：65 passed，22.26秒，exit0。
- Qt桥接/定量及峰边界：17 passed，35.86秒，exit0。
- 组审核首次两项因严格dataclass重建失败，修复为保留类型字段；重测2 passed，1.70秒，exit0。
- 新策略实际worker发现质量提示白名单未更新，3行被正确拒绝且无结果；补新策略明确标志及独立quality policy，不放宽未知标志。worker+组审核37 passed，7.17秒，exit0。
- Ruff check当前0；Pyright0 errors/0 warnings（完整检查后仍需看最终退出码）。
- `.local/t046/product_probe.py`第二次完整exit0：Fig1E12框/12曲线/4蛋白；33组合并135表格行；960px无横溢出；手动入口；保存审核后下一组；UB16框/16曲线。
- 同图ACSL4泳道3：历史41–84，新0–89；原始积分62.91→2776.89，保留边缘背景/位深复核提示。不是用户正在操作的草稿数值，不与截图98.43混淆。
- 初次产品探针因真实worker失败未完成，第一次截图不作成功证据。最终截图 `.local/t046/product-*.png` 来自通过的真实worker项目。

## 性能前后（同106行项目副本，12次采样）

| 路径 | 修改前 | 修改后 |
|---|---:|---:|
| Qt空闲publish中位数 | 91.995ms | 0.0052ms |
| 完整snapshot中位数 | 89.734ms | 39.220ms |
| 重复前端render | 395–603ms | 0.1–0.6ms |
| 项目恢复总耗时 | 17.516s | 11.594s |

日志：`.local/t046/baseline.json`、`after-final.json`。热缓存空闲路径不等于所有交互或整体计算速度；
前端首次构建仍有成本，科学worker总时长未宣称同比改善。Qt离屏GPU初始化诊断保留，不代表硬件交互验收。

## 交互与完整回归

- `.local/t046/interaction_probe.py` exit0：审核重开保留；修改封底后真实worker积分变化并撤销审核；忙时可切Fig；取消不跳回旧组，未完成行保持空；减少动效有效。
- 首次完整检查：755 passed / 3 failed / 520.12秒；Ruff、类型和9个导入契约通过，pytest后停止未进入wheel。外层uv返回4294967295，工具退出1；没有独立child退出记录，不能将异常外层数值解释为已定位原生故障。日志 `.local/t046/check-all.log`。
- 两处Qt回归仍寻找旧单泳道页的“全部曲线”按钮：按新默认先断言全组曲线，再点击保留的手动入口，原始20000/1000/800等数值、复制/撤销/保存重开断言保留；结果页的延迟关闭回归改为检查当前可见表格与质量说明。没有删除功能验证或加大等待容差。
- 第三处为document-v2 schema漏列新quality policy；补明确枚举并保留schema与模型完全相等断言。worker schema仅排序恢复原格式，未放宽数据验证。
- 修正后手动GUI单项1 passed / 10.16秒；三文件定向7 passed / 31.82秒 / exit0。
- 新完整 `dev.py check --all` 正在运行，启用既有Windows owned-child故障观察，日志 `.local/t046/check-all-final.log`。未结束不标通过。
- Impeccable单次detect针对新增JS/CSS，exit0，无primary findings；sidecar颜色/字号等advisory保留交独审，不改忽略规则。日志 `.local/t046/detector.json`。
- 独立审查与最终提交绑定结论待补。

## 独审修复轮

992c338 fresh reviewer disposition: fix，五项：跨组结果选择竞态、审核先于存储、恢复缓存缺结果键、曲线小字、窄屏Fig导航。独立数值/审核8项通过。

- 表格选择先同步目标行/泳道/区间，只发一次选择，目标组返回后定位编辑器。
- save新增可选待保存transform；审核回执不先安装view，编码/存储失败保持未审核；正常存储提交后安装并推进generation。
- 前端缓存增加已加载run ID与审核状态；同修订恢复成功、移除失败数据、再次恢复均重绘。
- 新标签至少11px，SVG按实际CTM缩放补偿到11px；390px导航标题独立行、固定组宽，单列曲线。截图覆盖同一文件，未改批准方向。
- 新三项Qt回归初次fixture漏拦源图文件选择且未建立正确持久化初态，出现等待/关闭失败和0xc0000409退出；没有采到精确原生故障栈，原生原因仍UNKNOWN。已修测试的源图适配隔离及持久化初始状态。没有调整产品关闭路径、测试超时或类型忽略；三项8.02秒exit0，随后连同独立手动入口4项9.17秒exit0。
- 首次相关14项1失败13通过，手动入口点击时页面busy尚未更新；测试明确等待可用按钮，保留全部数值/保存/原图断言。修正与新三项合跑4项9.17秒通过。
- 第二完整检查启用observer但未设UTF8；pytest至少一处上述入口时序失败，observer转发中文异常在GBK编码抛UnicodeEncodeError，外层exit1，未完成门禁。不宣称通过，第三轮将以UTF8环境保留完整诊断；未修改门禁脚本。
- Pyright最终0 errors/0 warnings，Ruff check/format与Node语法0。新测试用已有monkeypatch注入I/O故障，无新增类型忽略。
- 修复后真实私图整套探针exit0：12框/12曲线、所有刻度实际11px、33组135行表格、960/390无文档横溢出、手动入口、审核保存/下一组、UB16曲线。交互复测exit0：审核重开、修改失效、实际重算、忙时切组、取消均保留；取消文案明确“计算已取消”。


## 最终完成（2026-10-18 23:18）

- 产品提交4d4944a18877d10da4f2a7cef4bd4662ba4007a8。Windows / Python3.12.14 / Qt离屏，PYTHONUTF8=1及既有BIOIMAGE_WINDOWS_FAULTS=1；`uv run --locked --no-sync python dev.py check --all`自然结束exit0。
- Ruff check/format、Pyright 0 errors/0 warnings、9导入边界契约通过；**761 passed in 526.85s**，observer记录原pytest child exit=0/u32=0。全部隔离wheel、真实Qt关闭、PP-OCRv6/静态worker及TIFF/PNG来源检查通过，dev及外层exit0。日志 `.local/t046/check-all-release-candidate.log`。
- fresh独审绑定4d4944a的五项修复全部resolved、remaining clear、disposition ship（范围见independent-review.md）。documenter已核对并更新能力说明，DESIGN/sidecar未变。后继仅交付文档，不更改已检查产品。
- `Start-BioImage.ps1 --verify-launch` exit0，确认源码与界面均来自此候选树。原图SHA256最终仍为a2db16a4833db3116196968f22461e2b6d204f7d027c12e15881ae29885556d1。
- 本地任务完成；未替换旧版本/快捷方式、未关闭用户窗口、未push/main/发布。干净Windows/DPI/独立科学留出及历史原生UNKNOWN不因本轮通过销账。
