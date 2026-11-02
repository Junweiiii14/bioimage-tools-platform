# P009 交付探针进展与保留失败

2026-11-03。产品源码仍为fb3e11f的编排实现；本轮只修改测量/安装探针及新增界面用例，不改科学方法、门禁集合、预期、容差或超时。

## 输入异常隔离

真实WebChannel绑定两张输入，第一张损坏TIFF、第二张有效triangle_u8。有效输入实际产出40.0，坏输入单独failed且有原因，批次completed_with_issues；坏输入没有伪造成果，两份输入字节保持不变。`.local/p009-web-input-isolation.log`，1passed9.48秒，退出0。不是科学准确率或未见实验图验收。

## 隔离wheel

第二轮`uv run --locked --no-sync python -m tooling.installed_wheels`退出0，完整`.local/p009-installed-wheels-second.log`。环境QT_QPA_PLATFORM=offscreen、QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu，分别在不装WB的runtime/app、独立WB与app[wb]环境，从构建wheel安装验证。新编排探针确认包内JS/CSS实际存在、模块路径位于sys.prefix，真正WebChannel编辑保存重开、4000.0→40.0两批、6个带PID的succeeded RunRecord、320像素节点位置、template_version1及共享CLI再运行40.0。旧全部probe和断言保留，没有跳过既有安装检查。

第一轮新探针错误地用app.quit反复驱动轮询，进入新WebEngine初始化后没有进展；未完成，不能算安装通过。仅在核对CommandLine包含本探针及父PID52988后，终止自建GUI PID29120；命令返回0，旧wheel执行handle随后退出1。`.local/p009-installed-wheels-first.log`保留。修正为旧GUI和新AUTHORING_SCRIPT在同一已安装环境的两个独立进程执行；新探针用局部QEventLoop等待，不反复退出QApplication，并显式等待存储关闭和窗口销毁。只增加-u让各探针stdout及时输出，未修改旧GUI断言或科学结果。新一轮退出0不能证明所有历史GPU故障已解决，GLES/shared-context日志仍保留。

## 正式测量首轮失败

准确冻结5d0c355，默认5+30的`.local/p009-perf-frozen-5d0c355`首轮退出1，没有overall成功报告。standard四主题node/preview共8组，各35条原始样本完整落盘；只完成1个控制预热，随后等待下一真实PID超时30秒，upper未运行。有效已完成组仅是相应局部证据，不能代替整轮完成。

重复注入的控制准备脚本在顶层声明const polarity，第二次声明使JavaScript未执行，且旧工具没检查返回true。修正仅给该准备块局部IIFE作用域，并确认其真实执行回执；不改变产品、采样数、终点、可信/前台/时钟/身份守卫或30秒等待。`.local/p009-perf-probe-r6.log`连续2轮控制诊断退出0，非正式分布；准备在新冻结提交、新目录重新完整默认采样，旧失败不覆盖。

诊断r1–r5和线程饥饿最小实验见performance-measurement.md；不将它们与本次顶层const问题或所有旧Qt失败统一归因。正式性能结论仍待最终完整数据，超线必须保留，不自动重试凑通过。

## 静态与剩余

相关Ruff通过，两个安装脚本独立编译通过，`.local/p009-refined-probes-types.log`为pyright0 errors/warnings，退出0。本轮没有本地全量回归。接下去完整测量、准确提交代码独审和PR/必需CI正常集成；科学/物理IME/干净目标Windows/DPI及用户体验边界继续保留。
