# T-047 验证与候选安装记录

环境：本机 Windows、锁定 Python 3.12.14 环境；仅 t045 候选 checkout。原 ResearchVault 工作区、原版入口、私图和用户现有窗口保留。预览经用户明确批准后实施。

## 源码与独审

- `d6c8127`：统一项目入口、原图/项目文件夹分流、导入直达灰度、最近项目/页面位置恢复、同窗切换宿主、session epoch 拒绝旧回调、关闭协调与并行候选安装配方。
- `90ae634`：ICO 生成改用 RGBA/Pillow；PySide6 QImage.save 字节格式重载实际失败，最小实验已复验。
- `53a2030ba62f97247f10595b78b9b526b8007d2d`：独审 P1 修正，取消结束后重新评估未应用草稿及未保存修改，不直接进入关闭。新增安装诊断覆盖保存失败恢复、项目重开和真实任务取消后的确认。
- 入口/桥接/文件夹/启动回归33项，42.02秒，exit0（90ae 产品）。后继会话8项12.05秒exit0，覆盖新取消路径。最新 Ruff、格式、Pyright、Node 检查均 exit0。
- 源码自检 v4：7.265秒exit0；合成16位TIFF→真实两泳道worker→离线OCR→原图SHA核验→保存失败窗口保持可见→返回首页→重开同一保存项目→真实worker退出取消→草稿确认→未保存确认→保存并实际资源关闭。报告 `.local/t047/source-install-check-v4.json`，不读取用户私图。
- fresh reviewer 对90ae审查发现两项：取消后草稿确认缺失、安装版实证未完成。53a2030复核仅关闭第一项；第二项须待真实编译/安装证据，不宣告 ship。

## 视觉与边界

实际项目副本106行/33Fig执行打开、同窗首页/重开恢复及1600/960/390宽度截图。未保存确认的离屏Qt抓图遗漏HTML顶层dialog，因此另以真实Qt DOM快照在IAB渲染；仅证明界面外观，不冒充原生操作/进程退出证据。截图和私有项目副本只保留ignored目录。设计检测运行一次，既有token漂移不据此修改获批布局。

## 失败与未完成项

首轮完整检查因新测试未标注lambda被Pyright阻挡，未运行pytest/wheels；已改显式注解。新增旧epoch测试曾缺json导入；目录测试曾停在新增系统选择器，已显式测试取消路径；没有缩减生产门禁或放宽时限。

源码诊断v1终止exit1而报告未完成，精确原因UNKNOWN；v2明确失败于未绑定目标；v3/v4通过不追溯抹去旧故障。Qt离屏GPU mailbox/context日志与历史原生崩溃保留。

编译v1图标转换exit1；90ae编译v2为防止编译期间源码改变而停止自有编译树，实际compile_exit4294967295、260.579秒，未产生成功安装包。53a2030完整编译v3进行中。

完整门禁v2的pytest768项664.24秒通过，隔离wheel仍在执行；该次pytest基于90ae加载，新增取消回归另有53a2030证据。最终源码检查、最终安装产物/摘要/退出、桌面/开始菜单快捷方式及独审第二项仍待完成。干净Windows、原生按钮/DPI没有验收结论。

编译v3实际exit1、386.687秒，Nuitka报告只有onnxruntime元数据而未收录动态后端包。配方显式加入onnxruntime包后重建，不删减OCR。完整门禁v2全部结束exit0（768pytest及全部隔离wheel），最终53a2030门禁v3正在运行。独审复核已关闭草稿P1，安装实证仍待完成。

最终源码完整门禁v3已结束：769passed659.96秒，所有隔离wheel、真实OCR worker及PNG OCR检查、dev/check最终exit0。产品及科学代码对应53a2030，后继6325623仅增加显式ONNX后端打包与文档。完整编译v4仍在C阶段，未安装。

安装v4成功但验收未通过：桌面/开始菜单/卸载及EXE哈希核对通过；真实OCR worker因RapidOCR延迟导入模块未收录而failure，已显式收录完整rapidocr。初始化自检normal/offscreen均exit3且报告空白，UNKNOWN；增加显式诊断检查点与异常持久记录。不宣称可用安装通过，不启动交付。控制器SYSTEMROOT大小写错误单独保留，非产品错误。

## 最终本机候选交付

产品b6df40edf2beb560971fee9f8ac94d1381d265ff采用private-cpython-locked-wheels，原生启动器GCC -Wall/-Wextra/-Werror退出0；Python类型/静态/格式检查0。安装包360638287字节，SHA256 `37865a43f7eed96be4ec410628814c8990c634a755c5636bdbf2414a3bcb18bc`；安装exit0。启动器摘要 `9be99393b4de771f40c81195dd52b224793bc93e87ddcb95bd2a545d03316bcb`，私有Python摘要 `f7ab44f15f6067dc0613fb2b2aeff1287d4fa90b6fbe719f3574055bb11904ab`。

安装目录 `C:/Users/70236/AppData/Local/Programs/BioImage WB Candidate`；桌面/开始菜单 `BioImage WB（候选版）`。实际安装正常Windows窗口自检七检查11.516秒passed，控制器22.442秒/进程exit0，六个自有PID均退出，316个实际加载模块无开发目录路径。使用含空格报告路径验证启动器参数转发。真实OCR子进程在临时目录且PATH仅System32下识别Fig1A/AKT，定量错误协议exit2正确，stdout/退出码转发通过。精确 ignored 报告：`.local/t047/installed acceptance/final report.json`、`final report.json.process.json`，以及`.local/t047/installed-runtime-worker.json`、`installed-runtime-entries.json`。原TIFF/旧快捷方式摘要一致。没有运行卸载用户原版，仅卸载本轮失败AOT候选后全新安装本轮成功候选。

真实桌面快捷方式启动成功：`.local/t047/installed-user-launch.json`记录父55936/窗口55440，标题“BioImage WB · 候选版”、响应正常，保留供用户试用。源图片未自动导入此新首页。独审最终对b6df40e关闭第二项，ship仅本轮评分项，第一项先前53a2030已关闭。所有旧失败保留；原生物理按钮、DPI、干净Windows及科学留出仍未验收，无main/PR/对外发布。
