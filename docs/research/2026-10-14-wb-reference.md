# WB 参考冻结与首个产品包

问题：冻结哪些结果定义，怎样证明新数值核心可独立安装且不依赖 GUI？
2026-10-14 核验原方案第 18-19 页及旧 `wb_quant/core.py`、`normalize.py`、`io.py`。
原方案渲染到 `.local/wb-plan-page-18.png`、`19.png`，第 19 页公式、验收表与提取一致。
旧源码 8 个文件字节快照与 SHA 清单已保存，逐字节复核通过；旧目录无 Git，不能编造 commit。

决定：先独立实现 `profile_integral@1`。使用标准库 `fsum` 汇总梯形，公开 API 不依赖
NumPy、SciPy、Qt 或数据库。有效零值与未检测分开。冻结契约见 `docs/contracts/wb-reference-v1.md`。
保留原模式，二维像素总和、目标/内参归一化不得静默替换原有信号定义。

构建方案选择 uv 自带兼容后端 `uv_build==0.13.0`，实际构建并安装 wheel 成功。
来源：[uv 官方构建后端](https://docs.astral.sh/uv/configuration/build-backend/)
与 [workspace 文档](https://docs.astral.sh/uv/concepts/projects/workspaces/)，访问 2026-10-14。
没有引入新的运行时第三方依赖；uv.lock 仅增加本地 workspace 成员 wb-tool。

导入门禁采用现有锁定 Import Linter 2.15 的真实 console entry point。模块模式
`python -m importlinter.cli` 实测不执行检查，因此通过 `tooling.import_contracts`
调用真实 `lint_imports_command`。配置及传递依赖方法来源于
[维护者文档](https://import-linter.readthedocs.io/en/v1.10.0/contract_types.html)，
文档版本与安装版本不同，行为以本机 2.15 正/负图实验确认；新版文档地址 404，未用其支持结论。
两个合约检查 API→domain 层级和 domain 禁止 GUI/存储依赖，三例独立小图
确认合法图通过、传递 sqlite3 和反向 API 依赖失败。不预建第二模块以凑 independence 合约。

限制：解析数组证明公式，不证明真实条带检测。真实 TIFF 尚无认可人工标注；
饱和与曝光线性的条带级质量判定、归一化和 UI 仍待实现。
添加新包、改变公式/输入定义、引入两个独立工具时重新核验边界与隔离安装。

## 输入阶段

wb-tool 0.2.0 新增单页 TIFF 适配和半开泳道 ROI 原始剖面；依赖使用锁中已有
NumPy 2.5.4、tifffile 2026.9.20。整数 RGB 转换按冻结来源定义，位深上限依 dtype
而非固定 65535。MINISWHITE 保留原值并显示提示，dark/light 由调用者显式声明。
通过元数据判定 RGB 与 planar，不用数组尺寸碰巧为 3/4 推断颜色轴；不支持方向明确拒绝。
38 项数值/输入用例和 5 张真实输入烟测通过，后者仅验证输入路径。
新增实际 TIFF 输入与积分的 independence 合约及传递负例，当前三类门禁均运行。
隔离环境先按 uv.lock 同步依赖、禁止安装 workspace，再安装真正的 wheel；
可用缓存不足以保证离线索引解析，未宣称隔离依赖安装必须断网。
