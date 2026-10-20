# T061 精简验证与交付

## 冻结产品

产品710836e65521cf570a8407cdcc6799620a2d1701，base main8c1ca85。静态ruff/728格式/严格类型/9导入契约/来源边界/冻结规则均0。非作者独立聚焦审查及v1摘要兼容probe0，无新增P0–P2；完整日志和最终截图补核接受。最终文档head规则/独审和四必需CI另以PR19记录，不把旧状态标成新head通过。

## 必要检查（不新增极端矩阵）

- 初次core20项：18pass2fail/9.34s，合成膜内纹理不足触发unknown；改纹理分位后新增4项/9.40s0。未修改预期/容差/skip/xfail或门禁。原通过16个旧清单用例未单独重复跑。
- Web相关11/11.31s0；精确回执调整后单项1/3.42s0。真实后台、原图导入/识别、明确确认、保存重开1/4.40s0。共新增6个参数化展开用例（4核心+1Web+1host）。
- 唯一本机完整 `uv run --locked --no-sync python dev.py check --all`：916passed/763.69s，原pytestexit0/u32=0，全部隔离wheel、真实离线OCR/PNG worker和最终检查exit0。环境：Windows11/Python3.12.14/Qt6.12.0，offscreen/disable-gpu、UTF8/unbuffered/faulthandler60、既有Windows native观察，未运行额外压力测试。后继仅收尾文档，产品/测试/tooling非Markdown文件与710相同，无理由重复本机全门禁。
- 一次机械设计检测[]。测试内首张grab抓到上一帧，未用作通过依据；另一次绘制同步的1280×720合成界面捕获 visible=true/overflow=false，非作者核对无阻塞布局问题。图片仅本地，不冒充科学真值或物理DPI验收；全局DESIGN/sidecar/token/intake.css不变。

## 真实图片与方法选择

82张TIFF，21三联组/19横条参考候选。旧几何算法在21信号候选上均未给出完整几何；新版白光约束后21信号组27区域，单次识别5.272665s，不含图册编码。冻结代码再核角色/区域/error与本地图册无差异，原文件摘要均匹配。原图不写入、不上传、不入Git。

21cohort前瞻划分14开发/7留出（55/27图片），同采集组/参考/精确重复并组。82标签全unverified，N/目标/19参考有效性未知；已展示全数据，不能称独立盲测。accuracy=null，不把候选覆盖当正确率。标签不足，不训练模型/不增加依赖；保留程序候选与集中复核。

## 包态与旧版清理

私有同版本CPython/四锁定wheel/完整WebEngine/OCR/模型许可与源码包，构建/ISCC0；361523190字节，setupSHA90915b9ffdd7c697d975390e8115240709fd6216203c9ff89e222209b3680709。桌面BioImage-WB-图像识别测试版-T061。内部兼容E7Test通道，显示名/版本T061。

旧E7由精确进程路径请求正常关闭，未强杀或丢弃；三个旧安装各自身卸载器exit0，旧注册项在新安装前均消失。新安装exit0，现注册显示图像识别测试版；PowerShell5.1既有双流程自检exit0，新私有python -I识别/清单v2往返/固定4槽未审核建议/原图不变probe0，模块SHA与冻结产品一致，未导入开发树。此前用户数据canary摘要一致。安装态Qt与全门禁串行。

旧桌面T048/T060安装包和t021过期开发快捷方式精确文件删除成功。批量递归缓存清理、明确旧runtime目录递归清理，以及混合旧构建/说明批量清理均被自动审批拒绝，仅返回blocked by policy；未改用其他工具绕过。旧构建目录、部分旧bytecode缓存和桌面历史说明仍保留，不能宣称本地迭代痕迹完全清除。详见local-version-cleanup.json。

未正式发布，未设定时任务。独立科学真值/样本对应、干净Win10和物理DPI仍未验。

## 原始日志SHA256（ignored本地）

- `.local/t061-fullcheck-710.txt`：`a48b9163f742520387766d8d269e264102ba661493fc40fc7f93b48ea057ab1d`。
- `.local/t061-installed-selfcheck.txt`：`62ab458d46102948823e435783b4b53b941f90c12a73fed68933a9595f93be2b`。
- `.local/t061-private-discovery.json`：`ec772ab1fffcf2b2729fc91bb4861e85e4404048fc443e0216be5e82df6364d0`。
- `.local/t061-capture.log`：`dcaf7ccb4eda4ef9e504e1fc17f9aa54ffe744e76421173feeb7101b299c3284`。
- `.local/t061-related-core.txt`：`09e6365633ff9ef38dbc40c0c66a2ccc215b7fa99bce7e1d294a2ea072f2a41e`。
- `.local/t061-related-core-v2.txt`：`c69d869798897526e34ce9a6d70b99e0b6291f5492d834fe7af8b8ccdd0b9aa2`。
- `.local/t061-related-web.txt`：`cfd3591bea58a29c52ad38102957ca8cb8eca35e05de01d173f86d09839fdaee`。
- `.local/t061-related-desktop.txt`：`af72f9af53f341c18558318bcd9ad366deb7ec4e4430a8c24519faf83f1e8260`。
- `.local/t061-web-ack.txt`：`4a9e144ddd5a6287093113753d3487ec363f810bad223182295e88ed1b2e60e2`。
- `.local/t061-build-710.txt`：`ae65c06ef39c9c88fd5ce97bf36114988b424c543960b64dd22c16ce39a494ad`。
