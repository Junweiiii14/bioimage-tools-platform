# P015 研究适配器验收入口

已完成PR66/main a761284工程验收及正式回传；[最终交付](final-delivery.md)、[目标核对](objective-audit.md)、[最终验证](validation.json)。下方阶段记录保留当时状态，最终状态以任务卡/本段收据为准。

当前实现与状态以[任务卡](../../tasks/P-015-nuclei-research-adapter.md)为准。独立包、CLI和环境命令见[工具README](../../../tools/nuclei/README.md)。本目录不包含权重、原图或安装包。

## 已执行与待完成

- 21项新增用例通过（18工具、3宿主），覆盖原值、拒绝不支持输入、标签溢出/负值、零结果、冻结身份、取消与失败、旧工作区保护和真实轻量进程失败。严格类型0 errors，3个研究依赖不在桌面环境的源码缺失warnings保留。
- 初版真实worker在Windows卡于NumPy native初始化；独立最小探针在保持stdin打开时复现，faulthandler显示另一线程阻塞os.read。改为Python3.12支持的非阻塞pipe读取后通过；新增保持管道打开的回归，避免communicate关闭stdin掩盖问题。[Python官方接口](https://docs.python.org/3.12/library/os.html#os.set_blocking)。初次运行经300秒deadline被现有进程树取消，无输出提交，失败历史保留。
- `run_regression.py`用明确指定的研究Python与宿主Python运行，不下载/调参。实际14场景：9张受支持灰度原图逐像素/逐ID等于P014冻结直接调用，合法空图、缺模型、坏摘要、1秒期限取消、16bit拒绝。原图摘要前后相同；50ms采样观察的全部后代退出后不存在。未采样瞬时进程/峰值不作保证。第二轮补验host-owned模型暂存及失败原因可见，第三轮对独审修复后代码完整复验14场景。
- 这些是已见数据工程回归，不提高P014的科学结论；不包括Linux实际模型、GPU、16bit、真实实验室或学生独立验收。
- 首轮独审b1e348a发现signed TIFF准入和长异常协议两项问题，已修复并补反例，见[independent-review](independent-review.md)。全量门禁、最终增量复审a490d2e已通过（含显式venv入口修复）；全仓/PR66最终CI尚待实际收据；不能将本页视作已完成。

## 依赖和检查变更说明

`uv.lock`只新增本地nuclei-tool成员和desktop可选nuclei额外项，现有第三方版本未变；默认没有TensorFlow/StarDist。研究依赖单独`requirements-research.txt`固定P014全版本及共享契约的Pydantic依赖，worker逐项核验、请求记录整份版本摘要。新增包进入Pyright/pytest、AST边界、Import Linter、独立wheel安装；只增加检查，无测试容差/skip/xfail/忽略放宽。窄外部stub用于类型检查，不伪造实现。

临时模型快照放入现有WorkflowPreparation拥有的目录；退出确认、取消仲裁、候选资产校验和事务提交沿用现有WorkflowSession/RunSession/AsyncStorage/Workspace。平台与WB源码不加入核分割语义；仅桌面明确注册和独立CLI。

## 首轮全仓失败与定向核查

首轮dev.py check --all退出1：1717 passed/4 failed/10已有deprecated warnings，1274.55秒。三项旧旋转canvas用例在5秒waitUntil取像素超时，伴随SKIA/GPU上下文丢失；采用现有CI同样QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu和offscreen，原三项原断言未修改，定向3 passed/5.81s/exit0。未证明物理GPU根因解决，初次失败保留。首轮执行期间有独审修复，不作为最终候选完整证明。

第四项是Import Linter正例写死9条规则，本次实际增加两条规则应为11；修正预期为完整“11 kept, 0 broken”，同时为模拟图显式建立nuclei包，并新增4个跨层/跨工具/运行时的传递导入负例。原9个负例未删除，规则没有减弱；不是把失败输出改成成功。最终全量和CI将重新执行。
