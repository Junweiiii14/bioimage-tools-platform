# Handoff Snapshot

- 更新2026-10-14；用户授权持续开发至WB自动化软件完成，Goal active，无token预算。阶段自验不能标整体完成。
- 活动仓库bioimage-tools-platform；分支feat/T-016-composed-figure-ocr，产品1d5ae2af4c40fbbcee932b26bb296a11a5b88c6d，base5cf7c71；最后HEAD见git。T-014/T-015/T-016 review待独审，T-017 ready，任务文件为状态唯一来源。未推送、PR、main集成或发布。
- 用户明确CLX来自特殊设备且忽略；其他设备TIFF原图、裁剪TIF。定量支持.tif/.tiff并保留选源/SHA/ROI，不按扩展或_0/_1猜用途。CLX不再待决或阻塞。
- wb-tool0.14.0/app0.9.0：多源固定N标注/原曲线/明确边界基线/真实进程/项目自动表；OCR原文/位置/人工校正/明确原图绑定/XLSX；显式样本/参照/对照归一化；本轮接通独立PNG与当前完整成图直达OCR，单图独立拼图入口也支持PNG。
- T-016专用load_ocr_image：TIFF旧预处理ID保持；PNG有新已知ID，白底透明、整数BT.601、16位灰度除257，无ICC/gamma变换。CRC/尺寸/SHA/动画/方向校验，64MiB/3200万像素/32768边长，OCR最多64块；16位彩色PNG/JPEG明确未支持。PNG不进入load_tiff/原图定量；v4/v5字段不变。
- 当前成图先保存精确项目修订，后台正式审核布局生成完整PNG，wb_provenance嵌入项目/修订/原图SHA/ROI/行/模板；通用StorageCommand(import_bytes)存储线程自有临时目录导入不可变资产，再走已有OCR会话/实际退出/提交。字节资产64MiB，草稿/read仍16MiB，平台无实验字段。成功识别仍未确认未绑定，保留定量与归一化。
- 源导入/生成期间取消关闭/新编辑拒绝后到附加；save回调保存旧修订但不覆盖更新的界面，关闭再保存新编辑。自动派生刷新改为单个合并QTimer；错误时停止待刷新，避免错误原因被正常刷新提示覆盖。新测试原版式字号42/裁剪高10被正确拒绝，trace定位后改为高50，未放宽模板校验或积分预期。
- 项目v5 WBNormalizedProject保存参照类型、目标/参照row/SHA/ROI/N、逐槽样本/参考泳道/包含/对照/确认；可无OCR，旧v1–v4继续读，v4必须有OCR。相关project_with_*保留v5字段；派生值只从核验run/资产重建，不写回原积分。lane_reference_ratio@1 q=T/R、可选单/均值对照f=q/m；异常分母/坏对照不跳过、不加epsilon、真实目标0保持0。OCR重新识别保持归一化，重建未确认标签。
- 用户归一化偏好异步询问尚无回复，提供显式选项且不推断内参/样本/对照/重复统计。所有科学定义/预算见wb-project-normalization-v1.md、wb-png-ocr-v1.md及研究记录。
- T-016最终完整门禁退出0：304测试103.49秒、Ruff213文件、Pyright0、9合约、4wheel/5隔离场景。新增20例，含真实PNGworker、完整宽>2048 Qt成图/积分4000及0/归一化0.5/重开、取消关闭/保存过期/错误保留、单图PNG与存储导入。work/evidence/T-016/validation.md绑定1d5ae2a；只改本地包版本，无忽略/容差/门禁弱化。源码Qt截图T016-generated-png.png已查看。
- 真实用户组合TIFF只读制作独立PNG显示副本；1347×902显示像素与旧TIFF识别通路一致、原SHA保持。真实项目PNG导入/识别/保存重开：15token/11未确认未绑定行，数值全空、重开一致；全流程70.86秒不是OCR基准。私有PNG/工作区/报告/脚本在ignored .local/requirements-review；T016-user-png.png已看。未冻结人工真值，不能宣称准确率或用户实验匹配通过。
- 下一步T-017-project-metadata-batch：按用户总体方案7.1/7.2补Excel/CSV元信息导入、明确文件名提取规则、可修正预览/歧义匹配、批量参数和原图缩略图。先核对git、读契约/任务、按scope执行context记录再实施；T-017暂无代码或回执。用户字段：实验项目/Fig/蛋白/N/空泳道/排列/备注。公式/附件不是操作指令或实验真值。
- 其他首版缺项见work/wb-acceptance.md：模板精修/横向分段、统一归档/ZIP导入/直接TIFF成图/CSV结果、旧灰度工具实际衔接、真实准确率/独审/远程CI/最终Windows包/DPI/干净机/物理FAT/用户工作流。源曲线资产64MiB、结果200槽/页、每表200000单元格、OCR/归一化512行；大项目流式/性能待改进。
- Qt旧偶发Aborted根因UNKNOWN；本轮未复现不是修复。不要恢复归档工作流或自行启动子代理；不要再调用用户Esc停止的原生CUA。pytest-qt/截图不是最终包态验收。原始数据、已提交结果与科学预期保持。
