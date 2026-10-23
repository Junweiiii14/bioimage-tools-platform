# 已完成 PNG 项目页面状态诊断

环境沿 T080：Windows、Python 3.12.14、锁定环境，基线 HEAD
`2d2c9727ec93c7a625e46964696788f06f8f4834`；未提交工作树。
Qt 串行，`QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu`。

主任务真实续跑保留 `.local/T080/real-project-resume.log`：180 通过，PNG 后端全部
阶段 done、交付 complete 且六个最终文件存在，但脚本等待 `mode==='results'&&!state.busy`
超时。该失败记录没有覆盖，也没有重做已完成的测量、裁剪或导出。

只重开一次既有 PNG 工作区，读取 host 与真实 WebChannel/JS 状态。0/250/1000/2500 ms
采样均显示 busy=false，automation.complete=true、paused=false，无 JS 异常。重开按
既有路由进入 intake，follow=false、key为空；点击结果页后 mode=results，完整项目、
完整拼图、灰度表、打开项目目录等六个可见按钮均 enabled。项目模型序列化在诊断前后
精确相同，没有再处理原图。原始私有路径和界面截图只留本地：

- `.local/T080/completed-png-ui-probe/before-explicit-results.json`
- `.local/T080/completed-png-ui-probe/after-explicit-results.json`
- `.local/T080/completed-png-ui-probe/results.png`

最小合成实验复现脚本时序：初始 session route 在 busy 之后到达时，原有 desktop
route 会推迟到空闲，再切到 intake；这发生在测试绕过页面、直接调用 bridge 的启动
方式。先等待实际网页和 session route 就绪，再开始，则终态按正常 follow 进入 results。
两个时序均断言 busy=false、complete=true；没有观察到完成后永久忙态。

普通用户必须先看到已就绪的页面才能点击继续，属于后一个时序。本次未据此改产品。
只修 ignored 真实续跑脚本：开始前等待 WebChannel、当前项目页面和 session 路由
就绪，截图前等待交付按钮解禁；不再把 native storage ready 当作页面 ready，也不
用固定 200 ms 延迟当作 UI 完成证据。已完成私有项目未重跑该脚本。

命令前缀 `uv run --locked --no-sync`：

| 命令 | 结果 | exit |
| --- | --- | --- |
| `pytest .local/T080/test_completed_png_ui_probe.py -q --tb=short --show-capture=no` | 1 passed，7.35 s | 0 |
| `pytest .local/T080/test_late_route_probe.py -q --tb=short --show-capture=no` | 2 passed，3.77 s | 0 |

诊断测试结束后 Qt 空闲。未新增产品修改，不外推正式安装包/干净 Windows 验收。
