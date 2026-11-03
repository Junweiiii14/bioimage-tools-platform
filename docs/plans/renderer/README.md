# 研发文档HTML构建

当前构建器为build-v42.cjs，固定使用package-lock.json中的marked 17.0.5，不增加产品依赖。

```powershell
npm ci --prefix docs/plans/renderer
npm run build --prefix docs/plans/renderer
```

生成五份同名HTML，正文、样式与脚本可离线阅读；本地参考链接依赖仓库对应文件。使用系统字体，无外网字体请求。可通过浏览器打印保存PDF。

旧build.mjs仅重建4.0历史方案，输入固定为research-platform-reference-v4.md，输出限.local/deliveries/historical-v4，不能覆盖当前HTML。旧构建产物与校验不作为新版通过证据。
