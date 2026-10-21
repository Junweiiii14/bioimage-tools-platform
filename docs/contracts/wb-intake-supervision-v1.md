# 批次曲线复核与整版网格 v1（T074）

数值计算沿用原像素 AnalysisRequest / update_quant_lane / analyze_annotations，不添加数值策略或显示预处理。显示直接复用 manualQuant.chart：完整采样、原有峰底、积分边界、填色及质量标记。调整保留几何 local_signal_ambiguity 警告。

revise_intake_quant 检查稳定蛋白/泳道/条带身份及所属 Fig 已完成成图；只将目标 Fig 测量与输出阶段置回 pending，保留其他结果。桌面先保存请求，再由现有批次执行器重算；旧回复受 project/session/revision/generation 和取消状态保护。未保存草稿留在页面内存；失败不宣告成功，旧输出目录不改写。

schema15 在 schema14 基础上增加 grid：policy=intake_grid@1、columns 1–12、gap 2–1000 输出像素、order 全部稳定 Fig ID 的排列（空表示清单顺序）。保存网格才升级版本；旧1–14仍读取，旧应用拒绝15，修改前保留项目副本。默认 min(3,N) 列、40像素间距。

render_intake_grid 只读取 SHA 验证过的已保存单 Fig 图像，沿用其泳道显示尺度；不缩放、不拉伸、不改变定量。列宽/行高取各列/行最大值，顶边/左边对齐，其他白色留空，不跨 Fig 对齐同名蛋白。32M像素/单边32768上限；缺 Fig 拒绝宣告完整，界面列出缺项原因。

单 Fig、总图导出均不覆盖已有文件。总图预览及 PNG/TIFF 使用同一 FigureRender；完整输出新增 all-figures.png、all-figures.tiff、all-figures-layout.json 并纳入成员索引。缺项为部分输出。网格保存只使输出过期，不使单 Fig/原像素结果失效。

拼图左侧点击 Fig 切换成图、点击蛋白定位；进入裁剪必须明确使用“修改裁剪”。单 Fig 与全部 Fig 均可缩放/适应窗口；每行数、顺序和间距在右侧修改并保存。
