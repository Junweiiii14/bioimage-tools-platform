# T-042 验证记录（进行中）

环境Windows、Python3.12.14、锁定uv/SciPy/NumPy/PySide6；依赖锁未修改。base b32acff，产品提交cba80df、240bfdd、df375c4，最终兼容提交2980a0a已独审。

- source_geometry最初39项相关测试exit0；后续Marker/显示框/边界/worker协议27项exit0。最终独审df375c4复测12项exit0，首轮3问题和增量2问题均修复。
- Ruff、格式、Pyright0错误、policy提交钩子均通过；最终增量类型检查0错误、smoke-env与policy exit0；完整check --all进行中，不能声称完成。第一次exit1是测试脚本格式问题；第二轮约72项后无进一步输出，专属测试进程停止，未判全通过；第三轮加-vv/faulthandler诊断运行中。
- 源图API回归 frozen-v4 为8/8（旧1/8），逐图标准和限制见crop-scoring.md；新边界frozen-boundary-v1同样8候选、保存重开相等。
- 正常网页工作台workbench-web-v3：8原图→8成功run→正常导出→保存后重开相等→原图SHA不变，exit0。使用WebWorkbenchWindow与正常host服务，不注入ROI/N/结果。先前误开旧Qt验证窗口已关闭，网页HTML/CSS没有变更。
- 网页重开结果页另检：48后台cells、48渲染数值按钮、busy=false，capture_workbench.py exit0；截图.local/t042/workbench-results.png。参考未进入以上处理。
- 中间失败保留：原生验证v1/v2终止；网页v1保存前revision比较误设；网页v2发现新边界质量flag被worker协议拒绝，8次中7次interrupted，绝未计作成功。df375c4补版本化flag校验与协议往返后v3成功。
- 真实积分48槽仅作为边界诊断，不报准确率；支持不足、相邻信号与原像素位深极值仍需复核。未恢复饱和区线性信息，未自动猜实验蛋白/配对。输出中的Unassigned保留未知语义。

所有本地证据位于活动工作树.local/t042；私有原图、参考图和生成成果不进Git。旧工作区/旧结果未覆盖。未发布、未合并main、未做干净Windows验收。

最终独立审查见independent-review.md，2980a0a兼容增量3项独立测试exit0。所有发现关闭，审查未代替完整门禁或科学泛化验收。
