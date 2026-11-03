# F008 依赖候选核验

2026-11-03，Windows/PowerShell，基线 main 6e0dcd44ae726caffa9215da49bcf569737258cd。只有构建/CI依赖及任务证据变化，无产品源码、科学方法或测试变化。

## 遗留问题与处理

- PR4/PR20 实际失败是缺少唯一规则回执；现有产品 CI 已通过但不能代替本次组合候选的检查。
- PR5 停留在旧主线及旧交接，保留其历史，重新在当前主线应用相同 setup-uv SHA。没有覆盖新工作流或带入旧 snapshot。
- 三项升级在本 PR 的 diff 可逐项检查；成功合并后原 PR 标记由本 PR 替代，不先关闭未完成的升级。

## 来源与差异审阅

- checkout 固定 `3d3c42e5aac5ba805825da76410c181273ba90b1`（v7.0.1），来自 PR4。[发布说明](https://github.com/actions/checkout/releases/tag/v7.0.1)包含 unsafe PR 检查、ASCII空白处理及unset值转义修补；[action.yml](https://github.com/actions/checkout/blob/3d3c42e5aac5ba805825da76410c181273ba90b1/action.yml)运行于node24。本项目保持只读pull_request、persist-credentials:false，未开启allow-unsafe-pr-checkout。
- setup-uv 固定 `37802adc94f370d6bfd71619e3f0bf239e1f3b78`，沿用 PR5 经查证的候选。[提交](https://github.com/astral-sh/setup-uv/commit/37802adc94f370d6bfd71619e3f0bf239e1f3b78)将默认下载改为Astral镜像、失败回退GitHub，校验逻辑保留；node24。此次覆盖现行三个job中的相同引用，uv CLI仍固定0.13.0。
- 四个包的构建后端从uv_build==0.13.0升至0.13.6，和PR20一致。[官方发布](https://github.com/astral-sh/uv/releases/tag/0.13.6)。不将CLI发布说明中的所有变化当作本项目后端变化；兼容性以当前wheel构建/安装检查为准。
- uv.lock无变化：构建后端要求位于四个pyproject的build-system，不是运行时依赖升级。`uv lock --check`退出0（83 packages）。

## 验证记录

- 当前范围context：退出0，已读取核心规则、任务及模块说明；实际使用已有bioimage-v0环境的Python执行当前工作树dev.py，没有借用其产品实现。
- `git diff --check`：退出0。
- 作者检查不冒充独审；无产品代码变更。完整双平台、桌面环境及规则检查将由本PR准确提交CI执行，未结束前不写通过。
- 主仓库交接与清理清单在B018统一维护，避免依赖分支写入过时产品指针。
