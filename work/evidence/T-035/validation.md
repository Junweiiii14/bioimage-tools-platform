# T-035 验证

环境：Windows，本地锁定依赖，协调工作树；产品基线 b253e34，核心20f571c、网页宿主96366e9。

## 用户指定原图

只验证用户指定的 G4-1（末尾11597）与 M2-2-2（末尾26751）叠加源图，均1344×1100 RGB8。排版A–E、未叠加仪器过程图与裁好副本均不作自动裁图验收输入。此前混合10文件的5/10不是此输入类型的准确率。

真实 Qt WebEngine + WebWorkbenchWindow 完整流程退出0；原图导入后自动建立项目、自动裁图、定量、拼图与输出，无逐图确认。

| 原图 | 泳道数 | 原像素ROI x,y,w,h |
|---|---:|---|
| G4 | 3 | 724,547,236,63 |
| M2 | 5 | 511,617,394,63 |

宽高遵循1.25×n，整数宽度最多0.5像素取整。两个输入前后SHA256一致；导出ZIP中的两张原值TIFF裁图均逐像素等于输入对应数组切片。原图未压缩或覆盖。显示缩放不进入定量。

真实DOM验证：自动完成进入拼图；点击G4拼图回到其原图；n从3改4，宽度236→315，高63不变；返回拼图重算；恢复n3后留存项目。两个样本通过不能外推任意图片100%准确率。

本地私有证据（不提交）：`.local/t035/verification.json`、`montage-final.png`、`resize-n.png`、`mobile.png`、项目与结果。浏览器交互预览端口50617只展示真实记录和本地草稿，科学计算由桌面宿主执行。

## 工程与界面检查

- focused pytest：test_web_bridge、test_project_entry、test_ratio_crop、test_ratio_crop_view，21 passed / 9.10s。新增测试初次失败源于fixture把项目建在原图目录内部，已改为独立输入目录，保留安全限制。
- 核心代理29专项、6兼容性用例通过；scoped pyright 0错误、ruff通过、Node语法通过。
- Impeccable finish reviewer：ship，无material fix，保持既有三栏构图。detector运行一次退出1，含既有token/小字号、动态img src等提示；没有宣称静态检测零问题。
- 最终 `uv run --locked --no-sync python dev.py check --all` 退出0：582 passed / 222.28s，ruff/format/pyright/import contracts及隔离wheel安装与桌面/OCR探针全部通过。日志.local/t035/check-all-final.log。
- 未执行远程CI、PR/main集成、干净Windows验收；高级曲线/OCR/模板网页迁移不属于本轮。

## 最终增量

- 25ac71d独立复审：空泳道metadata与历史n冲突的P2已关闭，无新增可行动问题；18专项退出0 / 9.10s。
- 最终提交两原图再次端到端退出0；Node语法、最终pyright 0错误退出0；浏览器reload默认拼图且两张溯源按钮可见。
- 首轮全量静态项通过、581 passed / 227.86s，但整体退出1且无异常文本，不记门禁通过。最终独占复查退出0；首次异常根因UNKNOWN，保留记录。
