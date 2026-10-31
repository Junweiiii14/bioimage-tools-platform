# 研发方案HTML构建

使用Node 20或更新版本。仅文档构建器依赖marked 17.0.5，固定在本目录package-lock.json；不改变产品依赖。

```powershell
npm ci --prefix docs/plans/renderer
npm run build --prefix docs/plans/renderer
```

从docs/plans/research-platform-rd.md构建同目录HTML。仓库版引用已有web_ui/fonts/NotoSansSC-VF.ttf，避免重复提交24MB字体内嵌文件；克隆后离线打开即可。单文件便携版运行`npm run standalone --prefix docs/plans/renderer`，产物在.local/deliveries/B-008，不入Git。正文内容和许可证不省略。

本目录构建器替代B007本机临时构建脚本；旧审查摘要仍绑定其旧产物。发布时应重新检查相对链接、标题/数据和字体加载，不能把旧产物的哈希当当前HTML通过证明。
