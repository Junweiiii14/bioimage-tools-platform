# T080 验证记录（进行中）

环境：Windows本机，活动wb-lab-installer树、基线main2d2c972；locked uv Python3.12.14、Pillow12.3.0、tifffile2026.9.20。当前产品增量未提交、独审/CI/安装尚未完成。

| 阶段 | 命令/证据 | 实际结果 |
|---|---|---|
| 规则 | `uv run --locked --no-sync python dev.py context --task T-080 ... --record`，receipt见本目录 | exit0，涵盖apps/tools/tests/tooling/contract/handoff |
| 输入 | `uv run --locked --no-sync python .local/T080/inventory.py` | exit0，39源文件SHA，3PNG副本解码数组逐像素相同；未改原图 |
| 视觉诊断 | `.local/T080/focus.py`及本地contact sheets | exit0，已打开原素材/重点图；显示缩放只用于观察 |
| 旧公共API基线 | `.local/T080/baseline.py` | exit0，21来源变体case仅3自动；3内参全拒；所有原SHA保持 |
| 独立机制诊断 | peer-diagnostics四个脚本/报告 | 各exit0；大倾角主行−17.38..−17.61°为手工限定ROI诊断，不算自动成功 |
| 原型 | prototype.py、prototype_v2..v5.py及projection_probe.py | 各脚本exit0不代表图正确：v1膜边误选、v2碎核漏末槽、v3峰点偏心/部分尺度失败、v4半突出宽度失败均保留；v5修正后用于产品方案，不宣称准确率 |
| 科学方案独审 | scientific-impact-review.md | 方向可实施，指出v2具体失败；不是最终代码独审 |
| 首次裁剪集成 | `pytest tools/wb/tests/test_intake_automatic_crop.py tools/wb/tests/test_reliable_geometry.py -q --tb=short` | pytest exit1，26过7败。外层PowerShell尾部Get-Content导致shell报告0，不能记作测试通过。原日志.local/T080/crop-integration-first.log |
| 静态检查 | ruff对根代理当前6产品文件+automatic_crop测试 | exit0；首次4格式错误已format修正 |
| 类型检查 | pyright根代理6文件 | exit1，3项均为并行交付API尚未接入cancelled参数；尚未最终复核 |
| 交接维护 | maintain_handoff.py --repo . --compact-if-needed | exit0，changed0/warnings0/unresolved0 |

## 测试预期变更的理由

T080明确扩展常见marker及大于10°明显主行支持，因此旧公共适配器的两个必停案例移为新policy4积极采纳测试，独立核验生成器定义的每槽样本中心、角度、身份和JSON重开；旧可靠domain的暂停和数值测试保留。空白、N冲突、等强双排仍保留真实反例。

手动旋转由随角度缩框改为固定尺寸，测试不再要求显示框位于旧ROI，而是断言新within_source@2政策、宽高不变、原ROI不变、原图边界及重开。另加真正源边越界拒绝；无关Fig保留测试将贴原图边界的fixture向内留4px，保留原先其他Fig和风格全部断言。不能为了测试继续静默缩框。

真实目录为开发诊断集，21case不是21独立项目；80%完整项目泛化尚无统计验证。最后应报告完整目录主链的实际表现及错误，不用候选数量代正确率。

## P3/P4 集成进度（2026-10-23，尚未独审/提交）

- 最终模块公共API诊断一次21例：20候选/20实际自动采纳（17新policy4、3既有policy3），reviewed均false；9采集组中8组的两来源都采纳，3PNG转换TIFF均采纳。这些是开发来源变体，不是21个或9个独立实验项目。唯一g02-2是末槽26个空白padding像素触膜外，核心并未越界，正按该新证据做限定修复。真实原图、TIFF副本、旧基线SHA不变；private报告 `.local/T080/common-integrated-final/report.json`。
- 旋转UI定向10例exit0，拖柄补强1例exit0；真实键盘/Qt pointer路径、主框与拉正预览、角度/固定宽高、撤销复位/重开。硬件WebEngine首次上下文错误保留，最终测试仅子进程设置`QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu`。补强后端审查发现仅角度编辑仍重建自动定量槽位，正在修复；不能把此时的旋转功能标成最终通过。
- `pytest tests/test_intake_delivery_ui.py tests/test_intake_delivery_restore.py -q --tb=short` exit0，2passed/4.79s：四个交付动作从主页面直接可见且带身份，未保存布局/忙态禁导出；完整交付目录通过真实主窗恢复到新工作区，所有原交付文件SHA不变，旧绝对输出位置不沿用。
- 完整UI增量组合（原35UI+上两例）exit1：36passed、1failed/25.91s。失败为新增测试断言误引用另一测试的`dragAngle`变量；改成此用例真实预期角2°，保留其晚到保存和新草稿恢复全部断言。`-k rotation_draft_late_save`定向重验exit0，1passed/2.38s；未放松产品或容差。
- 1440/1024宽度截图一次查看：首张宽屏抓到了旧compositor帧，补等待原生绘制150ms后随上述组合重抓；宽/窄顶部四入口均可见，无水平裁切。此为合成UI资料，不含真实原图。Impeccable detector exit2，6warning+10advisory均来自既有动态无src图片、处理中动画、旧半径/字体/背景阴影；新增交付条无检测项，未顺带改造原页面。未将detector记为通过。
- 全仓ruff check/format exit0（915files）；首次全仓pyright exit1，仅新交付测试3处tifffile.imread unknown，改用TiffFile读取且不新增ignore，最终门禁待跑。根此前限定6文件pyright缺cancelled参数错误已随API接入解决（限定再次exit0）。
- 交付作者：后端44项exit0/9.11s；完整desktop intake34项exit0/69.78s；追加3项真实桌面位置持久化/首次目录/逐裁图归位/保存失败不建目录/恢复新代边界exit0/12.25s。详见另行交付实现记录，均为作者验证。

以上没有代替准确提交的最终独立审查、必需CI或新安装包验收。依赖、锁文件、测试门禁与既有规则未降低。

## 独立预审与真实整项目新增问题

- 未参与实现的t080_independent_review预审11项非Qt通过（exit0/6.79s），确认3项P2，不以dirty树给提交级通过：纯旋转保raw后的pending页面无法再编辑；v4安装自检漏验证export drain；v4继续按钮虽有ready项仍被blocked-first后端拒绝。
- 前两项根已修：仅已reviewed的display_review@1 pending额外可编辑，新实际页保存ack/新session重开再改角/固定尺寸测试；安装自检显式核无其他running和可执行pending。UI交付3项exit0/4.22s。第三项由工作流作者修复，最终独审待冻结提交。
- 真实180目录及PNG转换目录首次整项目从真实主窗/Storage/worker启动：两例exit1/16.05s，均第一crop完成并CAS后在交付展示TIFF阶段报`TIFF strings must be 7-bit ASCII`。原工作区/报告保留，尚未宣称整项目完成。定位中文来源元数据编码后将重开继续，不能将这次失败隐藏成自动通过。
- 更新源码`--verify-supervision-installation .local/T080/source-supervision.json` exit0/13.58s，19检查全部通过：新policy主链、真实worker、原像素裁图、可见图/表、修改曲线、单Fig及完整拼图PNG/TIFF一致、重开、资源正常关闭。报告phase=passed/errors=[]；这次仍为源码运行，不能称安装包通过。Qt日志GLES降级保留，子进程使用offscreen/disable-gpu。
- 全仓pyright最后一次exit0（0errors/0warnings），ruff918files与import-linter9契约exit0。未运行本地完整check--all；准确最终HEAD的CI会执行全部门禁，当前不得填通过。
- 安装说明修正既有错误“一次仅一个目录”：现产品真实支持1–32本机目录，原有多目录原生事件测试保持；补充四入口、原值/展示TIFF区别、目录/ZIP恢复及不覆盖。安装资源版本0.14.0.79→0.14.0.80；依赖/锁/编译工具未升级。

## 保留现场后的完整目录验收

- 中文TIFF描述改为可逆ASCII JSON；PNG保留既有UTF-8字节，以便已写入PNG的旧失败目录安全续写。交付+sequence后端25项exit0/5.81s，真实Qt blocked+pending工作区重开、继续其他Fig、部分导出、修复后全完1项exit0/10.21s；没有重跑其他Fig的run/attempt/claim。
- `.local/T080/test_real_project_resume.py`从上述两个失败工作区重开继续，首次已经保存的raw crop SHA保持。整体pytest exit1，1passed/1failed/85.97s；180全部完成，PNG全部后端步骤和六个最终文件已完成，但最终等待结果页15s超时，独立保留该UI失败，正检查完成状态同步。没有再次运行算法整批。
- `.local/T080/audit_real_delivery.py` exit0/2.28s：公开恢复入口逐项检查180交付149成员、PNG交付50成员；9/3个Fig全部含单Fig PNG/TIFF及CSV/XLSX，总拼图、总表、恢复ZIP齐全，index complete=true/errors=[]。组内原图分别27/3张；CSV分别9/3数据行，非空且缺槽仍为缺失符号；所有12裁剪reviewed=false，无人工裁剪确认。39个原始文件SHA不变。
- 已查看两个实际完整拼图：180的9组与内参3组可见条带均完整保留，大倾角组已拉正；有弱泳道的组未删槽。项目分组和N是冻结的开发配置，不能以这两个配置项目证明80%独立项目泛化或积分真值。私有图像和逐源信息不提交仓库。
- 预审作者之外的审查者复验3项exit0/1.88s，三P2修复和ASCII兼容修复可接受；最终提交绑定结论仍待冻结SHA。
- PNG末尾超时已定位为ignored脚本早于WebChannel/session路由就绪调用bridge：一次真实重开后结果页六按钮全部可用、模型字节不变（1passed/7.35s）；两时序合成对照2passed/3.77s。不修改产品、不重跑已完成私有项目，修本地脚本就绪等待；详情completed-png-ui-diagnosis.md。
- 新增源码非自动`--verify-sequence-installation .local/T080/source-sequence.json` exit1/4.63s：部分输出后人工review点击未提交。原诊断及GPU日志保留，自动supervision的19检查通过不覆盖此失败；正在针对性核查诊断流程。
- 非自动诊断修复导航selected/提交submitted回执混用，并等待实际账本无running、pending_ready=0及页面digest一致；中间仅回执修正仍被正确的“当前阶段退出”门禁拒绝，失败保留。最终`source-sequence-drained-review.json` exit0，13必需检查/errors=[]/8.875s，实际两次人工复核、两个worker、原值uint16、缺失非零、完整输出/重开/正常关闭全部保持；详见sequence-diagnostic-validation.md。没有修改产品复核、调度或降低断言。
- 冻结前全仓Ruff check/format 920files、Pyright 0errors/0warnings、policy、diff --check及handoff容量维护均exit0。仍以准确提交独审与远端必需检查为P5最终条件。
