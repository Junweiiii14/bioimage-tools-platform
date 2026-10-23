# T-081 明显条带裁剪与整批裁剪阶段门槛

- 状态：本机实现、安装及桌面交付验收完成；下述最终闭合条件全部满足时 complete，否则 in-progress。2026-10-23 用户已授权自主推进至独审、必需检查、正常合入和交付，不反复确认、不过度测试。
- 基线：main d08b16bc0f632ee08f4d621f255469c416046593；已安装/上一包产品79b9db9；活动树wb-lab-installer，分支codex/t081-prominent-crop。T080闭合真实收据.local/T080/package/final-closeout.json，旧snapshot待更新内容不能当当前阻断。
- 最新约定覆盖早先方案：填写N是裁剪必须满足的数量；不采用按实际明显数改N的提议。明显程度最高的一行直接选，两行接近也选最高，不固定上下；保留完整N空间与A到C中间原始像素/弱空间距，不剪接。弱/缺失不转有效零，不从图像猜蛋白或样本对应。
- 目标：首先核对用户真实180目录漏裁路径，前两个Fig、GAPDH_161202_0_7_0_0 (1).tiff及大倾角；提高明显主行自动定位，阴影杂质降分；有效裁剪必须保存真实原值资产。某行失败继续其他行crop，但所有本批必需crop真实完成前禁止compose/measure/export；修正后继续，保留成功原值及历史。
- 顺序：P1实际入口/配置/单图与组图基线诊断→P2固定N主行优化及阶段barrier、版本化契约→P3有限数值/真实页面/180流程验证与原图SHA→P4绑定提交独审/必需CI/正常PR合入→P5新离线包构建、实际安装/自检/UI导出恢复/交付。
- 验收：在真实入口既定N下明确条带无需先手框；显著主行按评分直接采用；准确N个槽位/原坐标/完整中间区域；无效crop的批次其余裁剪继续而后续阶段不启动；修正后不重复成功裁剪，旧算法/结果不静默重算。原图/历史不可覆盖，软件原像素定量与显示变换分离。独立80%项目科学准确率尚无留出真值，不作已证声明。
- 非目标：重建视频聊天/调度、其他工具、付费依赖、原图上传、删除原图或旧源码。不覆盖旧交付。
- 证据：work/evidence/T-081及ignored .local/T081；记录环境/命令/exit/commit，失败如实保留，未运行不写通过。

- 已确认真实根因：原用户工程Fig1N2/Fig2N4填反，用户回复确认应4/2，后续新工程按此验证；原工程只读。workflow@4在4crop需复核时继续Fig3/4，是阶段问题实证。详细初诊、失败与进展见evidence及ignored .local/T081/progress.json。
- P1–P3完成：prominent@1、crop@5、grid@2、workflow@5及公开发布API全批门槛实现；94定向与静态检查、实际同源180正常DOM入口9crop/4Fig/完整输出通过，无手工裁剪确认，39原图不变、9原值裁图逐像素一致。初始失败保留。下一步精确commit独审/四CI/PR合入和新包实际安装，未标最终完成。
- P4首CI：1eb780c独审Accepted；Windows2fail/1289pass是验收仍要求旧policy3/guided2，三个精确版本期望已迁移到新契约，原值/N/页面/worker断言保持。限定两失败路径分别通过，详见ci-policy-migration。新准确提交独审/CI/合入和安装仍待完成。
- P4完成：81d8d87精确独审Accepted，四CI success，双平台1291与全部wheel；PR42正常merge main b59123e，树相同。初Linux20min窗口关闭取消UNKNOWN及Windows失败均保留。
- P5 R1实际安装、自检与33项通过后，真实截图额外发现恢复图片类型遗漏，产物独审Blocked，未交付安装包。现于codex/t081-restore-auxiliary-tiff/base b591补齐typed source/crop/Fig恢复类型，四个真实反例先红、30定向绿；R2准确独审/CI/重建和实际安装继续，不能标完成。详见restore-image-roles。

- R2首c3df CI：Linux1295及wheel/规则/桌面成功；Windows1294pass/1fail是第二次关闭前未等待真实后台空闲。受控真实读表原测试红、补齐空闲与新未保存编辑前置后3pass；所有精确状态和3000/20000ms时限不变，产品/门禁未改。具体CI后台操作UNKNOWN，见ci-session-precondition。等待新精确提交独审/四CI，未据初失败构建。


## 最终冻结与闭合条件

- 最终产品/安装源码 f1e6142ab41e16c66cfeb3d33958ab3a364581b1 已绑定非作者 Accepted，四必需CI SUCCESS（Linux1295/509.77s、Windows1295/756.69s，全部隔离wheel）。算法主改 PR42 已合main b59123e，恢复修复及本记录在 [PR43](https://github.com/Junweiiii14/bioimage-tools-platform/pull/43) 集成。
- R2真实构建/稳定路径升级 exit0；7793安装文件/209产品源码逐SHA相同、双模式自检、37安装态定向53.91s、163实际模块源摘要通过；真实180重开27原图/9原值裁图/4PNG/27缩略图通过。产物非作者Accepted、201文件ZIP校验及桌面真实PS5.1解压完成，详见 [final-delivery](../evidence/T-081/final-delivery.md)。
- 交付：桌面 WB-T081.zip、WB-T081 文件夹；私有180完整项目 WB-180-T081（127文件）。原始39输入/旧工程/旧包/dirty源码和视频树保持。包中只有合成练习，无私有原图。未新建功能、视频聊天或调度。
- 首次桌面发布命令 exit1：原生解压与tree核验已成功，随后校验器在维护终端继承PS7模块路径而找不到Get-FileHash。原日志保持；独审Accepted的恢复helper只隔离校验子进程到WinPS5.1内置Modules，重核现有树/ZIP后实际checker exit0，不重写字节/重解压/删除。不能把首次publisher写成通过。
- 完成必须同时成立：冻结产品的源码与产物独审Accepted、四CI成功、安装/双自检/37项及全部图片恢复通过、桌面ZIP和目录与产物SHA完全相同；本收尾记录的准确HEAD另经非作者独审和四必需CI SUCCESS后 PR43 正常merge（不绕过规则）；冻结产品到最终收尾HEAD的 apps/packages/tools/tooling/锁/测试/CI无变更，合并main树相同，工作树干净。
- 最终可机读收据 `.local/T081/package/r2/final-closeout.json` 只在上述条件全部核实后创建，绑定冻结产品HEAD、最终文档HEAD、四CI链接及main合入SHA；不存在或任一条件失败时不得标goal complete。文档不能预先声称自身未来HEAD CI已过。包内维护收据绑定真实构建f1，不改称最终文档HEAD。
- 80%独立项目100%自动裁剪、干净Win10/全部员工设备/物理DPI、原生退出/GPU历史UNKNOWN继续未验或未知；本机通过不外推。完整归档恢复的active export按既有契约interrupted，选新输出位置继续，已完成裁剪/测量保持。
