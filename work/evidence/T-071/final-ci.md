# 最终门禁及增量

## a952555 本机完整门禁

`uv run --locked --no-sync python dev.py check --all`，现有CI原生观察/BIOIMAGE_NATIVE_STACKS=1/BIOIMAGE_WINDOWS_FAULTS=1、offscreen/disable-gpu、verbose/faulthandler。979 passed /825.65s，原始child0/u32=0，全部独立wheel/桌面存储及进程/真实OCR与PNG OCR/整命令实际0，2026-10-21T01:56:09+08完成。本地日志t071-final-fullcheck-v3.log及process.json，启动绑定a952555；随后提交a541b68仅两份Markdown。pytest979及全部wheel构建完成后、尾部验证附近开始编辑下述诊断观察，其他生产/测试/门禁不变。因此完整结论只绑定a952，不声明5f被该门禁覆盖；5f由专项及下述新CI独立覆盖。

## a541b68 远端失败保留

- quality39469038484，Linux job118787923625：978通过/1失败，398.84s、debugger1，wheel未运行。新增序列诊断第二个review点击被busy保护拒绝（1.05s），不是原值/屏障断言失败。
- Windows job118787923320：978通过/1失败，619.40s、原child1/u32=1，wheel未运行。旧test_manual_lanes_workbench真实Qt指针框选获得(39,42,16,38)，原预期(35,40,20,40)/abs1。原归档close用例已越过，但不据此消除历史native UNKNOWN。此次坐标偏差没有足够现场矩形证据确定根因，保持UNKNOWN，不增加容差、不改原值答案。
- 两份完成job日志经API实际0保存.local/t071-ci-{ubuntu,windows}-a541.log；规则和桌面环境检查成功不能替代两项失败。

## 诊断请求时序修正

仅安装诊断观察器：QWebChannel发出的请求与JavaScript求值回调是两个异步通道。页面已返回click不表示桌面槽已收到；自动选源请求也可能仍在途。临时页面包装器原样转发bridge.request及原回调，并在实际槽回执后归还在途计数。人工修正仅在没有在途请求且页面就绪时点击一次；点击后等待槽回执与原持久提交，仍无修正即失败。没有自动重试被拒点击、生产调度/UI/存储更改、延长120/150秒或25ms轮询。

局部首次尝试错误要求原生视图selected/source_preview，WB清单页不保证该原生视图预览存在，导致4通过/1诊断超时（152.35s实际1）；已删除该错误前置条件，不掩盖失败。最终真实-I两Fig发货页面诊断1通过/11.68s实际0，仍有全部13检查、两个真实worker、逐目标屏障、原像素/输出/重开/所属销毁要求。静态初稿私有字段/错误方法名被Pyright拒绝，最终不访问这些字段；格式修正无规则忽略。其后增量独审及最终四CI结果见下节。

## 5f2090a 最终四检查与集成

- 未修改旧手动泳道测试的预期、容差或产品坐标；本机定向1 passed/18.84s实际0，仅未复现，不将a541偏差根因改为已明。
- quality39471789384：Linux job118797435037，979 passed/332.14s，inferior正常、debugger0；Windows job118797434748，979 passed/615.77s，原child0/u32=0。两者均完成全部四wheel、安装烟测、真实OCR/PNG/static worker及完整check0。完整job日志API读取实际0，存.local/t071-ci-{ubuntu,windows}-5f2090a.log。
- rules-context39471789387与desktop-environment均SUCCESS，四必需检查齐全；可选native-case的SKIPPED未记成成功。`gh pr merge 30 --merge --match-head-commit 5f2090ad05af6ce6d427b43e428916cefba3df7f`实际0，2026-10-20T18:18:14Z正常合入main710bb85de99e88a970f4d0f5613ca554b705ecf7，没有绕过或改写成功状态。
- 非作者独立读取两份原始日志、Git/API均0：main710bb与获审5f整棵tree相同（77cd85513c881685d0a2ca391f70b443b92046c0），Accepted。旧坐标偏差/native UNKNOWN仍保留，不以此次成功宣称根因已解决。
