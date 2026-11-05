# P016 验证入口

- [首条GUI真实点击](first-gui-run.json)：实际原生选择/模型分析/导出/关闭/新进程重开；46核、标签与P014逐像素相同、原图不变。首次轮廓截图为本机 .local/p016-gui-result.png（采集时文案“核数”，候选后续明确为“已保存核数”）。
- [实际模型异常回归](gui-regression.json)、[脚本](run_gui_regression.py)：Qt控制器/真实隔离模型；仅原生选择器替换，零核/缺模型/16bit拒绝/观察PID后取消/历史保留。与首条人工式点击证据区分。心跳最大间隔约63ms是本机单次观察，不是跨机器性能保证。
- 普通CI新增 test_nuclei_ui.py（4项）、test_nuclei_web.py（1项）、工具内显示零/非零与损坏出处测试（2项），不依赖TensorFlow或网络。小窗口960×640实际WebChannel的选择、缩放、缺设置入口和对话框范围通过。

独审、完整门禁、PR/main仍待完成。

## 依赖与门禁差异

工作台已直接装配核分割入口，因此把轻量 nuclei-tool列为bioimage-app默认依赖，避免原有只安装wb extra的工作台因缺轻量包无法启动；保留nuclei extra兼容。uv.lock仅增加该本地依赖两处，无第三方版本变化。默认不加入TensorFlow或StarDist。隔离wheel测试同步提供新依赖并断言资源随包、API来自隔离安装、未导入重模型；原检查和容差未删除/降低。

Impeccable context已运行。一次机械检测仅报告backdrop色彩advisory；色值逐字沿用现有module_compare.css，继承同一对话框外观，不引入全局token或重做设计。设计文档既有Platform字段不是规范枚举的预存漂移已发现，本轮不顺带修复。最终视觉独审待进行。
