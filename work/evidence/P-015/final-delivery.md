# P015 工程验收交付

2026-11-06：固定StarDist研究适配器已按正常PR流程合入[PR66](https://github.com/Junweiiii14/bioimage-tools-platform/pull/66)，主线`a7612843e5216f0471b51be93bd3687f0b8dbc82`，与最终候选`8f00757a966d5ff7c9f9237dbfe39471d3c9719b`文件树逐字节一致（git diff exit0）。本地已合入实际main为`528c8217356c52d0f2c9cb7aa5188eed6a954d61`；后续收尾仅文档，随下一正常任务带入。

## 交付接口

独立`tools/nuclei` / `nuclei_tool.api`和显式`python -m bioimage_app.nuclei_cli`。只接受单页、单通道、unsigned uint8、BlackIsZero/TopLeft TIFF；拒绝signed、16bit、RGB、多页和显示变换。输出原图YX坐标uint32实例标签、核数、输入/固定方法/权重/预处理/环境出处；零核是有效结果，异常/取消没有成功资产。

固定P014 StarDist0.9.2/2D_versatile_fluo、scale0.5等参数与三个权重成员摘要。TensorFlow只在单独固定环境运行，worker不自动下载模型。复用WorkflowSession/RunSession/AsyncStorage/Workspace的取消、进程树退出确认、临时目录回收和事务提交，没有新执行引擎、WB算法修改或平台实验特判。[完整准备和运行命令](../../../tools/nuclei/README.md)。

## 实际证据

| 项目 | 结果 |
| --- | --- |
| 真实隔离模型/进程 | 14场景通过；9张已见公开灰度图每个标签像素/实例ID等于P014冻结直接调用，另含零核、缺模型、坏摘要、取消、16bit拒绝 |
| 原图/资源 | 原输入SHA不变；50ms采样观察到的后代进程均退出；候选只由既有宿主完成事务后发布，模型暂存归宿主所有 |
| 新用例 | 21项工具/宿主用例通过；新增4个传递边界负例，连同原测试共48项定向通过 |
| 独审 | 产品`a490d2e`通过；门禁测试增量`95ecb02`通过；修复signed TIFF、长异常协议、venv入口解析三项问题，[完整审查](independent-review.md) |
| 本机全仓 | `dev.py check --all` exit0；1728 passed/10既有warnings，1208.32秒；全部隔离wheel通过；使用现有CI同样offscreen/--disable-gpu |
| Windows CI | [job127452480405](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/42086151498/job/127452480405)，1728 passed/10warnings，1420.98秒；完整check/wheel成功 |
| Linux CI | [job127452481324](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/42086151498/job/127452481324)，1724 passed/4既有Windows限定skip/10warnings，810.58秒；完整check/wheel及venv回归成功 |
| 必需门禁 | quality42086151498、rules-context42086151033、desktop-environment全部成功；可选native-case未运行，不计通过 |

真实运行摘要见[real-regression.json](real-regression.json)。第三轮9次完整CLI含宿主/进程启动平均6.85秒（5.96–9.30秒），观察到的后代RSS总和最大577.35MiB；50ms采样不是精确峰值或内存硬限制，不能与P014纯推理时间直接比较。新包默认/隔离wheel不依赖TensorFlow、GUI或平台存储；研究环境为固定Python3.12.14，完整依赖另行准备。

## 保留的失败与限制

初版Windows阻塞管道与NumPy native导入死锁已由最小探针定位，改非阻塞pipe并补回归；首次300秒deadline取消无发布。首轮全仓exit1（1717 passed/4 failed）：旧导入正例仍期待9条而实际新增到11条，已修正并增加负例；另3个旧旋转画布超时在现有CI设置下原断言通过。原失败不抹除，物理GPU上下文问题不宣称根治。

严格类型0 errors/3个研究库缺源码warnings保留，未忽略/降级。uv.lock现有第三方版本未变；仅新轻量成员/额外项，研究依赖分离固定。未改旧测试容差、skip/xfail或服务器规则。

已见P014图像只证明封装一致性，不是新的独立科学验证。训练重叠、患者独立性、16bit、Linux实际模型推理、实验室/学生/目标机验收仍未覆盖；无IF强度、全细胞、统计、Agent、安装器发布或私有数据上传。原dirty工作树、在用GUI/安装与私有原图未操作。旧P014/P013/P012/T082科学和目标环境缺项不关闭。

## 自动接续

验收结果已成功回传指定上游`01a19bfd-f3ab-7502-86da-9f61953d1c8a`（local，工具返回目标threadId、isError=false），由上游核对依赖后自动派发，不等待用户再次催促。下一最小候选是现有界面中的单图研究结果走查：原图与标签定位/核数/出处/失败原因同源展示，明确研究状态；仍沿用既有执行与提交，不扩整套GUI或科学准入。具体任务号和范围以正式派发为准。
