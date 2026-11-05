# P014 公开复现实验（进行中）

研究入口：[选型研究](../../../docs/research/2026-11-06-mature-nuclei-methods.md)。本目录不包含原图、权重或安装器；只记录研究配置、脚本和非私有结果。当前未完成独审/CI/集成，不代表产品或科学准入。

## 固定材料

- `dataset-plan.json`：730dd50先冻结3开发/10评估图；官方Kromp元数据来源和限制在研究文档。
- `development-plan.md`、`development-metrics.csv`：仅开发组比较CP两配置、StarDist三缩放，不训练模型或继续搜索。
- `frozen-config.json`：1866b47冻结最终选择；687e34a把日志显示的概率阈值补为权重文件中的完整精度，实际推理始终读取原权重阈值，没有改参数。
- `cellprofiler-frozen.cppipe`：官方4.2.8加载后导出的完整配置（DateRevision428），源于官方Human例的核模块，配置变化见prepare_cp.py和development-plan；不使用历史cp3流程。
- `evaluate.py`：原样复用P013已审计metrics函数。输入适配仅将非零实例ID压紧，不改变像素/连通性；在原分辨率计算严格IoU>0.5的一对一实例匹配。
- `requirements-development.txt`：研究隔离环境的完整精确版本列表；不是项目正式依赖。运行时为Windows11/Python3.12.14、CPU。模型及代码许可单独见license-sources。

## 复现顺序

从仓库根执行。以下`CACHE`代表自选仓库外绝对路径；所有运行结果使用新目录，旧结果不覆盖。需要官方CellProfiler4.2.8安装；本轮使用已有安装，未修改安装及既有设置。安装器来源见官方发行页，未在本研究重装。

1. `uv venv --python 3.12.14 CACHE/stardist-venv`，随后`uv pip install --python CACHE/stardist-venv/Scripts/python.exe -r work/evidence/P-014/requirements-development.txt`。
2. 用该解释器运行`work/evidence/P-014/fetch_public.py CACHE`，逐项校验输入/模型SHA256。它只下载清单中的公开材料，不解析任意模块，不改产品环境。
3. 按dataset-plan的evaluation名单将10幅原图复制至新的`CACHE/evaluation-input`，保留原始字节；不要把开发图或GT放进去。
4. 用该解释器运行`measure_process.py CACHE CACHE/cp-monitor "C:/Program Files/CellProfiler/CellProfiler.exe" -c -r -p work/evidence/P-014/cellprofiler-frozen.cppipe -i CACHE/evaluation-input -o CACHE/cp-evaluation -d CACHE/cp-evaluation/done.txt`。须先创建新的cp-evaluation目录，检查退出0、done为Complete及10图CSV/npy齐全。
5. 用同一解释器运行`measure_process.py CACHE CACHE/sd-monitor CACHE/stardist-venv/Scripts/python.exe work/evidence/P-014/run_stardist.py CACHE CACHE/sd-evaluation --group evaluation --scale 0.5`。
6. 用同一解释器运行`evaluate.py CACHE CACHE/evaluation-scores --group evaluation --prediction cellprofiler=CACHE/cp-evaluation --prediction stardist=CACHE/sd-evaluation`。调用脚本时均补上`work/evidence/P-014/`前缀。

先后运行两方法，不同时占用CPU。process.json的耗时包括启动/导入/输出，SD execution.json逐图耗时包含读取、归一化和预测；CP日志逐模块wall time可按图汇总。内存是50ms采样的存活进程树RSS之和峰值，可能漏掉短暂峰值/重复计算共享页，不等同精确独占峰值。例行Windows缓存状态未清空，不称严格冷启动基准。记录失败和不支持格式，不能填零或只留下成功行。

## 边界

CP从图像元数据缩放至其内部灰度范围并执行官方阈值/declumping；SD取相同原始像素（复制灰度RGB须逐像素三通道相同），按3/99.8百分位归一化，再由官方scale=0.5线性缩放和原坐标多边形输出。两者预处理不同，这是实际成熟管线对照，不是隔离单一算法变量的实验。没有利用显示图定量，也没有验证IF强度或全细胞。

BBBC039部分重叠DSB2018；本轮另用Kromp数据，但训练像素清单/患者独立性仍未完全核对。只称固定公开子集表现，不称独立泛化、学生可用或临床性能。最终选型和下一任务须以完整结果及独审为准。
