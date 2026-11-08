# P027 参考组选择与草稿冲突独核

提交 `4168f9c4b9d55f1fbc67b124244be15f0c0393da` 相对 `8321615773c73ede412e1a60b2688e545f537f8a`。该范围通过。独立测试使用审查树锁定环境、offscreen WebEngine、实际工作台控件、WebChannel、来源识别任务、持久化与正常关闭。输入为两份小型合成 TIFF，一张可识别为横向参考成品。字体目录指向 Windows Fonts，软件渲染。所有项目与设置均在本目录。

## 后台更新时保留已有编辑

候选先保存 Fig 与蛋白草稿，再从页面点击识别，在同一 JS 事件回合实际修改名称，早于后台回包。真实识别更新后，本地保持新名称、显示冲突并禁用保存，已提交名称保留旧值。显式重载后，点击“单列已识别的参考结果”并保存成功；参考组 ID 与识别证据一致，没有蛋白或裁剪源，普通组原有蛋白与 Fig 均保留。关闭后只读 SQLite 核验 revision 3 的资产摘要及分组内容。证据为 observations.json、disk-check.json。

`python.exe -I -B -X utf8 -m pytest -q --tb=short --show-capture=no -p no:cacheprovider .local/references/test_refs.py --basetemp=.local/references/run-3`，1 passed / 5.20 s，exit 0。前两次测试使用了同一段独核 JavaScript，将换行置于 return 后导致自动插入分号，断言得到空值，两次 exit 1。修正独核表达式后通过，第二次短 traceback 见 run-2.log。

## 已选原图后来被识别为参考成品

候选与基线均先将一张宽图作为 Target 的原图真实选中并保存。点击来源识别后，基线额外出现无编辑的清单冲突，需要显式重载，候选直接继续。点击“单列已识别的参考结果”后：

1. 原选中来源保留，参考组退出 Fig/蛋白顺序，侧边有“取消原有裁剪源选择”。页面提示“参考结果仍有裁剪源选择，请在参考区取消选择。”开始禁用，保存仍可点。
2. 尝试保存，后端拒绝参考成品作为裁剪源，界面显示失败，已提交摘要未变。本地草稿保持，取消原有源的按钮仍可用。
3. 点“取消原有裁剪源选择”并保存，参考标记、普通组的蛋白与有效来源均写入磁盘，页面恢复可编辑。两版各自关闭后，SQLite revision 3 所指资产逐字节摘要及分组相等。

第 2 步的可点保存是基线已有的可恢复反馈。候选移除的初始化行只改变第 1 步之前的假冲突，不降低后端来源验证。产品增量只有 intake_groups.js 一行，因此基线实例使用相同 Python 代码并从 git 准确基线取原 JS，其他界面文件逐项沿用两版共同内容。关键位置为 intake_groups.js:26、150、157、211、261、576 和 instrument_intake.py:639、687。

`python.exe -I -B -X utf8 -m pytest -q --tb=short --show-capture=no -p no:cacheprovider .local/references/test_preselected.py --basetemp=.local/references/preselect-run1`，2 passed / 6.39 s，exit 0；日志含 QtWebEngine shared-image mailbox 消息。见 preselect-run1.log、preselected-base.json、preselected-candidate.json、disk-check-preselected.json。只读 SQLite 复核 exit 0。未操作可视窗口或用户数据。
