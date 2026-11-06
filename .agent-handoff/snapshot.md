# 当前恢复入口

P017明确孔板终点研究已完成，唯一状态见work/tasks/P-017-endpoint-assay-research.md。活动树bioimage-plan-sync，分支codex/p017-endpoint-assay-research；研究/规划交付完成。已保留P016 ac10a07收尾并合入已验main6bd4680（00becc8），上游B020前端规划e4209e9随本次正常PR集成。旧dirty树、P012窗口、用户安装及原图不动。

研究主选BCA单板562nm/BSA浓度整理。真实42孔/6样本参考与SciPy+statsmodels直接调用一致；18技术孔均低于原软件计算LoQ，体积3/10uL与空白身份未获SOP验证，不能把未外推当科学通过。详docs/research/2026-11-06-endpoint-assay.md和work/evidence/P-017/README.md。指定独审bcf57ce及最终b2eaccd增量通过；PR68合入main f8f69b5且树一致，双平台完整必需CI成功。最终交付见work/evidence/P-017/final-delivery.md。最终收据仅本地提交，随下一正常任务带入，不再触发CI；收尾后共享树释放，回传上游协调B021/PR69和下一新窗口。本窗口不启动下一任务。

主方案docs/plans/research-platform-rd.md第11节已明确MVP先行、当前小批次后集中统一前端/既有P009图形编排；资料不足不无限推迟统一。分别报告工程MVP、统一交互验收、源码可运行候选、用户安装更新、科学/真人试用；规划不代表实施，用户仍使用旧安装。最新用户规则替代旧偏好：每个新派发开发任务由上游另开窗口，同一任务修复/复审回原窗口；P017结束后不自行启动下一任务。第三方算法本体/权重/冻结参考不改；自有胶水可修，方法参数改变须明示版本并重验。简洁和体量优先，真实外部边界校验一次，不加重复包装/臆测fallback。

P016核分割已完成PR67/main6bd4680、独审/双平台CI，证据见P016/final-delivery。既有科学/训练重叠/患者独立性/学生/16bit/Linux真实模型/旧GPU与目标机限制保留；R全流程、BCA独立化学真值及学生需求本轮未验。普通已授权步骤继续，不要求用户反复批准。
