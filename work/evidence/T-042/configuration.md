# T-042 配置与检查记录

日期：2026-10-17（Asia/Shanghai）；Windows 11 10.0.26200；base b32acff0dff9d6c6a84741ecc3aba8a3be4a010f；分支 codex/t042-source-only-repair。本轮无产品代码/依赖/规则改动。

| 检查 | 退出码 | 结果与边界 |
|---|---|---|
| git status / branch / HEAD / worktree list | 0 | 原主目录dirty保留；复用最新协调树；该树原有.impeccable/questions未跟踪内容保留 |
| dev.py context --task T-042 --scope work/tasks --scope work/evidence/T-042 --scope .agent-handoff --record | 0 | 已生成rules-context.json；后续扩大产品修改范围须重载 |
| dev.py doctor | 0 | Python3.12.14、pytest9.1.1、Hypothesis6.169.0、Ruff0.17.0、Pyright1.1.414；product_status仍为过时文案，不作产品状态依据 |
| dev.py smoke-env | 0 | Qt6.12.0、NumPy2.5.4、SciPy1.18.1、Pillow12.3.0、Pydantic2.14.1；uint16 TIFF、QProcess、offscreen QWidget通过；非工作台端到端验收 |
| gh --version / auth status | 0 | gh2.96.0，已认证；未写GitHub、未外传图像或创建PR |
| dev.py policy | 0 | 现有离线边界检查通过，扫描112产品文件 |
| 本地数据清单（Python只读SHA） | 0 | 8源图SHA全部匹配旧首轮manifest；12参考文件建立当前SHA清单，未做历史参考SHA比较；无重新识别 |

本地隐私清单：.local/t042/input-inventory.json，不进入Git。仅记录输入路径/hash/位深及尺寸，不含参考几何；旧首轮预测文件另记SHA。参考文件数量12不等于12个验收样本，实际配对评分须阶段0确定。

社区检索入口已实际调用（2026-10-17）；以下是研究线索，未安装、未跑算法对照，不声称解决本图：

- [ImageJ Analyze/Gels官方工作流](https://imagej.net/ij/docs/menus/analyze)
- [ImageJ GelAnalyzer维护者源码](https://imagej.net/ij/developer/source/ij/plugin/GelAnalyzer.java.html)
- [scikit-image区域方向示例](https://scikit-image.org/docs/stable/auto_examples/segmentation/plot_regionprops.html)
- [scikit-image Hough等几何API](https://scikit-image.org/docs/stable/api/skimage.transform.html)

工具选择：现有Web、Git/gh、锁定数值栈与Qt测试足够启动；不新增插件/MCP或变更用户全局配置。已应用plugin-management和agent-handoff；性质测试、界面接入、PDF阅读到对应阶段再读相关技能。

未运行：修复后8图准确率、产品测试、完整check --all、独立审查、远程CI、干净Windows、包态交互。修复前严格1/8来自T040冻结证据；本轮未重新算出该准确率。旧600 passed但exit1保留待诊断。

收尾：maintain_handoff.py --repo . --compact-if-needed exit0，归档1个旧work-log节，unresolved=0；git diff --check exit0。配置文件未提交，产品HEAD保持base。
