# P024 三工具练习走查

Windows 本机，工作树起点 72651ea。使用 P023 受审目录（5dbfb3947632，0.14.0）中的私有 Python 和已安装的 WebWorkbenchWindow，另起测试实例，传入本次独立 settings.ini，工作目录 .local/p024-walkthrough。选图、结果、导出均走正常桌面控件和真实 worker。这个验证入口没有再次测试 EXE 启动器。测试项目由应用在文档/BioImage/Projects 下分别创建唯一目录，原图及旧项目保留。

| 入口与材料 | 实际操作和结果 | 导出与冷重开 |
|---|---|---|
| WB 仪器文件夹，P012 生成的 A/B 两张 700×300 uint16 TIFF | 添加 Fig，N=5，Target 与 Reference 各选择对应 A/B 图，自动完成两行原始积分。两行都是 268125、375375、268125、375375、268125 | “导出原始积分”生成 WB结果.xlsx。新进程从首页最近项目打开同一 Fig，积分和完整快照目录相同。显式归一化沿用 P012 操作与既有证据，本轮检查原始积分最短路线 |
| 单图核分割，S-BIAD634 CC0 原图 | 从未配置状态进入运行设置，原生对话框选择 P015 外部 Python 和 P014 模型，再选择原图。实际方法输出46核 | 导出 count.csv、两个显示PNG、uint32标签和出处等。新进程打开 Nuclei-04e831efe9ae，仍为46核，运行 ID 3b914b640dde43fdaee28276dccbe484 |
| BCA，原有 synthetic.csv + record.json | 分别选择两份文件，核对绑定摘要与合成记录。两技术孔、预稀释10，导出 S1 原样均值 5008.680555555556 µg/mL，四组 partial 汇总留空 | 导出逐孔/样本CSV及出处。11月6日 Windows 原生重开对话框在确认项目之前由用户 Esc 中断。11月9日恢复后另起离屏 Qt 界面，从首页进入 BCA，使用 Qt 文件夹选择框读同一 BCA-8485a3ce4ce1，页面显示相同运行 ID 63647dd725694a7ba63805cd3623febe 与 5008.681 |

原始界面状态、导出资产摘要及冷重开前后156个已记录文件摘要保存在 walkthrough.json.gz。两组摘要逐项相同，未包含活动数据库、锁及日志。核和BCA导出目录与项目目录分开。固定核方法与权重、处理契约、默认值、schema、门禁及所有产品代码未改。

## 作者验证与限制

- 生成练习图：`uv run --locked --no-sync python examples/wb-first-use/generate.py examples/first-use/wb`，exit 0。核图从 P014 缓存 rawimages 原样取用，核对作者 CC0 说明和下载清单，SHA256 77f7b965733145a6edae173090ba1b9081266c708a3f141a12f8b281af640074。BCA 文件直接复用，保持现有逐字节绑定。
- 首轮桌面操作使用 P023 的 CDP 探针（独立端口）和原生文件选择。一开始隐藏的测试实例未开始运行即终止，并改用可见测试实例。一次原生目录框仍打开时 CDP 超时，确认选中目录后继续。WB 两个单选控件间页面重绘，重新定位第二个控件后成功。冷重开前首次读到活动锁失败，关闭进程后排除数据库和锁等再采集摘要。
- BCA 补验命令为候选私有 `runtime/python.exe -B -I .local/p024-walkthrough/finish-bca.py`。第一次探针误用窗口属性 view，AttributeError 后退出 -1073740791。修正探针为实际 web 属性，启用 offscreen 与软件渲染，结果证据写入且进程 exit 0，保留 GLES3/shared-context 回退日志。仅在此新进程操作离屏 Qt 文件选择器，未重新运行分析。
- `uv run --locked --no-sync python dev.py policy` 与 `git diff --check` exit 0。本机未重复全装配、科学或全门禁矩阵。真实学生、科学适用性、物理交互和干净目标机仍待相应材料/环境，历史 Linux 关闭 UNKNOWN 保留。

## 练习资料与复现

本机独立 ZIP 位于 `.local/p024-first-use.zip`，与 P023 程序目录分开。解压后从 `examples/first-use/README.md` 打开，WB 和核原图可直接选择，BCA 样例沿仓库原路径保留。维护者可从受审提交执行以下命令生成同一成员集合：

```powershell
git archive --format=zip --output=.local/p024-first-use.zip HEAD examples/first-use examples/wb-first-use tools/bca/examples tools/bca/README.md tools/nuclei/README.md tools/nuclei/requirements-research.txt docs/runbooks/nuclei-single-image.md docs/runbooks/unified-workbench.md docs/runbooks/research-workflow.md docs/research/2026-11-06-mature-nuclei-methods.md work/evidence/P-023/final-delivery.md
```

ZIP 用于现成候选练习，准备环境/追溯历史时可查完整仓库。冻结候选已有的说明不回写；本任务修订的随包说明适用于后续构建。

规则核验首次报“Integration needs exactly one changed integration context”。P023收尾另生成了以合并后 main 为基线的空历史清单，覆盖了原PR75集成清单。两份均保留：原PR75清单位于原路径，72651ea收尾清单逐字节归档为 P-023/closeout-integration-context.json，P023收尾 rules-context 保持原字节且登记在 P024 清单。未修改门禁。
