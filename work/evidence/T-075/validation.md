# T075 实施期验证（未交付）

环境：Windows11，Python3.12.14，PySide6 6.12.0 / Chromium140.0.7339.225，uv.lock 固定依赖。基线0376f23＋本任务未提交工作。下述结果只覆盖当时相关文件；最终提交独审、CI和安装版验收尚未运行。

| 检查 | 结果与限制 |
|---|---|
| 核心修订/元信息/分组/外观相关40项 | exit0，5.92s，初版相关范围 |
| 新核心修订6项 | exit0，2.50s；含最新sequence v2、真实已发布输出保持逐文件摘要 |
| 新网页高级协议测试 | exit0；真实 worker/CAS、导入后保存回执与重开 |
| 真实网页四工具保存/导出/重开 | exit0，6.46s；加入并发标量冲突确认后6.44s exit0 |
| 受影响网页6项 | exit0，4.63s；矩阵/排序/后台草稿/阅读位置/小窗口 |
| 受影响产品模块Ruff/Pyright | 修正缩进与类型后0；后续新修改仍需最终相关检查 |
| 全JS syntax | 初次演示exp语法修正后0；后续新修改仍需最终检查 |
| Qt静态捕获 | QWidget.grab 离屏和windows均有滞后，不能验收；本机CDP探针成功，首有效26图在.local/t075-visual-valid；主题需真实按钮重取 |

真实失败：appearance+intake_web_ui 联跑在约第11项后Windows Chromium D3D read-access/access violation退出1；软件渲染只用于定位，不改变生产GPU参数。新并发冲突测试最初未按宿主协议递增fixture generation，修正fixture后通过，未放宽冲突断言。元信息分页、固定footer和后续视觉修正须补相关确认。

Qt测试/截图stderr含SharedImage/GLES环境警告，成功断言不等同原生异常全部归因。未运行：最终完整必需CI、绑定提交独审、源码-wheel-安装比对、候选安装及物理高缩放验收。

收尾增量：6项高级/外观10.27s exit0，迟到读取回执不覆盖新设置面板；全部JS syntax通过；13个相关Python Ruff format/check、5个新增/改动模块Pyright exit0。组件示例 components.html 共用正式 CSS/字体/motion。原生Windows（GPU启用）DPR2.25、110帧rAF中位16.7ms/P95 16.7/最大16.8ms；样本为设置抽屉及切页，rAF不是绘制帧完整证明。
