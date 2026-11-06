# 核分割首次准备

供环境维护者使用；普通分析在工作台选择原图后运行。软件不会自动下载模型。以下命令在本次源码仓库根目录运行。



在仓库根完成`uv sync --locked --all-groups`。以下使用**新建**的研究环境，避免改动已有实验环境；重模型依赖不进入默认桌面依赖。Python固定3.12.14，依赖清单沿用P014并补固定Pydantic契约依赖。

```powershell
uv venv --python 3.12.14 .local/nuclei-research-env
uv pip install --python .local/nuclei-research-env/Scripts/python.exe -r tools/nuclei/requirements-research.txt
uv build --package tool-contracts --wheel --out-dir .local/nuclei-wheels
uv build --package nuclei-tool --wheel --out-dir .local/nuclei-wheels
uv pip install --python .local/nuclei-research-env/Scripts/python.exe --no-deps .local/nuclei-wheels/tool_contracts-0.1.0-py3-none-any.whl .local/nuclei-wheels/nuclei_tool-0.1.0-py3-none-any.whl
```

模型由用户明确准备；运行时不下载。固定来源为[StarDist models v0.1](https://github.com/stardist/stardist-models/releases/download/v0.1/python_2D_versatile_fluo.zip)，ZIP SHA256 `4ad678d0758eed6e55625f1b5ae30771e59adb79f1239e09b9772eac8846c3dd`。将已核验的`config.json`、`thresholds.json`、`weights_best.h5`放入专用模型目录。三个成员摘要固定于`domain/method.py`，运行时检查原目录及私有快照。许可为BSD-3-Clause，准确版本及证据见[P014来源](https://github.com/Junweiiii14/bioimage-tools-platform/blob/1c819aeaae9813fdc29606cbad463b08a191fbab/work/evidence/P-014/license-sources.json)；本包不捆绑权重。已有P014缓存可直接只读使用。以上链接在默认浏览器中打开。


准备完毕后返回运行设置，选择 python.exe 和模型目录。研究适用性尚未独立验证。
