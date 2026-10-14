# T-013 作者验证记录

2026-10-14，分支feat/T-013-crop-candidates，base194794e；实现与证据在同一提交，准确HEAD以git log为准。Windows、Python3.12.14、uv0.13.0、PySide6/Qt6.12.0；第三方依赖不变，仅wb-tool0.10.0/bioimage-app0.5.0本地版本改变。

- `uv run --locked --no-sync python dev.py check --all` 最终退出0：Ruff182文件、Pyright0、9导入合约、244测试（65.02s）、4wheel/5隔离安装场景。日志ignored `.local/requirements-review/t013-full-check.log`。隔离wheel新增公开候选API、v2记录/读取与原ROI保持断言；原OCR模型/worker安装检查保留。
- 定向 `pytest tools/wb/tests/test_crop_detection.py tests/test_figure_desktop.py -q`：16通过。新增9个领域/应用用例（包含参数化）和5个GUI用例，旧2个项目GUI继续通过。覆盖原值/固定N/空位/暗亮极性/噪声/弱槽/上下限/多膜/边缘策略/取消，旧v1读取、v2保存、非法身份几何分类拒绝、手工元信息保持、复核门禁和归档快照。
- Qt真实按钮流程：检测→切候选→应用→手改→恢复→N改变禁用旧应用→状态筛选→聚焦膜画框仍为原坐标→保存重开；删除行同时移除当前建议。故障源继续后续行，取消/关闭保留已完成建议，检测期间编辑使结果丢弃，关闭后实际资源退出并可重开。
- 用户实际10张TIFF通过真实窗口导入/后台检测/聚焦截图/保存关闭重开。10个快照，源SHA前后相同，所有真实行无已应用ROI且未审核。候选数2/1/0/0/3/1/0/0/2/1；白背景和小裁剪自动定位失败保留状态。私人脚本/JSON/截图均在ignored `.local/requirements-review`。不提交私有图；不声称真实准确率。
- 界面截图已检查：修正长内部row UUID挤在泳道标签的问题，改为仅显示泳道序号；膜/Marker/候选标签分开位置。真实图膜较小，补聚焦功能并验证坐标。最终截图`real-candidate-desktop.png`只作本地证据。

## 发现与修正
首个Qt用例错误地把偶数宽条带的加权中心取整写死为y0=66，实际为67。改为检查所选建议映射、包含已知条带和固定高；领域位置的预设±2像素真值断言不变，未放宽算法容差。静态检查发现测试dict展开类型和私有路径访问，改为TypedDict与资产relative_path；聚焦范围tuple长度推断改为明确tuple[int,int]。第一次全量在该类型错误处停止，修正后最终全量通过，无skip/xfail/type-ignore/门禁放宽。

首轮真实算法探针检出膜边缘过渡被排为行候选；在算法v1正式提交前增加显式膜边缘包含选项/默认guard及可见提示，并增加合成边缘回归。未从任务单预期结果调参。已提交契约列明工程默认值与上限，原定量算法未变。

## 尚未完成
独立审查、远程CI/PR集成、完整Windows产品包/干净机/DPI/物理FAT、人工真值准确率均未运行。本轮未复现旧Qt原生中止，根因仍UNKNOWN。源无后缀/_0/_1/CLX身份与定量用途待用户说明，软件继续显式选源。项目级OCR/多源定量/自动表/归一化等见T-014与首版核对表；不能标整体goal complete。
