# 用户追加的成熟算法复用准则

2026-11-05，上游转达用户明确要求写入库内正式方案并同步HTML/Git/main，不只停留聊天。P013任务卡已扩充文档范围，context --scope . --record --integration重新运行退出0并读取；旧回执保留在4ebb14d及之前提交，本次仅更新真实source_head，不改规则/门禁。

实际修改 `docs/plans/research-platform-rd.md` 第5节、`docs/plans/workflow-development.md` 第3节及同名HTML。覆盖新研发/基线继续优化之前先检索成熟实现/官方pipeline/预训练模型、适用者直接调用、版本/代码与权重许可、代表性对照/失败/CPU/部署成本、自研证据边界、所有实验模块/算法研发Agent，以及不加繁复审批。既有规则中的“本项目现成实现优先”已改为实证比较，不默认简易自有基线胜出。

检查：`npm run build --prefix docs/plans/renderer` 退出0；五份固定输出中仅两份正文变化，其余Git内容不变。HTML解析检查关键要求文本及相对链接通过；`git diff --check`、`dev.py policy`退出0。未改样式/构建器、产品代码/依赖/测试，不为此启动本机全量。

PR63的4ebb14d仍运行原必需CI，不推送其活动分支新HEAD。此补充先本地提交并立即回传上游，明确尚未main；PR63集成后另走正常PR与必需检查，不能只留下本地补丁。P013最终完成还包括本项main同步与回传。

## 后续真实调用入口预检（未安装、未运行）

2026-11-05补核以下官方来源，只用于下一任务设计；本轮运行算法仍仅scikit-image基线。

- CellProfiler [v4.2.8发布](https://github.com/CellProfiler/CellProfiler/releases/tag/v4.2.8)及[BSD-3许可](https://raw.githubusercontent.com/CellProfiler/CellProfiler/v4.2.8/LICENSE)已核。[官方examples](https://cellprofiler.org/examples)的Human cells、Counting and scoring可作为pipeline入口；示例资料许可/固定文件摘要与适用范围仍需单独核对。[固定版本CLI源码](https://raw.githubusercontent.com/CellProfiler/CellProfiler/v4.2.8/cellprofiler/__main__.py)明确headless使用`-c -r -p`，以及`-i`输入和`-o`输出。下一项应调用官方程序和pipeline，不复写IdentifyPrimaryObjects。
- [4.2.8 setup.py](https://raw.githubusercontent.com/CellProfiler/CellProfiler/v4.2.8/setup.py)声明core4.2.8、scipy1.9.0、skimage0.18.3、tifffile<2022.4.22及Java/wx等依赖，与当前产品环境不同；需先选官方独立发行或隔离运行环境并测CPU/内存/失败退出，不能直接将旧依赖灌入产品，也不能把安装成本当作跳过成熟实现的理由。未证实当前主机安装可用。
- StarDist官方发布入口当前为[0.9.2](https://github.com/stardist/stardist/releases/tag/0.9.2)；[官方README](https://github.com/stardist/stardist/blob/main/README.md)说明`StarDist2D.from_pretrained('2D_versatile_fluo')`/`predict_instances`调用，以及该模型和2D_paper_dsb2018均训练于DSB2018子集。权重的具体版本/许可/摘要及独立评估集尚未核完，不下载模型或声称准入。
- [Cellpose当前模型文档](https://cellpose.readthedocs.io/en/latest/models.html)页头为4.2.1-1-ga54cb48，列有SAM/DINO模型，首次调用会自动下载权重。不能依“latest”不加区分地安装；下一项需固定具体发布/模型，先核权重许可、大小与CPU可行性，再决定是否纳入少量候选。这里没有授权下载大模型或证明性能。

BBBC038/039及DSB2018关系已在任务卡标明；下阶段先检索未参与候选训练的适用公开标注，再冻结独立留出，无法核实重叠则仅报告诊断表现。
