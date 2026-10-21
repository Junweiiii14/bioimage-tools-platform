# T075 验证与交付证据

候选 `5c56f5509e8ad9381420e26af059e9c60501ebbb`；产品基线 T074 `0376f23`。本机安装与还原已完成，交付独审通过，必需 CI 失败定位中，暂不标整项完成。

| 本轮最终检查 | 结果 / 证据 |
|---|---|
| 构建与安装 | 构建0、安装0；独立5c56f55目录，`build-manifest.json`含安装器/运行时/四wheel摘要 |
| 资源与载荷 | `resources.json`：34前端source/wheel/install相等；`installed-validation.json`：7780载荷相等 |
| 固定状态还原 | `fidelity.json`：26PNG逐像素相等、字体/尺寸/文案/状态records相等；Windows Qt6.12 / Chromium140，DPR1.5，未禁GPU |
| 真实安装业务 | 私有Python -I，146产品/Qt磁盘模块为安装目录；高级四工具保存/重开/导出、跨窗appearance、合成IME基线3项20.75s，pytest与外层均0 |
| 中文新快照补验 | 原IME publish可能去重；单独强制新revision，断言真实stateChanged与网页revision均到达后验证同节点/焦点/光标/草稿。1项3.91s，外层0，详见installed-validation.json |
| 安装主链 | PS5.1 selfcheck实际0；19命名检查、自动处理/矩阵/导出重开/所属资源关闭均通过，11.391s |
| 动态与缩放 | 同源动作序列、真实CDP指针移动，安装278帧/7.99s+尾帧；DPR1.5和2.25各109帧间隔，中位16.7ms，P95≤16.8ms，console空 |
| 即时反馈 | `input-response.json`：拼图/设置/主题真实CDP点击，下一帧19.2/13.5/9.6ms且状态正确；不是物理输入延迟 |
| 代码独审 | fa746fa三问题→1d872bf修复/Accepted→edafe65裁剪标签→e8只读revision/错误重试→5c56只读busy，各绑定报告随本目录保留 |
| 有界视觉独审 | 初轮四项＋直接裁剪标注回归，最终edafe65限定范围ship；后续前端仅加载错误反馈，不扩张装饰审查 |
| 诊断复现工具 | capture_workbench.py同步正常preview session refresh，冻结保存标签状态；Ruff check/format通过，不改产品或图片 |

原始安装日志、自检JSON、JUnit、来源清单、PNG与录屏保留在报告列出的本机绝对路径。代码、字体、资源摘要和简要结果入库，生成安装包/图片/科学数据不入库。

## CI180（未通过）

Windows job119423218848：1 failed/1191 passed、746.36s、原pytest exit1；既有test_rotation_preview_and_one_real_click_commit[False]的4.8输入/真实命中复合断言失败。Ubuntu job119423218306：既有test_repeated_window_close_and_collection等待resources_closed时挂起，60秒Python栈在worker retire、storage emit、Qt waitUntil；15分钟runner取消。两个job均未完成wheel。原日志.local/t075-ci180-{windows,linux}.log；run39657811667。新诊断仅将原两项布尔断言的同一JS求值结果附上字段，不改预期/容差/skip/timeout；本机相关三项4.57s通过，未认定远端根因已明。

## 保留的真实失败和边界

- 初轮QWidget.grab滞后、旧主题状态与未冻结顶部回执不能作还原通过；最终CDP与正常session refresh重新建立有效基准，没有像素后处理。
- edafe候选首次GCC长路径头文件查找失败；完整同版11602文件复制短路径且摘要相等后重建，失败目录仍保留。
- edafe安装高级工具保存后立即open暴露主快照滞后；e8只读revision修复。e8又抓到后台来源读取busy拒绝，只读open解除busy限制，写入仍严格，5c56实际安装链路通过。旧候选不能替代本轮结果。
- 首安装来源审计误把Qt嵌入的相对shiboken模块当磁盘文件，测试通过但外层失败；诊断分类修正不放宽产品/Qt磁盘路径核验。
- 原appearance+intake联跑D3D访问异常根因UNKNOWN；成功运行中的SharedImage mailbox日志保留，不据后继通过认定所有原生问题已修复。
- 干净Win10、物理输入/缩放、独立科学留出保留；不合并主分支、不公开发布、不删除旧安装。一次HTTP预览服务启动被自动审批拒绝，未绕过，使用本地同源HTML文件。

# 实施初期记录（历史）

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
