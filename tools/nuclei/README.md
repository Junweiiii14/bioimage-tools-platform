# 固定核分割研究工具

唯一公开入口`nuclei_tool.api`。固定P014 StarDist0.9.2/2D_versatile_fluo研究方法，尚无科学准入。
领域只验证数组和标签；输入/模型/输出I/O在适配层，宿主通过既有WorkflowSession运行独立worker。
TensorFlow不属于本包默认依赖，不得在宿主导入时加载，也不运行时下载权重。

接口暂限单帧、单通道uint8 TIFF；不接受RGB、16bit或显示转换。输出标签保留原像素坐标，合法零核与失败分开。
进一步只收单页、BlackIsZero、TopLeft（Orientation=1或缺省）的TIFF；RGB/调色板/多页/翻转标签明确拒绝。Pillow只解码原始灰度，不做通道猜测、缩放、LUT或位深转换。

## 准备与运行（Windows研究入口）

在仓库根完成`uv sync --locked --all-groups`。以下使用**新建**的研究环境，避免改动已有实验环境；重模型依赖不进入默认桌面依赖。Python固定3.12.14，依赖清单沿用P014并补固定Pydantic契约依赖。

```powershell
uv venv --python 3.12.14 .local/nuclei-research-env
uv pip install --python .local/nuclei-research-env/Scripts/python.exe -r tools/nuclei/requirements-research.txt
uv build --package tool-contracts --wheel --out-dir .local/nuclei-wheels
uv build --package nuclei-tool --wheel --out-dir .local/nuclei-wheels
uv pip install --python .local/nuclei-research-env/Scripts/python.exe --no-deps .local/nuclei-wheels/tool_contracts-0.1.0-py3-none-any.whl .local/nuclei-wheels/nuclei_tool-0.1.0-py3-none-any.whl
```

模型由用户明确准备；运行时不下载。固定来源为[StarDist models v0.1](https://github.com/stardist/stardist-models/releases/download/v0.1/python_2D_versatile_fluo.zip)，ZIP SHA256 `4ad678d0758eed6e55625f1b5ae30771e59adb79f1239e09b9772eac8846c3dd`。将已核验的`config.json`、`thresholds.json`、`weights_best.h5`放入专用模型目录。三个成员摘要固定于`domain/method.py`，运行时检查原目录及私有快照。许可为BSD-3-Clause，准确版本及证据见[P014来源](../../work/evidence/P-014/license-sources.json)；本包不捆绑权重。已有P014缓存可直接只读使用。

将下列三个实际路径替换后运行：

```powershell
uv run --locked --no-sync python -m bioimage_app.nuclei_cli --source "C:/research/original.tif" --workspace "C:/research/new-nuclei-workspace" --worker-python ".local/nuclei-research-env/Scripts/python.exe" --model-directory "C:/research/models/2D_versatile_fluo"
```

成功最后一行JSON为`phase=finished,state=succeeded`，退出码0，`outputs`给出**已提交**labels和provenance路径；其他情况退出非零，`failure_reason`/`stop_reason`给出原因，不返回成功结果路径。缺模型提示显式准备，不自动补齐。工作区必须不存在或为空，重复运行请选新目录；本入口不修改旧结果、不启动GUI。Ctrl+C沿既有取消/进程树退出/存储仲裁，等待最终finished后再操作目录。

## 结果与边界

- `labels.npy`为原图YX坐标的uint32实例ID矩阵，0为背景，核数为不同非零ID数。读取使用`numpy.load(path, allow_pickle=False)`，不可把实例ID当荧光强度。通用端口使用`analysis_result`，dtype/shape/frame在provenance中明确；本任务未扩共享图像schema。
- `provenance.json`保存原始输入摘要、固定方法/全环境版本、模型摘要、尺度与百分位、标签摘要、请求身份和核数。`state=valid,nuclei_count=0`是合法空结果，异常不会伪造此结果。物理像素大小UNKNOWN。
- 方法固定`stardist-fluo-p014@1`：scale0.5、p3/p99.8不clip、2×2 tiles、CPU线程4/1、原模型阈值。StarDist负责逆尺度映射；宿主不再缩放标签。修改这些值必须新方法版本，不静默重算历史。
- 2,000,000像素/16MiB输入、16MiB单模型成员为工程准入预算（P014最大1,392,640像素），不保证任意预算内图像成功或内存上界。默认300秒（可设1..3600）在输入准入后启动工作流期限，超时记cancelled/deadline；无额外内存硬限制。进程强退后的临时模型快照由现有宿主临时目录收尾。
- 固定研究环境与默认桌面Pillow版本不同，工具兼容12.3..13但worker强验13.0及完整固定环境。默认导入不加载TensorFlow；`typings/`仅为固定外部API提供静态类型声明，未消除实际缺源码的三个Pyright警告；真实模型另行验证。
- Windows本机真实模型证据、完整命令和限制见[P015任务](../../work/tasks/P-015-nuclei-research-adapter.md)和[证据](../../work/evidence/P-015/README.md)。Linux普通边界/隔离wheel检查不等于Linux真实模型验收。

P014图像已经用于研究，当前对照仅证明工程封装一致性，**不是新独立科学验证**。训练数据重叠、患者独立性、真实实验室、学生使用和16bit适用性仍未知。没有IF强度、全细胞、统计或Agent能力，也没有发布安装器。


P016增加公开 `NucleiDisplay`、`original_png`、`present_nuclei_result`：从宿主已验证提交的原图、标签、出处和冻结请求生成原坐标显示PNG，并交叉核对来源/标签摘要和核数。显示变换不回流推理；算法/参数/方法版本未变，新增源码使implementation digest自然变化。已有P015结果可只读重开，不要求历史worker仍安装。实际桌面入口见[单图操作指南](../../docs/runbooks/nuclei-single-image.md)。

## 已有核结果的配对通道强度

在项目根目录运行。先确认两张原图来自同一视野，方向、裁切和每个像素的位置一致。尺寸检查无法验证物理配准。将路径换为已完成的单图核计数项目、目标通道原 TIFF 和项目外已有的导出目录。

```powershell
uv run --locked --no-sync python -m bioimage_app.nuclei_intensity_cli --workspace "C:/research/nuclei-workspace" --target "C:/research/PH3.tif" --output-dir "C:/research/exports" --confirm-same-frame
```

命令输出新目录下的 CSV 路径。每个非零实例保留原 ID，面积为像素数（px²），均值为原始 DN，积分为像素 DN 之和（DN·px）。零核生成仅有表头的 CSV。相邻的 provenance.json 保存方法版本、项目运行、原核图、标签和目标图摘要，供复查。仅接收原坐标单页 uint8 灰度 TIFF，保留原背景和曝光标度。跨样本比较、背景校正及阳性判定均在此方法范围之外。
