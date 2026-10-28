# R06/R07/R11 最终本机执行证据

2026-10-28。本轮冻结源码/完整门禁/实际构建源均为 `ed830e1d3bab3d0c8c57f3766a898991e8a0f431`，分支 `codex/t082-reliability-remediation`；执行期间 HEAD 与 clean 状态保持。此后交接提交只有文档和证据，不冒称由后续 HEAD 构建。原始记录及逐文件摘要见 [r11-raw](r11-raw/README.md)，原始本地目录 `.local/T082/r11/` 保留。此处记录本机工程验收，科学适用性与外部矩阵未通过项见文末。

## 环境与最终工件

- Windows 11 家庭版中文版 10.0.26200 x64，Core Ultra 7 255HX / 20 logical processors，物理内存 16496738304 B。CPython 3.12.14、PySide6/Qt 6.12.0、uv 0.13.0；PS 5.1 与 PS 7.6.5。
- 最终工件目录 `C:/Users/70236/.codex/artifacts/T082-ed830e1/.local/releases/runtime-ed830e1d3bab-acceptance-t082-r11-a`；安装器 `BioImage-WB-Acceptance-t082-r11-a-Windows-x64-ed830e1d3bab-Setup.exe`，**384432982 B**，SHA256 **`5c49309132a8152c8b095dd255acdcef9adf02ecfa68175e36a6de83be724268`**。不是 Laboratory 发行包；未推送、发布或替换在用安装。
- 最终 build-manifest SHA256 `8e3dc049b1305656be28f7ad950f74c43b26f8e26ca2f095ed202edec2643418`。记录已核验工具来源/版本/哈希、第三方依赖哈希与四个 wheel、uv.lock、模型/VC runtime、安装载荷及准确源码。完整标准构建 `python -m tooling.build_runtime_candidate --iscc <锁定ISCC> --gcc <锁定GCC> --laboratory --acceptance-id t082-r11-a` exit 0；实际绝对参数见 build-start 和 manifest。
- 从 `.local/T082/r11/新检出 验收源码` 的干净 ed830e1 检出执行仓库 wrapper，以候选的私有 Python `-I -B -X utf8` 核验，PS5.1/7 **均 passed / exit 0 / 7794 文件 / extras=[]**。核对 Git 参考归档 399 文件及 shipped source 217 文件，参考归档 SHA `d70c7c592e317a4255a3898f11f776d11e233e24f5de9d05bc8ccd75d107186d`。失败报告通过 previous-report SHA 关联，未覆写。

## 完整仓库门禁

在本工作树对准确 ed830e1 执行 `uv run --locked --no-sync python dev.py check --all`，进程局部 `QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu`：**1503 passed / 10 warnings / 756.15s，全部 isolated installed_wheels 成功，整体 exit 0**，结束后 HEAD 不变、dirty=[]。

包含 policy、Ruff/1018 文件格式、严格 Pyright、9 条导入契约、固定 JS 工具/4 个负例、自有 Python 回归、四 wheel 隔离安装/API/桌面/OCR worker/历史与导出/异步关闭。未运行远端 CI；不能由本机记录推断 Linux 或远端检查成功。完整日志 SHA256 `8b096e5eaf7e437c6e949b582c2cd186330f49f74cf36d8d00f52b98175e3669`，exit 记录 SHA `ade6ab7d3a96db203eef4bc60cb644cdb3a6d80c92d6f7e629b91e97df26d0b9`。

d66655b 的先前全门禁 1501 + wheels exit 0 也保留，不能替代包含随后 f5d7ac9 wrapper 修复的最终门禁。44ee78c 的 2 failed / 1499 passed / exit 1 与 wheel 未运行继续保留；d1036c2 的同一行撤销修复及反例/独审见 [r05-final-gate-repair](r05-final-gate-repair.md)。

## 真实安装、跨版本升级和安装态验证

唯一可弃身份 `BioImageTools.WB.Acceptance.t082-r11-a`，设置 `Acceptance-t082-r11-a`，通道 `wb-acceptance-t082-r11-a`，启动器 `BioImageWB-Acceptance.exe`。实际中文空格目录 `C:/Users/70236/AppData/Local/Programs/BioImage WB 验收 t082-r11-a`。事前记录并保护 Laboratory 的登记、设置摘要、快捷方式和三份安装身份文件。

| 实际执行 | 结果与证据 |
| --- | --- |
| 旧提交 244c5da1b03e47f6d17801912cb38003e8edab27 构建并安装 | 独立同 AppId 旧版本安装器 SHA `9606126d48ec33e53164c50f5dd230c23890ae0af9f6315235d8bad0b1cfc667` / 384431971 B；PID45400 exit0，登记与5快捷方式正确，旧安装严格核验7794文件通过 |
| 真实升级 244c5da → ed830e1 | PID55160 exit0；同 AppId/目录，日志追加既有卸载记录，登记版本变为 `0.14.0-Acceptance-t082-r11-a-ed830e1d3bab`；26份合成原图/项目/清单全部摘要和大小保持，设置 sentinel 保持。5个快捷方式身份/目标保持，升级重建使 .lnk 字节摘要变化 |
| 升级后私有 Python 严格核验 | passed / exit0 / 7794原载荷；仅额外 `unins000.dat`、`unins000.exe`，不将它们算作认证载荷 |
| schema 1–6 安装态旧工程 | `verify_installed_legacy.py verify` 用私有 Python `-I -B -X utf8`，PATH仅System32、无开发环境注入；全部读取/保存/渲染/ZIP/恢复通过，原样本保持。实际API位于安装runtime，isolated=true / bytecode_writes=false；夹具清单 SHA `84acf225cd697039c9c830fd60e9b11f9710d6d8e6013cbd82b18f83aa22b247`，旧金样未因本轮重定标 |
| 随包第一诊断 | `--verify-installation` PID26832 exit0 / 17.782s / 无超时；报告7 checks、errors=[]，含真实durable worker/离线OCR、保存失败可见且窗口保持、保存重开、busy取消后的草稿/dirty确认与资源关闭 |
| 随包第二诊断 | `--verify-supervision-installation` PID47660 exit0 / 14.891s / 无超时；报告19 checks、errors=[]，原uint16裁图、显示纠偏、缺失不填零、提交后的XLSX/恢复包、PNG/TIFF与grid、实际页面/阶段门槛、重开、原图保持和关闭；PID54356/13540两个worker已退出 |

双诊断之前再次严格验证载荷；模块探针 PID41144 exit0，四包路径均来自安装 runtime，isolated=true，通道正确。总报告 SHA `28f0bdb064acc2ed426cbb14c3f76bc0eedee413b8eb7e3ced567852e60a70ee`，两诊断 SHA 分别 `08e871488ce72697ce60a8c85b526dc39c459c1f27969821f7a3b9279327dcde` / `d10e0f5ca00c8f12c3ba4fbc3ce7860f53d0ccea00d62607667ccd72b69dfc18`。第一诊断无逐worker PID记录，资源关闭断言不外推成逐PID观察。结束时原7794文件保持，新增1274个 pyc **仅列为未认证缓存**，不改可信清单、不清除后重跑冒充首次通过。两份 stderr 的 GLES3/shared-context 错误保留，不能宣布 GPU 根因修复。

## 真实卸载与数据保护

严格验证/诊断完成后，才在安装根下新建 `用户保留 合成验收`，复制26份已冻结合成原图/工程/清单；它是卸载保留探针，未污染此前的严格载荷验证。原26文件、安装内26副本及已完成验证输出121文件共173份逐文件冻结 SHA/大小。

脚本匹配准确 AppId 注册键、ed830版本、绝对根和登记的 unins000.exe，并拒绝根目录重定向；只运行该自有卸载器。PID47416 **exit0 / 未超时**，日志 `Uninstallation process succeeded` / 不需重启。验收注册键、启动器、private Python、卸载器和5快捷方式确已移除。**173文件全部原样保留，设置 sentinel 保持**；目录剩余 **1274运行缓存 + 26合成用户文件**，没有手工删除。日志的非空目录145与此一致，不能说安装目录清空。

Laboratory 的七份前后快照（准备、安装前后、升级前后、诊断后、卸载后）均 SHA256 `b4e2b65b20c6380a4b6f32fdb541bf4c347b4cde5e241500581ee69e6ef17fc3`。其中记录20个卸载键值、157个设置值的摘要，以及旧快捷方式/安装身份文件摘要，不公开私有设置内容。原 ResearchVault dirty 树、原图和历史项目未作为这些测试输入或清理对象。

## 失败链与有效替代路径

1. d66655b 在深 worktree 构建到 Inno 阶段失败 exit2：真实存在文件的路径达到260字符，载荷最大272；未删除依赖或改清单，改为同源码干净短检出后完整构建通过。短输出路径是已验证的规避路径，不宣称修复所有 Windows 长路径情形。
2. 新检出的真实私有 Python 揭示 wrapper 缺 `-B`，先写 argparse.pyc 后被严格验证正确拒绝。f5d7ac9 最小修复，双shell 2红→2绿、48相关与独立5测试通过；仍拒绝已有未冻结缓存。失败候选保留，未清缓存改成功，见 [r07-private-runtime-repair](r07-private-runtime-repair.md)。
3. ed830e1 首次短 Temp 构建 exit0，但后续两shell验证均发现缺失 annotated_types/py.typed。只读调查发现3个Temp候选均少98个原先存在的零字节文件；旧实际安装仍完整、Inno日志曾压入对应文件、安装器摘要不变。**删除进程、时点和根因 UNKNOWN**，不能归咎于某个清理器或 Inno。没有手补空文件、删除旧失败或把缺失忽略。
4. 新建 Temp 外的持久短检出，同 ed830e1/锁定工具完整重建，得到本页唯一最终 SHA5c493…；真实双shell新检出严格核验全部7794通过，然后用该包完成实际升级与验收。首个Temp ed830安装器 SHAeeef1…和更早d666 SHA054404…仍只是历史工件，不可误拿作本次验收包，也不承诺重建字节相同。

## 独立复核与未验范围

非作者 `/root/independent_review` 对准确 ed830e1 全门禁、实际最终安装器/manifest、双shell请求/失败恢复关系、升级、历史报告、诊断及卸载给出 **Accepted**。其独立实算安装器与报告摘要、26及173文件SHA/大小、当前卸载状态、5快捷方式及Laboratory快照；没有重新运行产品、测试或清缓存。源码整体/后续修复的准确提交独审见 [final-integration-review](final-integration-review.md)。最后交接差异单独复核，不借此提前宣布最终文档通过。

原生屏幕探针以安装私有Qt、windows插件和无列明强制缩放变量记录 DPR1.5 / 逻辑DPI96 / 物理DPI126.0475 / 1707×1067；它**仅是环境观测**。自动诊断使用受控离屏环境，不能称物理150%交互验收。当前最小矩阵已完成本机Win11中文路径、安装/升级/卸载与合成生命周期；干净Win10、其他员工设备、物理125/150/200%/多屏/拖放、真实GPU及外部Office未运行。旧native异常及Temp零文件根因仍UNKNOWN。

R10 用户已明确暂无独立留出及负责人方法/指标/容差，保留科学待办；十个科学定义文件与冻结摘要保持，不宣称ImageJ等价、独立准确率或科学适用性通过。R09剩余调查线/小例回退及R12有据暂缓见对应台账。全部必做验收未齐，整体目标不能标记完成。
